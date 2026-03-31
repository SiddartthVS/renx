from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict
from dom import Node
import dom

'''
FILE 3
Parsing CSS source code to produce Python objects
Tools:
    1)current()   - to return current character or empty str upon eof
    2)eof()       - to check whether end of file is reached
    3)peek(s)     - to only check if the current character starts with s
    4)expect(s)   - to consume string s else error
    5)take()      - to consume and return current character
    6)consume(t)  - to consume and return a sequence of chars that satisfy the test t
    7)space()     - to skip whitespaces
    8)name()      - to consume and return valid selector names
    9)validate(c) - to check valid selector names

Parsers:
    10)selector() - parse and return single simple selector
    11)selectors()- parse and return List of all simple selectors
    12)declarations() - parse and return all declaration blocks as Dict
    13)rule()     - parse and return a single Rule object
    14)rules()    - return cached parsed rule list (called once during init)

Main:
    15)getCSS()            - returns parsed list of Rule objects
    16)getCSS_tag_names()  - returns list of tag_names used in selectors
    17)getCSS_classes()    - returns list of classes used in selectors
    18)getCSS_ids()        - returns list of IDs used in selectors
    19)getCSS_declarations(node) - returns final applicable style dict for node

Helpers:
    20)selector_matches_node() - to check if a selector matches a DOM node

Debugging:
    21)print_css(rule)     - print Rule contents
'''

#1
@dataclass
class SimpleSelector:
    tag_name: Optional[str] = None
    id: Optional[str] = None
    classes: List[str] = None

    def __post_init__(self):
        if self.classes is None:
            self.classes = []

    def specificity(self) -> Tuple[int, int, int, int]:
        id_count = 1 if self.id is not None else 0
        class_count = len(self.classes)
        tag_count = 1 if self.tag_name is not None else 0
        return (0, id_count, class_count, tag_count)

#2
@dataclass
class Rule:
    selectors: List[SimpleSelector]
    declarations: Dict[str, str]

#3
class CSSparser:
    def __init__(self, data: str):
        self.input = data
        self.pos = 0
        self._rules_cache: List[Rule] = self._parse_rules()

    def _parse_rules(self) -> List[Rule]:
        rules: List[Rule] = []
        self.pos = 0
        while not self.eof():
            self.space()
            if self.eof(): break
            rules.append(self.rule())
            self.space()
        return rules

#Tools

    def current(self) -> str:
        if not self.eof():
            return self.input[self.pos]
        return ''

    def eof(self) -> bool:
        return self.pos >= len(self.input)

    def peek(self, s: str) -> bool:
        return self.input[self.pos:].startswith(s)

    def expect(self, s: str) -> None:
        if self.peek(s):
            self.pos += len(s)
        else:
            raise Exception(f'Expected "{s}" at position {self.pos}')

    def take(self) -> str:
        if not self.eof():
            c = self.input[self.pos]
            self.pos += 1
            return c
        raise Exception("Unexpected end of input")

    def consume(self, test) -> str:
        result = ""
        while not self.eof() and test(self.current()):
            result += self.take()
        return result

    def space(self) -> None:
        self.consume(str.isspace)

    def name(self) -> str:
        self.space()
        s = self.consume(lambda c: c.isalnum() or c in ['-', '_'])
        if not self.validate(s):
            raise Exception(f"Invalid selector name: '{s}'")
        return s

    def validate(self, s: str) -> bool:
        if not s or s[0].isdigit():
            return False
        return all(ch.isalnum() or ch in ['-', '_'] for ch in s[1:])

#Parsers

    def selector(self) -> SimpleSelector:
        tag = None
        id_ = None
        classes: List[str] = []
        while not self.eof() and self.current() not in ['{', ',', ' ', '\t', '\n']:
            if self.peek('#'):
                self.take()
                id_ = self.name()
            elif self.peek('.'):
                self.take()
                classes.append(self.name())
            elif self.peek('*'):
                self.take()
                tag = None
            else:
                tag = self.name()
        return SimpleSelector(tag_name=tag, id=id_, classes=classes)

    def selectors(self) -> List[SimpleSelector]:
        result: List[SimpleSelector] = []
        while True:
            result.append(self.selector())
            self.space()
            if self.peek(','):
                self.take()
                self.space()
            else:
                break
        return result

    def declarations(self) -> Dict[str, str]:
        decls: Dict[str, str] = {}
        while True:
            self.space()
            if self.peek('}'):
                break
            name = self.consume(lambda c: c not in ': ')
            self.space()
            self.expect(':')
            self.space()
            value = self.consume(lambda c: c != ';').strip()
            if self.peek(';'):
                self.expect(';')
            decls[name] = value
        return decls

    def rule(self) -> Rule:
        self.space()
        selectors = self.selectors()
        self.expect('{')
        declarations = self.declarations()
        self.space()
        self.expect('}')
        
        return Rule(selectors, declarations)

#Main

    def rules(self) -> List[Rule]:
        return self._rules_cache

    def getCSS(self) -> List[Rule]:
        return self._rules_cache

    def getCSS_tag_names(self) -> List[Optional[str]]:
        return [sel.tag_name for rule in self._rules_cache for sel in rule.selectors]

    def getCSS_classes(self) -> List[str]:
        return [cls for rule in self._rules_cache for sel in rule.selectors for cls in sel.classes]

    def getCSS_ids(self) -> List[Optional[str]]:
        return [sel.id for rule in self._rules_cache for sel in rule.selectors]

    def getCSS_declarations(self, node: Node) -> Dict[str, str]:
        result: Dict[str, str] = {}
        if not isinstance(node.type, dom.Element):
            return result

        tag_name = node.type.tag_name
        attrs = node.type.attrs
        node_id = attrs.get("id", "")
        node_classes = attrs.get("class", "").split()

        matched: List[Tuple[Tuple[int, int, int, int], Dict[str, str]]] = []
        for i, rule in enumerate(self._rules_cache):
            for selector in rule.selectors:
                if self.selector_matches_node(selector, tag_name, node_id, node_classes):
                    matched.append((selector.specificity()+(i,), rule.declarations))

        matched.sort(key=lambda x: x[0])
        for _, decls in matched:
            result.update(decls)

        return result
            

#Helpers

    def selector_matches_node(self, selector: SimpleSelector, tag_name: str, node_id: str, node_classes: List[str]) -> bool:
        if selector.tag_name and selector.tag_name != tag_name:
            return False
        if selector.id and selector.id != node_id:
            return False
        for cls in selector.classes:
            if cls not in node_classes:
                return False
        return True

#Debugging

    def print_css(self, rule: Rule):
        print("\n----------------------------------------")
        print("Selectors:")
        for sel in rule.selectors:
            print(f"\tTag: {sel.tag_name}\n\tID: {sel.id}\n\tClasses: {sel.classes}\n")
        print("Declarations:")
        for k, v in rule.declarations.items():
            print(f"\t{k} : {v}")
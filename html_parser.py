import dom
from typing import  List, Tuple, Dict, Iterator
from dataclasses import dataclass
'''
FILE 2
Parsing HTML source code to produce DOM nodes
Tools:
    1)current() - to return current character or empty str upon eof
    2)eof()     - to check wheather end of file is reached
    3)peek(s)   - to only check if the current character starts with s
    4)expect(s) - to consume string s else error
    5)take()    - to consume and return current character
    6)consume(t)- to consume and return a sequence of chars that satisfy the test t
    7)space()   - to skip whitespaces
    8)tag()     - to consume and return alphanumeric tags
    
Parsers:
    9)text(d)   - parse and return a text node until '<' is found
    10)element()- parse and return an HTML element node
    11)attr()   - parse and return single attribut (name,value) pair
    12)attrs()  - parse and return Dict of all attributes
    13)children()-yield all child nodes for a parent tag
    
Fixes:
    14)skip()   - to skip tags like<!DOCTYPE>
    
Main:
    15)getDOMs() for parsing the full HTML body and returning a List[Node]
    16)getDOM()  for parsing a single tag and returning a single Node

Debugging:
    17)print_dom(node) - takes a node and prints all of its contentss

'''
SINGLE_TAGS = ['br','hr','img','input','link']

class HTMLparser:
    def __init__(self,data: str):
        self.input=data
        self.pos=0

#Tools

    def current(self) -> str:
        if not self.eof():
            return self.input[self.pos]
        return ''
    
    def eof(self) -> bool:
        return self.pos >= len(self.input)

    def peek(self,s: str) -> bool:
            return self.input[self.pos:].startswith(s)

    def expect(self,s: str) -> None:
        if self.peek(s):
            self.pos += len(s)
        else:
            content = self.input[max(0, self.pos-20):self.pos+20]
            raise Exception(f'Expected "{s}" at position {self.pos}. Context: ...{content}...')

    def take(self) -> str:
        if not self.eof():
            c = self.input[self.pos]
            self.pos += 1
            return c
        return ''

    def consume(self,test) -> str:
        result=""
        while not self.eof() and test(self.current()):
                result+=self.take()
        return result

    def space(self) -> None:
        self.consume(str.isspace)

    def tag(self) -> str:
        return self.consume(lambda c: c.isalnum())

#Parsers

    def text(self) -> dom.Node:
        content = self.consume(lambda c: c!= '<')
        return dom.text_node(content)

    def comment(self) -> dom.Node:
        self.expect("<!--")
        content = ""
        while not self.peek("-->") and not self.eof():
            content += self.take()
        self.expect("-->")
        return dom.comm_node(content) 
    
    def element(self) -> dom.Node:
        self.expect("<")
        name=self.tag()
        att=self.attrs()
        if self.peek("/>"):
            self.expect("/>")
            return dom.elem_node(name,att,[])
        self.expect(">")
        if name in SINGLE_TAGS:
            return dom.elem_node(name,att,[])
        child=list(self.children(name))
        self.expect("</")
        self.expect(name)
        self.expect(">")
        return dom.elem_node(name,att,child)
    
    def attr(self) -> Tuple[str,str]:
        name = self.tag()
        self.space()
        if self.peek("="):
            self.expect("=")
            if self.peek('"'):
                self.expect('"')
                value=self.consume(lambda c: c != '"')
                self.expect('"')
            else:
                value=self.consume(lambda c: c not in ' >\n')
        else:
            value=""
        return (name,value)

    def attrs(self) -> Dict[str,str]:
        allAttrs = {}
        self.space()
        while True:
            key,value = self.attr()
            allAttrs[key] = value
            self.space()
            if self.peek(">") or self.peek("/"):
                break
        return allAttrs

    def children(self,tag: str) -> Iterator[dom.Node]:
        self.space()
        while not self.peek("</"+tag):
            if self.peek("<!--"):
                yield self.comment()
                self.space()
            elif self.peek("<"):
                yield self.element()
                self.space()
            else:
                yield self.text()

#Fixes
                
    def skip(self) -> None:
        self.expect("<!")
        while not self.peek(">") and not self.eof():
            self.take()
        self.expect(">")

#Main

    def getDOM(self) -> dom.Node:
        self.space()
        if self.peek("<!"):
            self.skip()
            return self.getDOM()
        elif self.peek("<!--"):
            return self.comment()
        elif self.peek("<"):
            return self.element()
        else:
            return self.text()

    def getDOMs(self) -> List[dom.Node]:
        nodes = []
        self.space()
        while not self.eof():
            self.space()
            if self.peek("<!"):
                self.skip()
            elif self.peek("<!--"):
                nodes.append(self.comment())
            elif self.peek("<"):
                nodes.append(self.element())
            elif self.peek(" "):
                self.space()
            else:
                nodes.append(self.text())
            self.space()
        return nodes
    
    def find_title(self,nodes: List[dom.Node]) -> str:
        for node in nodes:
            if not node or not isinstance(node.type, dom.Element):
              continue
            #print("Tag : ",node.type.tag_name)
            if node.type.tag_name == "title":
                #print("Title found!!!")
                return node.children[0].type.content
            else:
                result = self.find_title(node.children)
                if result:
                    return result
        return "" 
  

#Debugging
    def print_dom(self,node, indent=0):
        prefix = " " * indent *2
        if isinstance(node.type, dom.Text):
            print(f"{prefix}Text: \"{node.type.content}\"")
        elif isinstance(node.type, dom.Element):
            if node.type.attrs != {'':''}:
                print(f"{prefix}Element: <{node.type.tag_name}>",end='')
                print(f"{node.type.attrs}")
            else:
                print(f"{prefix}Element: <{node.type.tag_name}>")
            #print(f"{prefix}Children Count: {len(node.children)}")
            for child in node.children:
                self.print_dom(child, indent + 2)
        elif isinstance(node.type, dom.Comment):
            print(f"{prefix}Comment: \"{node.type.content}\"")
    
"""
#Example test
text1 = '''
<!DOCTYPE = html>
<html>
<head>
<title>Test</title>
</head>
<body>
<div class="container">
<p>Hello, World!</p>
<!-- This is a comment -->
</div>
</body>
</html>
'''
text2 ='''
<div>Hello</div>
<p>Hi</p>
'''
text3 = '''
<html>
    <head><title>Test</title></head>
    <body>
        <div id="main" class="container">
            <p>Hello, World!</p>
            <!-- This is a comment -->
        </div>
    </body>
</html>
'''

parser = HTMLparser(text1)
dom_tree = parser.getDOMs()

for node in dom_tree:
    parser.print_dom(node)
"""

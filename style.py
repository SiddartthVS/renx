from dom import Node
import dom
from css_parser import CSSparser
from dataclasses import dataclass
from typing import Dict, List

'''
STEP 4
Applying CSS styles to the DOM tree to produce the Style Tree.

Main Goals:
    1) Assign CSS property values to each element node.
    2) Non-element nodes (text, comments) are wrapped in StyleNodes with empty style.
    3) CSS declarations are expanded from shorthand to 4-part box model strings.
    4) Missing CSS properties are filled with default values.
    5) Resulting Style Tree mirrors DOM structure.

Classes:
    - StyleNode: holds a DOM node, its CSS property dict, and styled children.
    - Style: builds the Style Tree by combining DOM and parsed CSS.

Main:
    - getStyleNodes(n,css,parent) - to return the final detailed Style tree

Helpers
    - set_defaults - to set some default values if not already exists
    - set_inherited - to set some inherited properties from parents

'''

@dataclass
class StyleNode:
    node: Node
    values: Dict[str, str]   
    children: List['StyleNode']

class Style:
    
    def getStyleNodes(self, node: Node, css: CSSparser, parent_values: Dict[str,str] = {}) -> StyleNode:
        
        '''if isinstance(node.type, dom.Element) and node.type.tag_name.lower() == "head":
            styled_children = [self.getStyleNodes(child, css, {}) for child in node.children]
            return StyleNode(node=Node(dom.Anon),values = {},children=styled_children)'''
        
        matched = css.getCSS_declarations(node)
        #print("Befor attributes",matched)
        matched = self.set_attributes(node,matched)
        #print("After attributes",matched)

        #print("Before defaults : ",matched)
        defaulted = self.set_defaults(matched)
        #print("After defaults : ",defaulted)
        defaulted = self.set_inherited(defaulted,parent_values)

        #print("Before headings : ",defaulted)
        defaulted = self.set_headings_images_lines(node,defaulted)
        #print("After headings : ",defaulted)

        for val in ["margin","padding","border"]:
            self.set_shorthand(defaulted,val)

        full_style = self.set_colors(defaulted)
        styled_children = [self.getStyleNodes(child, css, full_style)
                           for child in node.children
                           if child is not None]

        return StyleNode(node, full_style, styled_children)

    def set_defaults(self, values: Dict[str, str]) -> Dict[str, str]:
        '''
        Ensures all required CSS properties are present by filling in defaults.
        
        
        defaults = {
            "background": "transparent",
            "color": "black",
            "display": "inline",
            "width": "auto",
            "margin": "0px",
            "padding": "0px",
            "border": "0px",
            "height": "auto",
            "box-sizing": "content-box",
            "position": "static",
            "font-face": "Times New Roman",
            "font-family": "Times New Roman",
            "text-align" : "left",
            "font-size": "24px",
            "font-weight": "400",
            "img": "False",
            "line": "False",
        }

        for key, value in defaults.items():
            if not any(k.strip() == key for k in values):
                values[key]=value
        '''
        return values
    
    @staticmethod
    def set_inherited(values: Dict[str,str], parent: Dict[str,str]) -> Dict[str,str]:
        INHERITED_PROPS = ["color", "font-size", "font-face", "font-family", "text-align", "font-weight","link"
                           ,"text-decoration","a"]
        for prop in INHERITED_PROPS:
            if prop not in values and prop in parent:
                values[prop] = parent[prop]
        return values


    @staticmethod
    def set_shorthand(values: Dict[str, str], prop: str) -> Dict[str, str]:
        '''
        Expand shorthand into four sides, apply overrides in CSS order,
        then remove individual longhand props.
        '''
        all_keys = [f"{prop}-top", f"{prop}-right", f"{prop}-bottom", f"{prop}-left"]
        final = ["0", "0", "0", "0"]
        to_remove = []

        for key in values:
            if key == prop:
                tokens = values[prop].replace("px", "").split()
                if len(tokens) == 1:
                    final = [tokens[0]] * 4
                elif len(tokens) == 2:
                    final = [tokens[0], tokens[1], tokens[0], tokens[1]]
                elif len(tokens) == 3:
                    final = [tokens[0], tokens[1], tokens[2], tokens[1]]
                elif len(tokens) == 4:
                    final = tokens
                else:
                    raise Exception(f"Unexpected value count for '{prop}': {tokens}")
            elif key in all_keys:
                index = all_keys.index(key)
                final[index] = values[key].replace("px", "")
                to_remove.append(key)

        
        for key in to_remove:
            del values[key]

        values[prop] = " ".join(final)

        return values
    
    @staticmethod
    def set_colors(values: Dict[str,str]) -> Dict[str,str]:
        for prop in ["color", "background", "background-color"]:
            if prop in values:
                val = values[prop].strip().lower()
                if val.startswith("#") and len(val) == 4:
                    val = "#" + "".join([ch * 2 for ch in val[1:]])  # #abc → #aabbcc
                values[prop] = val
        return values
    
    def set_attributes(self,node: Node,values: Dict[str,str]) -> Dict[str,str]:
        if not node or not isinstance(node.type, dom.Element):
            return values
        for key,value in node.type.attrs.items():
            if key not in values.keys():
                values[key] = value
        
        return values
    
    def set_headings_images_lines(self, node: Node, values: Dict[str,str]) -> Dict[str,str]:
        INLINE_TAGS = {
    "a", "abbr", "acronym", "b", "bdo", "big", "cite", "code", "dfn", "em",
    "i", "img", "input", "kbd", "label", "mark", "q", "rp", "rt", "ruby",
    "s", "samp", "select", "small", "span", "strong", "sub", "sup", "time",
    "tt", "u", "var", "button", "textarea"
}
        BLOCK_TAGS = {
            "div", "p", "body", "html", "section", "header", "footer", "nav",
            "article", "aside", "main", "ul", "ol", "li", "table", "tr", "td",
            "form", "fieldset", "legend"
        }


        if not node or not isinstance(node.type, dom.Element):
            return values
        tag = node.type.tag_name
        if tag and tag.startswith("h") and tag[1:].isdigit():
            #print("Heading found!!")
            values.update(self.get_headings(values, tag))
        elif tag in BLOCK_TAGS:
            values["display"] = "block"
        elif tag and tag =="img":
            #print("Image found!!")
            values["img"]="True"
            values["display"]="inline"
        elif tag and tag == "hr":
            #print("Line found!!")
            values["line"]="True"
            values["border"]="0"
            values["padding"]="0"
            values["margin"]="1"
            values["display"]="block"
        elif tag and tag == "a":
            values["color"] = "blue"
            values["text-decoration"] = "underline"
            values["cursor"] = "pointer"
            values["link"] = "True"
            values["display"] = "inline"
        elif tag and tag == "head":
            values["display"] = "none"
        elif tag and tag == "title":
            values["display"]= "none"
        elif tag and tag == "link":
            values["display"] = "none"
        elif tag and tag == "br":
            values["display"] = "block"
            values["margin-bottom"] = "16"
            values["br"] = "True"
        elif tag and tag == "b":
            values["bold"] = "True"
            values["display"] = "inline"
        elif tag and tag == "em":
            values["bold"] = "True"
            values["display"] = "inline"
        elif tag and tag == "strong":
            values["bold"] = "True"
            values["display"] = "inline"
        elif tag in INLINE_TAGS:
            values["display"] = "inline"



        return values

    @staticmethod
    def get_headings(values: Dict[str,str], heading : str) -> Dict[str,str]:
        heading = heading.strip().lower()
        sizes = {
            "h1": ("32", "21"),
            "h2": ("24", "20"),
            "h3": ("18", "19"),
            "h4": ("16", "18"),
            "h5": ("13", "17"),
            "h6": ("10", "16"),
        }
        if heading in sizes:
            font_size, margin = sizes[heading]
            values["font-size"] = font_size
            values["margin-top"] = values["margin-bottom"] = margin
            values["font-weight"] = "700"
            values["display"] = "block"
        return values




# --- Example Usage & Testing ---
'''
text1 = """
<html>
    <head><title>Test</title></head>
    <body>
        <div id="main" class="container">
            <p>Hello, World!</p>
            <!-- This is a comment -->
        </div>
    </body>
</html>
"""

text2 = """
h1, h2, h3 {
    margin: auto;
    color: #cc0000;
}
div.note {
    margin-bottom: 20px;
    padding: 10px;
}
#answer {
    display: none;
}
"""

html = HTMLparser(text1)
css = CSSparser(text2)
dom_tree = html.getDOMs()

style = Style()
result = [style.getStyleNodes(node, css) for node in dom_tree]

print(result)
'''

from dataclasses import dataclass
from typing import List,Union
'''
FILE 1
DOM model creation using Tree Node data structure in python
    - Each node contains list of its children Nodes
    - Each node also contains its own type
'''

#5
AttrMap = dict[str,str]
#Dict to store "attribute name : corresponding value"

#2
@dataclass
class Text:
    content: str

#3
@dataclass
class Element:
    tag_name: str
    attrs: AttrMap#5

    
#4
@dataclass
class Comment:
    content: str

#5
@dataclass
class Anon:
    pass

    
#1
NodeType = Union[Text,Element,Comment,Anon]#2,3,4,5
#node is either a Text or an Element

class Node:
    def __init__(self, node_type: NodeType, children: List['Node'] = None): 
        self.children: List['Node'] = children if children is not None else []
        # stores a List of Nodes or None if it is the last node.
        # quotes 'Node' because not fully defined-forward reference.
        
        self.type: NodeType = node_type#1
        # stores a NodeType-either Text or Element or Comment

def text_node(data: str) -> Node:
    #this is to create a text node
    return Node(
        node_type = Text(content=data),
        children = []
        )

def elem_node(tag_name: str, attrs: AttrMap, children: List[Node]) -> Node:
    #this is to create an element node
    return Node(
        node_type = Element(tag_name=tag_name, attrs=attrs),
        children = children
        )
def comm_node(data: str) -> Node:
    #this is to create a comment node
    return Node(
        node_type = Comment(content=data),
        children = []
        )


    
        

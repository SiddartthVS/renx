from style import *
from dataclasses import dataclass, field
from typing import List, Optional, Union
import dom
import pygame

'''
FILE 4
Adding Dimensions and X,Y coordinates to style tree to produce Layout tree

Main Goals:
    1) Assign box type, style node ref, children and dimensions to each style node.
    2) Inline-box parents use Anonymous-box to group their Block-box children
Helpers:
    - is_block(b) - returns True if box b is block
    - is_inline(b) - returns True if box b is inline
    - is_anonymous(b) - returns True if box b is anonymous
    - append_child(parent,child) - used to append child boxes based on the rule
    - getSizes(b,str) - used to parse and get the values of the 4-valued string
    - set_width_x(b,parent) - used to set the x position and width of the box b
    - wrap(s,font,max-width) - used to the return a list of lines as per max-width

Mains:
    - set_layout_tree(b,parent,y) - to set all the measures of the layout tree
    - get_layout_tree(style_node) - to get the layout tree


'''

#1
@dataclass
class Rect:
    x: int
    y: int
    width: int
    height: int

#2
@dataclass
class Sizes:
    top: int
    right: int
    bottom: int
    left: int

@dataclass
class Dimensions:
    content: Rect #1
    padding: Sizes #2
    border: Sizes  #2
    margin: Sizes  #2

#3
@dataclass
class BlockNode:
    styled_node: 'StyleNode'

#4
@dataclass
class InlineNode:
    styled_node: 'StyleNode'

#5
class AnonymousBlock:
    pass

BoxType = Union[BlockNode, InlineNode, AnonymousBlock] #3 #4 #5

@dataclass
class LayoutBox:
    box_type: BoxType
    style_node: Optional['StyleNode'] = None
    children: List['LayoutBox'] = field(default_factory=list)
    dimensions: Dimensions = field(default_factory=lambda: Dimensions(
        content=Rect(0, 0, 0, 0),
        padding=Sizes(0, 0, 0, 0),
        border=Sizes(0, 0, 0, 0),
        margin=Sizes(0, 0, 0, 0)
    ))


class Layout:

#Helpers

    @staticmethod
    def is_block(box_type: BoxType) -> bool:
        return isinstance(box_type, BlockNode)

    @staticmethod
    def is_inline(box_type: BoxType) -> bool:
        return isinstance(box_type, InlineNode)

    @staticmethod
    def is_anonymous(box_type: BoxType) -> bool:
        return isinstance(box_type, AnonymousBlock)

    @staticmethod
    def append_child(parent: LayoutBox, child: LayoutBox) -> None:
        if Layout.is_inline(parent.box_type) and Layout.is_block(child.box_type):
            if not parent.children or not Layout.is_anonymous(parent.children[-1].box_type):
                default_values = Style().set_defaults({})
                dummy_style = StyleNode(node=Node(dom.Anon()), values=default_values, children=[])
                anon_box = LayoutBox(box_type=AnonymousBlock(), style_node=dummy_style)
                parent.children.append(anon_box)
            parent.children[-1].children.append(child)
        else:
            parent.children.append(child)


    @staticmethod
    def getSizes(box: LayoutBox, name: str) -> Sizes:
        try:
            values = [int(i) for i in box.style_node.values.get(name, "0 0 0 0").split()]
            if len(values) != 4:
                values = [0, 0, 0, 0]
        except Exception:
            values = [0, 0, 0, 0]
        return Sizes(*values)

    @staticmethod
    def set_width_x(box: LayoutBox, parent: Dimensions) -> None:
        try:
            width_str = box.style_node.values.get("width", "auto").strip()
        except:
            width_str = "auto"

        margin = Layout.getSizes(box, "margin")
        padding = Layout.getSizes(box, "padding")
        border = Layout.getSizes(box, "border")

        total_offset = margin.left + margin.right + border.left + border.right + padding.left + padding.right
        parent_width = parent.content.width

        if width_str == "auto" :
            content_width = max(0, parent_width - total_offset)
        
        else:
            try:
                if width_str.endswith("px"):
                    width_str = width_str[:-2]
                specified = int(width_str)
                content_width = max(0, specified)
            except ValueError:
                content_width = max(0, parent_width - total_offset)

        box.dimensions.content.width = content_width
        box.dimensions.content.x = parent.content.x + margin.left + border.left + padding.left

    @staticmethod
    def wrap(text: str, font: pygame.font.Font, max_width: int) -> List[str]:

        words = text.split(" ")
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)
        return lines

    #Mains

    @staticmethod
    def set_layout_tree(box: LayoutBox, parent: Dimensions = None, parent_y: int = 0) -> None:
        
        if parent is None:
            screen = pygame.display.get_surface()
            width, height = screen.get_size() if screen else (960, 600)
            parent = Dimensions(
                content=Rect(0, 60, width, height),
                padding=Sizes(0, 0, 0, 0),
                border=Sizes(0, 0, 0, 0),
                margin=Sizes(0, 0, 0, 0)
            )
            parent_y = 60

        Layout.set_width_x(box, parent)

        box.dimensions.content.y = parent_y 
        box.dimensions.content.height = int(box.style_node.values.get("height","0px").strip()[:-2])

        if box.style_node.values.get("img", "False") == "True":
            if box.dimensions.content.height == 0:
                try:
                    image = pygame.image.load(box.style_node.values.get("src", ""))
                    box.dimensions.content.height = image.get_height()
                except:
                    box.dimensions.content.height = 100

        total_height = 0
        prev_margin_bottom = 0
        prev_is_inline = False

        for child in box.children:
            
            margin = Layout.getSizes(child, "margin")
            padding = Layout.getSizes(child, "padding")
            border = Layout.getSizes(child, "border")


            collapsed_margin = max(prev_margin_bottom,margin.top)
            if prev_is_inline and Layout.is_inline(child):
                #print("inline found!!")
                child_y = parent_y + collapsed_margin + padding.top + border.top
                Layout.set_layout_tree(child, box.dimensions, child_y)
            else:
                #print("inline not found!!")
                child_y = parent_y + total_height + collapsed_margin + padding.top + border.top
                Layout.set_layout_tree(child, box.dimensions, child_y)


            if child.style_node and isinstance(getattr(child.style_node.node, "type", None), dom.Text):
                text = child.style_node.node.type.content.strip()
                if text:
                    font_px = child.style_node.values.get("font-size", "24px").replace("px", "")
                    font_size = int(font_px) if font_px.isdigit() else 24
                    font_family = child.style_node.values.get("font-family", "Times New Roman")

                    font = pygame.font.SysFont(font_family, font_size)
                    available_width = child.dimensions.content.width

                    lines = Layout.wrap(text, font, available_width)
                    line_height = font.get_linesize()

                    if len(lines) == 1:
                        child.dimensions.content.height = font.size(lines[0])[1]
                    else:
                        child.dimensions.content.height = line_height * len(lines)

            total_height += (
                collapsed_margin + border.top + padding.top +
                child.dimensions.content.height +
                padding.bottom + border.bottom
            )

            prev_margin_bottom = margin.bottom
            prev_is_inline = Layout.is_inline(child)

        box.dimensions.content.height = total_height if box.dimensions.content.height== 0 else box.dimensions.content.height
        if box.style_node.values.get("br") == "True":
            box.dimensions.content.height = 6

    @staticmethod
    def get_layout_tree(styled_node: 'StyleNode') -> Optional[LayoutBox]:
        display = styled_node.values.get("display", "inline").strip()

        if display == "block":
            box_type: BoxType = BlockNode(styled_node)
        elif display == "inline":
            box_type: BoxType = InlineNode(styled_node)
        elif display == "none":
            return None
        else:
            box_type = InlineNode(styled_node)

        root_box = LayoutBox(box_type=box_type, style_node=styled_node)

        for child in styled_node.children:
            child_box = Layout.get_layout_tree(child)
            if child_box is not None:
                Layout.append_child(root_box, child_box)

        return root_box

    @staticmethod
    def set_inline_block(box: LayoutBox) -> None:
            if Layout.is_inline(box.box_type):

                parent = box.dimensions
                x_cursor = parent.content.x
                y_cursor = parent.content.y
                line_height = 0
                max_width = parent.content.width

                for child in box.children:
                    Layout.set_width_x(child, parent)

                    margin = Layout.getSizes(child, "margin")
                    padding = Layout.getSizes(child, "padding")
                    border = Layout.getSizes(child, "border")

                    total_child_width = (
                        margin.left + border.left + padding.left +
                        child.dimensions.content.width +
                        padding.right + border.right + margin.right
                    )

                    if x_cursor + total_child_width > parent.content.x + max_width:
                        x_cursor = parent.content.x
                        y_cursor += line_height
                        line_height = 0

                    child.dimensions.content.x = (
                        x_cursor + margin.left + border.left + padding.left
                    )
                    child.dimensions.content.y = (
                        y_cursor + margin.top + border.top + padding.top
                    )

                    if child.style_node and isinstance(getattr(child.style_node.node, "type", None), dom.Text):
                        text = child.style_node.node.type.content.strip()
                        if text:
                            font_px = child.style_node.values.get("font-size", "24px").replace("px", "")
                            font_size = int(font_px) if font_px.isdigit() else 24
                            font_family = child.style_node.values.get("font-family", "Times New Roman")
                            font = pygame.font.SysFont(font_family, font_size)
                            lines = Layout.wrap(text, font, child.dimensions.content.width)
                            line_h = font.get_linesize()
                            child.dimensions.content.height = line_h * len(lines)

                    x_cursor += total_child_width
                    total_height = (
                        margin.top + border.top + padding.top +
                        child.dimensions.content.height +
                        padding.bottom + border.bottom + margin.bottom
                    )
                    line_height = max(line_height, total_height)

                box.dimensions.content.height = y_cursor + line_height - box.dimensions.content.y

            for child in box.children:
                Layout.set_inline_block(child)

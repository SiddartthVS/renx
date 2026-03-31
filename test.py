from html_parser import HTMLparser
from css_parser import CSSparser
from style import Style
from layout import Layout
import dom

html_input = '''
<div class="container" id="main">
    Hello<span>world</span>!
    <!--This is a comment-->
</div>
'''

css_input = '''
div.container {
    margin: 10px;
    padding: 5px;
}
span {
    display: inline;
}
'''

# Parse HTML & CSS
html_parser = HTMLparser(html_input)
css_parser = CSSparser(css_input)
dom_tree = html_parser.getDOMs()

# Generate Style Tree
style = Style()
styled_tree = [style.getStyleNodes(node, css_parser) for node in dom_tree]

# Generate Layout Tree
layout_trees = [Layout.get_layout_tree(s_node) for s_node in styled_tree]

# Print Tree Structure
def print_layout_tree(box, indent=0):
    prefix = "  " * indent
    box_type = type(box.box_type).__name__
    print(f"{prefix}{box_type} with {len(box.children)} children")
    for child in box.children:
        print_layout_tree(child, indent + 1)

for tree in layout_trees:
    print_layout_tree(tree)

from dataclasses import dataclass, field
from typing import List, Dict, Union
from layout import LayoutBox,Layout
import pygame
import dom
import re


'''
STEP 5
Converting the Layout tree into the Command list that can be used to render the elements in place..

Helper:
    - traverse() - prepares command for text and background rendering

Mains:
    - getDisplayList() - to get the List of command to be rendered
    - paint(screen) - to iterate through the List and Paint elements in the screen


'''

@dataclass
class Painter:
    root: LayoutBox
    scroll_y: int
    display: List[Dict[str, Union[str, int, bool, pygame.Rect]]] = field(default_factory=list)

# Helper
    def traverse(self, box: LayoutBox):
        
        box_rect = pygame.Rect(
                            box.dimensions.content.x,
                            box.dimensions.content.y - self.scroll_y,
                            box.dimensions.content.width,
                            box.dimensions.content.height
                            )

        '''background'''

        bgcolor = box.style_node.values.get("background", "transparent")
        img = box.style_node.values.get("img","False")
        line = box.style_node.values.get("line","False")
        link = box.style_node.values.get("link",'False')

        
        #set command
        if bgcolor != "transparent" and img != "True" and line != "True" and link !="True":
            self.display.append({
                "type": "background",
                "color": bgcolor,
                "rect": box_rect
            })
        if img == "True":
            self.display.append({
                "type": "image",
                "src": box.style_node.values.get("src",""),
                "rect": box_rect,
                "width": int(box.style_node.values.get("width","0px")[:-2] 
                            if box.style_node.values.get("width","0px").endswith("px") else
                            box.style_node.values.get("width","0")),
                "height": int(box.style_node.values.get("height","0px")[:-2]
                            if box.style_node.values.get("height","0px").endswith("px") else
                            box.style_node.values.get("height","0")),
                "alt" : box.style_node.values.get("alt","⚠︎Error while rendering image!!"),
                "font-family" : box.style_node.values.get("font-family", "Times New Roman"),
                "font-size" : int(box.style_node.values.get("font-size", "16px").strip()[:-2])
            })
        if line == "True":
              self.display.append({
                  "type": "line",
                  "color": box.style_node.values.get("color","black"),
                  "rect": box_rect,
                  "height":str(box_rect.height) if box_rect.height != 0 else "2"
              })
        if link == "True":
            self.display.append({
                "type": "link",
                "color": bgcolor,
                "rect": box_rect,
                "href":  box.style_node.values.get("href","")
            })


        '''text'''

        if isinstance(box.style_node.node.type, dom.Text):
            text = box.style_node.node.type.content.strip()
            if text:
                # get size
                font_size_str = box.style_node.values.get("font-size", "16px").strip()
                if font_size_str.endswith("px"):
                    font_size_str = font_size_str[:-2]
                font_size = int(font_size_str) if font_size_str.isdigit() else 16

                # get font family
                font_family = box.style_node.values.get("font-family", "Times New Roman")

                # get alignment
                text_align = box.style_node.values.get("text-align", "left").strip()

                #get font weight
                weight = True if "font-weight" in box.style_node.values.keys() else False

                #get font decoration
                underline = True if box.style_node.values.get("text-decoration","")=="underline" else False


                #set command
                self.display.append({
                    "type": "text",
                    "text": text,
                    "rect": box_rect,
                    "color": box.style_node.values.get("color", "black"),
                    "font-size": font_size,
                    "font-family": font_family,
                    "text-align": text_align,
                    "bold": weight,
                    "underline": underline
                })

        '''children'''

        for child in box.children:
            self.traverse(child)

    def normalize_color(self,value: str) -> str:
        """
        Normalize CSS color values to formats accepted by pygame.Color.
        Supports:
            - Named colors (e.g., "red")
            - 3-digit hex (e.g., "#abc")
            - 6-digit hex (e.g., "#aabbcc")
            - rgb() and rgba() functions
        """
        if not value:
            return "black"

        value = value.strip().lower()

        # Expand 3-digit hex to 6-digit
        if re.fullmatch(r"#([0-9a-f]{3})", value):
            value = "#" + "".join([ch * 2 for ch in value[1:]])

        # Validate 6-digit hex
        if re.fullmatch(r"#([0-9a-f]{6})", value):
            return value

        # Handle rgb() and rgba()
        rgb_match = re.fullmatch(r"rgba?\(([^)]+)\)", value)
        if rgb_match:
            parts = [p.strip() for p in rgb_match.group(1).split(",")]
            try:
                r, g, b = map(int, parts[:3])
                a = int(float(parts[3]) * 255) if len(parts) == 4 else 255
                return (r, g, b, a)
            except:
                return "black"

        # Fallback to named color
        try:
            pygame.Color(value)  # test if pygame accepts it
            return value
        except:
            print(f"Warning: Invalid color '{value}', defaulting to black.")
            return "black"

# Mains
    def getDisplayList(self) -> List[Dict[str, Union[str, int, pygame.Rect]]]:
        self.display.clear()
        self.traverse(self.root)

        return self.display
    
    def getLinks(self) :
        self.getDisplayList()
        result = []
        for cmd in self.display:
            if cmd["type"] == "link":
                result.append(cmd["rect"],cmd["href"])
        return result

    def paint(self, screen):

        self.getDisplayList()

        for cmd in self.display:

            if cmd["type"] == "background":
                pygame.draw.rect(screen,pygame.Color(self.normalize_color(cmd["color"])), cmd["rect"])
            
            
            elif cmd["type"] == "text":

                font = pygame.font.SysFont(cmd["font-family"], cmd["font-size"])
                
                font.set_bold(cmd.get("bold"))
                font.set_underline(cmd.get("underline"))

                wrapped_lines = Layout.wrap(cmd["text"], font, cmd["rect"].width)
                line_height = font.get_linesize()
                
                for i, line in enumerate(wrapped_lines):
                    y = cmd["rect"].y + i * line_height
                    align = cmd["text-align"]

                    if align == "justify" and i < len(wrapped_lines) - 1 and " " in line:
                        words = line.split()
                        space_count = len(words) - 1
                        total_text_width = sum(font.size(word)[0] for word in words)
                        total_space_width = cmd["rect"].width - total_text_width
                        space_width = total_space_width // space_count if space_count > 0 else 0
                        x = cmd["rect"].x
                        for j, word in enumerate(words):
                            word_surface = font.render(word, True, pygame.Color(self.normalize_color(cmd["color"])))
                            screen.blit(word_surface, (x, y))
                            x += word_surface.get_width() + (space_width if j < space_count else 0)
                    
                    else:
                        line_surface = font.render(line, True, pygame.Color(self.normalize_color(cmd["color"])))
                        line_width = line_surface.get_width()
                        if align == "center":
                            x = cmd["rect"].x + (cmd["rect"].width - line_width) // 2
                        elif align == "right":
                            x = cmd["rect"].x + (cmd["rect"].width - line_width)
                        else:  # left
                            x = cmd["rect"].x
                        screen.blit(line_surface, (x, y))


            elif cmd["type"] == "image":
                #print("Rendering image!!")
                #print(cmd["rect"].width," : " ,cmd["rect"].height)
                width = cmd["rect"].width if cmd["rect"].width <= 5 else cmd["width"]
                height = cmd["rect"].height  if cmd["rect"].height <= 5 else cmd["height"]
                x = cmd["rect"].x
                y = cmd["rect"].y
                try:
                    image = pygame.image.load(cmd["src"])
                    act_width = image.get_width()
                    act_height = image.get_height()
                    width = act_width if width<=5 else width
                    height = act_height if height<=5 else height
                    scaled_image = pygame.transform.scale(image,(width,height))
                    screen.blit(scaled_image,(x,y))
                except:
                    alt_text = cmd["alt"] 
                    font = pygame.font.SysFont(cmd["font-family"], cmd["font-size"])
                    line_surf = font.render(alt_text, True,(0,0,0))
                    screen.blit(line_surf,(x,y))

            elif cmd["type"] == "line":
                #print("Rendering line!!")
                start = (0,cmd["rect"].y)
                end = (screen.get_size()[0],cmd["rect"].y)
                pygame.draw.line(screen,self.normalize_color(cmd["color"]),start,end,
                                 int(cmd["height"]))
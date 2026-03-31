import pygame
import dom

from html_parser import HTMLparser
from css_parser import CSSparser
from style import Style
from layout import Layout
from display import Painter

# === UI Colors ===
CLOSE_BTN_COLOR    = (255,  80,  80)
PLUS_BTN_COLOR     = TAB_INACTIVE_COLOR = (230,145,120)
PLUS_HOVER_COLOR   = TAB_ACTIVE_COLOR   = (230,212,161)
DISABLED_COLOR = (200,115,90)

# === Tab Layout ===
TAB_WIDTH    = 150
TAB_HEIGHT   = 40
TAB_START_X  = 60
MAX_TABS     = 6

# === Pygame‐User Events ===
NEW_TAB_EVENT       = pygame.USEREVENT + 1
TAB_CLICKED_EVENT   = pygame.USEREVENT + 2
TAB_CLOSED_EVENT    = pygame.USEREVENT + 3
REFRESH_TAB_EVENT   = pygame.USEREVENT + 4
PRE_PAGE_EVENT      = pygame.USEREVENT + 5
NEXT_PAGE_EVENT     = pygame.USEREVENT + 6


DEFAULT_CONTENT1 = '''Hello!! This is RenX - a mini browser engine developed by V.S.Siddartth.'''
DEFAULT_CONTENT2 = '''Here are the list of things that you can do using RenX...'''
DEFAULT_CONTENT3 = '''- Open a HTML file to render using (Ctrl+O) keys'''
DEFAULT_CONTENT4 = '''- Open a New Tab using (Ctrl+N) keys '''


class PlusButton:

    def __init__(self):
        self.rect = pygame.Rect(10, 10, 40, 40)

    def draw(self, surface, font, hovered=False,scroll_y=0):
        self.rect.y = -scroll_y+10
        color = PLUS_HOVER_COLOR if hovered else PLUS_BTN_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        plus = font.render("+", True, (0, 0, 0))
        surface.blit(plus, plus.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if (event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos))\
        or (event.type == event.type == pygame.KEYDOWN and event.key == pygame.K_n and \
             (pygame.key.get_mods() & pygame.KMOD_CTRL)):
            if len(tabs) < MAX_TABS:
                pygame.event.post(pygame.event.Event(NEW_TAB_EVENT))
            else:
                print("Max tab limit reached.")

class RefreshButton:

    def __init__(self):
        self.rect = pygame.Rect(1050, 10, 40, 40)

    def draw(self, surface, font, hovered=False,scroll_y=0,width=1100):
        self.rect.x = width - 50
        self.rect.y = -scroll_y+10
        color = PLUS_HOVER_COLOR if hovered else PLUS_BTN_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        refresh = font.render("~", True, (0, 0, 0))
        surface.blit(refresh, refresh.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if (event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos))\
        or (event.type == event.type == pygame.KEYDOWN and event.key == pygame.K_r and \
        (pygame.key.get_mods() & pygame.KMOD_CTRL)):
            pygame.event.post(pygame.event.Event(REFRESH_TAB_EVENT))

class NavigationButton:

    def __init__(self):
        self.rect1 = pygame.Rect(960, 10, 35, 40)
        self.rect2 = pygame.Rect(995, 10, 35, 40)


    def draw(self, surface, font, hovered1=False, hovered2=False,scroll_y=0,width=1100,history=[],act_history=0):
        self.rect1.x = width - 130
        self.rect2.x = width - 95
        self.rect1.y = self.rect2.y = -scroll_y+10
        # Back button (<)
        if len(history) > 1 and act_history > 0:
            color1 = PLUS_HOVER_COLOR if hovered1 else PLUS_BTN_COLOR
        else:
            color1 = DISABLED_COLOR

        # Forward button (>)
        if len(history) > 1 and act_history < len(history) - 1:
            color2 = PLUS_HOVER_COLOR if hovered2 else PLUS_BTN_COLOR
        else:
            color2 = DISABLED_COLOR

        pygame.draw.rect(surface, color1, self.rect1, border_top_left_radius=12, border_bottom_left_radius=12)
        left = font.render("<", True, (0, 0, 0))
        surface.blit(left, left.get_rect(center=self.rect1.center))
        pygame.draw.rect(surface, color2, self.rect2,  border_top_right_radius=12, border_bottom_right_radius=12)
        right = font.render(">", True, (0, 0, 0))
        surface.blit(right, right.get_rect(center=self.rect2.center))


    def handle_event(self, event):
        if (event.type == pygame.MOUSEBUTTONDOWN and self.rect1.collidepoint(event.pos))\
        or (event.type == event.type == pygame.KEYDOWN and event.key == pygame.K_LEFTBRACKET and \
        (pygame.key.get_mods() & pygame.KMOD_CTRL)):
            pygame.event.post(pygame.event.Event(PRE_PAGE_EVENT))
        if (event.type == pygame.MOUSEBUTTONDOWN and self.rect2.collidepoint(event.pos))\
        or (event.type == event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHTBRACKET and \
        (pygame.key.get_mods() & pygame.KMOD_CTRL)):
            pygame.event.post(pygame.event.Event(NEXT_PAGE_EVENT))
class Tab:
    def __init__(self, index, title=None, content=DEFAULT_CONTENT1):
        self.index = index
        self.custom_title = title is not None
        self.title = title or f"Tab {index + 1}"
        self.content = content
        self.html = ""
        self.css = ""
        self.painter = None
        self.history = []
        self.act_history = -1

        self.rect = pygame.Rect(
            TAB_START_X + index * TAB_WIDTH, 10, TAB_WIDTH, TAB_HEIGHT
        )
        self.close_rect = pygame.Rect(
            self.rect.right - 20,
            self.rect.top + 10,
            15,
            15
        )

    def update_position(self, index,scroll_y):
        y = scroll_y-10
        self.index = index
        self.rect.x = TAB_START_X + index * TAB_WIDTH
        self.rect.y = -y
        self.close_rect.y = -y+10
        self.close_rect.x = self.rect.right - 20
        if not self.custom_title:
            self.title = f"Tab {index + 1}"

    def reload(self):
        if self.html and self.css:
            self.generate_display(self.html,self.history[act_history])

    def find_linked_css(self,nodes):
        css = ""
        for node in nodes:
            if isinstance(node.type, dom.Element):
                if node.type.tag_name == "link":
                    attrs = node.type.attrs
                    if attrs.get("rel") == "stylesheet" and "href" in attrs:
                        try:
                            with open(attrs["href"], "r", encoding="utf-8") as f:
                                css += f.read() + "\n"
                            print(f"Loaded linked CSS: {attrs['href']}")
                        except Exception as e:
                            print(f"Error loading CSS from {attrs['href']}: {e}")
                css += self.find_linked_css(node.children)  # recursive search
        return css

    def generate_display(self, html: str, path: str):
        """
        Parse HTML & CSS, build style tree, layout tree,
        then create a Painter and its display list.
        """
        self.html = html
        try:
            parser = HTMLparser(self.html)
            dom_tree    = parser.getDOMs()
            linked_css = self.find_linked_css(dom_tree)
            
            self.css = "\n"+linked_css

            css_rules   = CSSparser(self.css)
            style_tree  = [Style().getStyleNodes(node, css_rules) for node in dom_tree]
            layout_boxes = [Layout.get_layout_tree(st)
                            for st in style_tree
                            if st is not None]
            
            title = parser.find_title(dom_tree)
            
            #print("Title is :",title,"\n\n")
            if title != "":
                self.title = title

            for box in layout_boxes:
                Layout.set_layout_tree(box)

            '''for box in layout_boxes:
                Layout.set_inline_block(box)
            '''
            
            if layout_boxes:
                self.painter = Painter(layout_boxes[0],scroll_y= 0)
                '''display_list = self.painter.getDisplayList()
                print(f"Display List has {len(display_list)} items")
                for i, cmd in enumerate(display_list):
                    print(f"Display[{i}]:", cmd)'''
            else:
                print("No layout boxes generated.")
                self.painter = None

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error rendering: {type(e).__name__} – {e}")
            self.painter = None

    def paint(self, screen):
        if self.painter:
            self.painter.paint(screen)

    def draw(self, surface, font, scroll_y, active=False, show_close=True):
        color = TAB_ACTIVE_COLOR if active else TAB_INACTIVE_COLOR
        pygame.draw.rect(surface,(255,255,255), (self.rect.x-5, -scroll_y+6, 160, 61),border_radius=6)

        pygame.draw.rect(surface, color, self.rect, border_radius=6)

        title_text = self.title
        max_width = self.rect.width - 25
        text_width, _ = font.size(title_text)

        while text_width > max_width and len(title_text) > 3:
            title_text = title_text[:-1]
            text_width, _ = font.size(title_text + "...")

        if title_text != self.title:
            title_text += "..."

        title_surf = font.render(title_text, True, (0, 0, 0))
        surface.blit(title_surf, (self.rect.x + 10, self.rect.y + 10))


        if show_close:
            pygame.draw.rect(surface, CLOSE_BTN_COLOR, self.close_rect, border_radius=3)
            x_surf = font.render("x", True, (255,255,255))
            surface.blit(x_surf, x_surf.get_rect(center=self.close_rect.center))

    def handle_event(self, event, show_close):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if show_close and self.close_rect.collidepoint(event.pos):
                pygame.event.post(
                    pygame.event.Event(TAB_CLOSED_EVENT, tab_index=self.index)
                )
            elif self.rect.collidepoint(event.pos):
                pygame.event.post(
                    pygame.event.Event(TAB_CLICKED_EVENT, tab_index=self.index)
                )


# === Global State ===
tabs = [Tab(0, "Tab 1")]
active_tab = 0
act_history = -1
plus_button = PlusButton()
refresh_button = RefreshButton()
navigation_button = NavigationButton()
import pygame
import tkinter as tk
from tkinter import filedialog
import os

from html_parser import HTMLparser
from css_parser import CSSparser
from style import Style
from layout import Layout
from display import Painter

# DPI fix
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass
root = tk.Tk()
root.withdraw()

# Pygame init
pygame.init()
WIDTH, HEIGHT = 1000, 600
MIN_WIDTH, MIN_HEIGHT = 400, 300
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("My Minimal Browser")
try:
    icon_surface = pygame.image.load("icon.png")
    pygame.display.set_icon(icon_surface)
except Exception as e:
    print("\u26a0\ufe0f Could not load icon.png:", e)

clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18)

# === Colors ===
BG_COLOR = (255, 255, 255)
TAB_ACTIVE_COLOR = (100, 149, 237)
TAB_INACTIVE_COLOR = (180, 180, 180)
CLOSE_BTN_COLOR = (255, 80, 80)
CLOSE_TEXT_COLOR = (255, 255, 255)
TEXT_COLOR = (50, 50, 50)
PLUS_BTN_COLOR = (200, 200, 200)
PLUS_HOVER_COLOR = (160, 160, 160)

# === Tab Layout ===
TAB_WIDTH = 150
TAB_HEIGHT = 40
TAB_START_X = 60
MAX_TABS = 6

# === Events ===
NEW_TAB_EVENT = pygame.USEREVENT + 1
TAB_CLICKED_EVENT = pygame.USEREVENT + 2
TAB_CLOSED_EVENT = pygame.USEREVENT + 3

# === Plus Button ===
class PlusButton:
    def __init__(self):
        self.rect = pygame.Rect(10, 10, 40, 40)

    def draw(self, surface, hovered=False):
        color = PLUS_HOVER_COLOR if hovered else PLUS_BTN_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        plus = font.render("+", True, (0, 0, 0))
        surface.blit(plus, plus.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            if len(tabs) < MAX_TABS:
                pygame.event.post(pygame.event.Event(NEW_TAB_EVENT))
            else:
                print("\u274c Max tab limit reached.")

# === Tab Class ===
class Tab:
    def __init__(self, index, title=None, content="No Internet Connection"):
        self.index = index
        self.custom_title = title is not None
        self.title = title or f"Tab {index + 1}"
        self.content = content
        self.html = ""
        self.css = ""
        self.painter = None
        self.rect = pygame.Rect(TAB_START_X + index * TAB_WIDTH, 10, TAB_WIDTH, TAB_HEIGHT)
        self.close_rect = pygame.Rect(self.rect.right - 20, self.rect.top + 10, 15, 15)

    def update_position(self, index):
        self.index = index
        self.rect = pygame.Rect(TAB_START_X + index * TAB_WIDTH, 10, TAB_WIDTH, TAB_HEIGHT)
        self.close_rect = pygame.Rect(self.rect.right - 20, self.rect.top + 10, 15, 15)
        if not self.custom_title:
            self.title = f"Tab {index + 1}"

    def reload(self):
        if self.html and self.css:
            self.generate_display(self.html, self.css)

    def generate_display(self, html: str, css: str):
        try:
            self.html = html
            self.css = css
            dom_tree = HTMLparser(html).getDOMs()
            #print(f"✅ DOM Tree Length: {len(dom_tree)}")
            css_rules = CSSparser(css)
            style_tree = [Style().getStyleNodes(n, css_rules) for n in dom_tree]
            #print(f"🎨 Styled Tree Built")
            layout_boxes = [Layout.get_layout_tree(st) for st in style_tree if st]
            for box in layout_boxes:
                Layout.set_layout_tree(box)
                #print(f"📊 Layout tree set for box")
            if layout_boxes:
                self.painter = Painter(layout_boxes[0])
                display_list = self.painter.getDisplayList()
                print(f"🖍️ Display List has {len(display_list)} items")
                for i, cmd in enumerate(display_list):
                    print(f"🔍 Display[{i}]:", cmd)
            else:
                print("⚠️ No layout boxes generated.")
                self.painter = None
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ Error rendering: {type(e).__name__} - {e}")
            self.painter = None
    
    def paint(self, screen):
        if self.painter:
            self.painter.paint(screen)

    def draw(self, surface, active=False, show_close=True):
        color = TAB_ACTIVE_COLOR if active else TAB_INACTIVE_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        title_surf = font.render(self.title, True, (0, 0, 0))
        surface.blit(title_surf, (self.rect.x + 10, self.rect.y + 10))
        if show_close:
            pygame.draw.rect(surface, CLOSE_BTN_COLOR, self.close_rect, border_radius=3)
            x_surf = font.render("\u00d7", True, CLOSE_TEXT_COLOR)
            surface.blit(x_surf, x_surf.get_rect(center=self.close_rect.center))

    def handle_event(self, event, show_close):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if show_close and self.close_rect.collidepoint(event.pos):
                pygame.event.post(pygame.event.Event(TAB_CLOSED_EVENT, tab_index=self.index))
            elif self.rect.collidepoint(event.pos):
                pygame.event.post(pygame.event.Event(TAB_CLICKED_EVENT, tab_index=self.index))

# === State ===
tabs = [Tab(0, "Tab 1")]
active_tab = 0
plus_button = PlusButton()

# === Main Loop ===
running = True
while running:
    WIDTH, HEIGHT = pygame.display.get_surface().get_size()
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        plus_button.handle_event(event)
        for tab in tabs:
            tab.handle_event(event, show_close=(len(tabs) > 1))

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_o and pygame.key.get_mods() & pygame.KMOD_CTRL:
                filetypes = [("HTML files", "*.html *.htm"), ("All files", "*.*")]
                html_path = filedialog.askopenfilename(title="Open HTML File", filetypes=filetypes)
                css_path = filedialog.askopenfilename(title="Open CSS File", filetypes=filetypes)

                if html_path:
                    with open(html_path, "r", encoding="utf-8") as f:
                        html_content = f.read()
                        tabs[active_tab].title = os.path.basename(html_path)
                        tabs[active_tab].custom_title = True
                        tabs[active_tab].content = html_content

                        css_content = ""
                        if css_path:
                            with open(css_path, "r", encoding="utf-8") as f2:
                                css_content = f2.read()

                        tabs[active_tab].generate_display(html_content, css_content)
                        print(f"✅ Loaded HTML into Tab {active_tab + 1}")

        elif event.type == NEW_TAB_EVENT:
            new_index = len(tabs)
            tabs.append(Tab(new_index))
            active_tab = new_index

        elif event.type == TAB_CLICKED_EVENT:
            active_tab = event.tab_index

        elif event.type == TAB_CLOSED_EVENT:
            closed = event.tab_index
            del tabs[closed]
            if active_tab == closed:
                active_tab = max(0, closed - 1)
            elif active_tab > closed:
                active_tab -= 1
            for i, tab in enumerate(tabs):
                tab.update_position(i)

        elif event.type == pygame.VIDEORESIZE:
            new_width = max(event.w, MIN_WIDTH)
            new_height = max(event.h, MIN_HEIGHT)
            screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)

            tabs[active_tab].reload()

    # Update tab positions each frame
    for i, tab in enumerate(tabs):
        tab.update_position(i)

    # === Drawing ===
    screen.fill(BG_COLOR)

    for i, tab in enumerate(tabs):
        tab.draw(screen, active=(i == active_tab), show_close=(len(tabs) > 1))

    plus_button.draw(screen, hovered=plus_button.rect.collidepoint(mouse_pos))

    if tabs:
        if tabs[active_tab].painter:
            tabs[active_tab].paint(screen)
        else:
                text = font.render("❌ Rendering failed. Check terminal for error.", True, (200, 0, 0))
                screen.blit(text, (20, 100))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()

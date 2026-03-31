import os
import pygame
from tkinter import filedialog

from html_parser import HTMLparser
from css_parser import CSSparser
from style import Style
from layout import Layout
import metadata

from tabs import (
    tabs,
    active_tab,
    plus_button,
    refresh_button,
    navigation_button,
    NEW_TAB_EVENT,
    TAB_CLICKED_EVENT,
    TAB_CLOSED_EVENT,
    REFRESH_TAB_EVENT,
    PRE_PAGE_EVENT,
    NEXT_PAGE_EVENT,
    Tab,
)

# === DPI Fix on Windows ===
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# === Pygame Initialization ===
pygame.init()
WIDTH, HEIGHT = 1100, 600
MIN_WIDTH, MIN_HEIGHT = 600, 300
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("RenX")

# === Custom Browser Icon ===
try:
    icon_surface = pygame.image.load("icon.png")
    pygame.display.set_icon(icon_surface)
except Exception as e:
    print("Could not load icon.png:", e)

clock = pygame.time.Clock()
font = pygame.font.SysFont("Comic sans", 16)
scroll_y = 0
scroll_step = 40
FPS = 60

# === UI Colors ===
BG_COLOR            = (255, 255, 255)
TAB_BAR_COLOR       = (230,92,50)
TAB_BAR_Y_OFFSET    = 60  # space for tabs at top

# === Painter: builds display list & paints it ===
class Painter:
    def __init__(self, root_box):
        self.root = root_box
        self.display = []

    def traverse(self, box):
        r = box.dimensions.content
        box_rect = pygame.Rect(r.x, r.y, r.width, r.height)

        # 1) Background
        bgcolor = box.style_node.values.get("background", "white")
        self.display.append({
            "type": "background",
            "color": bgcolor,
            "rect": box_rect
        })

        # 2) Text
        from dom import Text
        if isinstance(box.style_node.node.type, Text):
            raw = box.style_node.node.type.content.strip()
            if raw:
                # Safe font-size parsing
                fs = box.style_node.values.get("font-size", "24px").strip()
                if fs.endswith("px"):
                    fs = fs[:-2]
                font_size = int(fs) if fs.isdigit() else 24

                family = box.style_node.values.get("font-family", "Times New Roman")
                align  = box.style_node.values.get("text-align", "left").strip()
                bold   = int(box.style_node.values.get("font-weight", "400").strip()) >= 700

                self.display.append({
                    "type":       "text",
                    "text":       raw,
                    "rect":       box_rect,
                    "color":      box.style_node.values.get("color", "black"),
                    "font-size":  font_size,
                    "font-family": family,
                    "text-align":  align,
                    "bold":        bold,
                })

        # 3) Recurse into children
        for child in box.children:
            self.traverse(child)

    def getDisplayList(self):
        self.display.clear()
        self.traverse(self.root)
        return self.display

    def paint(self, screen):
        for cmd in self.display:
            if cmd["type"] == "background":
                col = pygame.Color(cmd["color"])
                pygame.draw.rect(screen, col, cmd["rect"])

            elif cmd["type"] == "text":
                f = pygame.font.SysFont(cmd["font-family"], cmd["font-size"])
                f.set_bold(cmd["bold"])

                lines = Layout.wrap(cmd["text"], f, cmd["rect"].width)
                lh = f.get_linesize()

                for i, line in enumerate(lines):
                    surf = f.render(line, True, pygame.Color(cmd["color"]))
                    w = surf.get_width()

                    if cmd["text-align"] == "center":
                        x = cmd["rect"].x + (cmd["rect"].width - w)//2
                    elif cmd["text-align"] == "right":
                        x = cmd["rect"].x + (cmd["rect"].width - w)
                    else:
                        x = cmd["rect"].x

                    y = cmd["rect"].y + i*lh
                    screen.blit(surf, (x, y))


# === Main Loop & Event Handling ===
running = True
while running:
    # Keep track of window size & mouse
    WIDTH, HEIGHT = pygame.display.get_surface().get_size()
    mouse_pos = pygame.mouse.get_pos()
    

    for event in pygame.event.get():
        # Tab bar events
        plus_button.handle_event(event)
        refresh_button.handle_event(event)
        navigation_button.handle_event(event)
        for tab in tabs:
            tab.handle_event(event, show_close=(len(tabs) > 1))

        if event.type == pygame.QUIT:
            running = False

        # Ctrl+O: open HTML & CSS files
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_o and \
             (pygame.key.get_mods() & pygame.KMOD_CTRL):
            filetypes = [("HTML files","*.html *.htm"), ("All files","*.*")]
            html_path = filedialog.askopenfilename(title="Open HTML File",
                                                   filetypes=filetypes)
            scroll_y = 0
            if html_path:
                with open(html_path, "r", encoding="utf-8") as f:
                    html_content = f.read()

                # reload into active tab
                tabs[active_tab].title = os.path.basename(html_path)
                tabs[active_tab].custom_title = True
                tabs[active_tab].generate_display(html_content,html_path)

                tabs[active_tab].act_history += 1
                tabs[active_tab].history.insert(tabs[active_tab].act_history,html_path)
                print("\n\n")
                for h in tabs[active_tab].history:
                    print("History :",h[-10:])
                print("Active:",tabs[active_tab].act_history)

        # Link click event
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            current = tabs[active_tab]
            if current.painter:
                for cmd in current.painter.display:
                    if cmd["type"] == "link" and cmd["rect"].collidepoint(event.pos):
                        scroll_y = 0
                        html_path = cmd["href"]
                        print(f"Clicked link to: {html_path}")
                        try:
                            with open(html_path, "r", encoding="utf-8") as f:
                                html_content = f.read()

                            # reload into active tab
                            tabs[active_tab].title = os.path.basename(html_path)
                            tabs[active_tab].custom_title = True
                            tabs[active_tab].generate_display(html_content,html_path)

                            tabs[active_tab].act_history += 1
                            tabs[active_tab].history.insert(tabs[active_tab].act_history,html_path)
                            print("\n\n")
                            for h in tabs[active_tab].history:
                                print("History :",h[-10:])
                            print("Active:",tabs[active_tab].act_history)
                        except Exception as e:
                            print(f"Error opening link target {html_path}:", e)
                        break

        # Scroll events
        elif event.type == pygame.MOUSEWHEEL and tabs[active_tab].painter:
            scroll_y -= event.y * scroll_step
        elif event.type == pygame.KEYDOWN and tabs[active_tab].painter:
            if event.key == pygame.K_UP:
                scroll_y -= scroll_step
            elif event.key == pygame.K_DOWN:
                scroll_y += scroll_step

        # Tab events
        elif event.type == NEW_TAB_EVENT:
            scroll_y = 0
            new_idx = len(tabs)
            tabs.append(Tab(new_idx))
            active_tab = new_idx

        elif event.type == TAB_CLICKED_EVENT:
            active_tab = event.tab_index

        elif event.type == TAB_CLOSED_EVENT:
            idx = event.tab_index
            del tabs[idx]
            if active_tab >= len(tabs):
                active_tab = len(tabs) - 1
            for i, t in enumerate(tabs):
                t.update_position(i,scroll_y)

        elif event.type == REFRESH_TAB_EVENT:
            scroll_y = 0
            if tabs[active_tab].act_history >= 0 :
                if tabs[active_tab].history[tabs[active_tab].act_history]:
                    html_path = tabs[active_tab].history[tabs[active_tab].act_history]
                    with open(html_path, "r", encoding="utf-8") as f:
                        html_content = f.read()
                tabs[active_tab].title = os.path.basename(html_path)
                tabs[active_tab].custom_title = True
                tabs[active_tab].generate_display(html_content,html_path)

        elif event.type == PRE_PAGE_EVENT:
            scroll_y = 0
            if tabs[active_tab].act_history > 0:
                tabs[active_tab].act_history-=1
                pygame.event.post(pygame.event.Event(REFRESH_TAB_EVENT))

            print("\n\n")
            for h in tabs[active_tab].history:
                print("History :",h[-10:])
            print("Active:",tabs[active_tab].act_history)

        
        elif event.type == NEXT_PAGE_EVENT:
            scroll_y = 0
            if tabs[active_tab].act_history < len(tabs[active_tab].history)-1:
                tabs[active_tab].act_history+=1
                pygame.event.post(pygame.event.Event(REFRESH_TAB_EVENT))
            print("\n\n")
            for h in tabs[active_tab].history:
                print("History :",h[-10:])
            print("Active:",tabs[active_tab].act_history)

        # Window resize
        elif event.type == pygame.VIDEORESIZE:
            new_w = max(event.w, MIN_WIDTH)
            new_h = max(event.h, MIN_HEIGHT)
            screen = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)
            tabs[active_tab].reload()

    # === Drawing ===
    screen.fill(BG_COLOR)

    # Draw tab bar
    tab_bar = pygame.draw.rect(screen, TAB_BAR_COLOR, (0, 0 - scroll_y, WIDTH, 55))

    # Always update tab positions
    for i, t in enumerate(tabs):
        t.update_position(i,scroll_y)

    
    # Draw tabs + “+” button
    for i, t in enumerate(tabs):
        t.draw(screen, font, active=(i==active_tab), show_close=(len(tabs)>1),scroll_y=scroll_y)

    plus_button.draw(screen, font, hovered=plus_button.rect.collidepoint(mouse_pos),scroll_y=scroll_y)
    refresh_button.draw(screen, font, hovered=refresh_button.rect.collidepoint(mouse_pos),scroll_y=scroll_y,width=WIDTH)
    navigation_button.draw(screen, font, hovered1=navigation_button.rect1.collidepoint(mouse_pos),
                           hovered2=navigation_button.rect2.collidepoint(mouse_pos),scroll_y=scroll_y,
                           width=WIDTH,history=tabs[active_tab].history,act_history=tabs[active_tab].act_history)

    # Paint current page or error message
    current = tabs[active_tab]
    if current.painter:
        current.painter.scroll_y = scroll_y
        current.painter.paint(screen)
    elif not current.painter and len(current.history)>0:
        metadata.paint_error(screen,WIDTH)
    else:
        metadata.paint_home(screen,WIDTH)
    




    # Limit scrolling
    if tabs and tabs[active_tab].painter:
        content_height = tabs[active_tab].painter.root.dimensions.content.height
        max_scroll = max(0, content_height - HEIGHT + TAB_BAR_Y_OFFSET)
        scroll_y = max(0, min(scroll_y, max_scroll))
    else:
        scroll_y = 0

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
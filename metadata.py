import pygame
from layout import Layout

def paint_home(screen: pygame.Surface,width: int):
    y = 0
    # Para 1
    head =  pygame.font.SysFont("Comic sans", 32)
    font =  pygame.font.SysFont("Comic sans", 18)
    head.set_bold(True)
    font.set_bold(False)
    line1 = head.render("Hello!!", True, pygame.Color(230,92,50))
    screen.blit(line1,(30,70))
    content = '''This is a minimalistic browser rendering engine built from scratch that is capable of rendering basic HTML + CSS content from local '.html' files. Here are some of the things that you can try :'''

    wrapped_lines = Layout.wrap(content, font,width-200)
    line_height = font.get_linesize()
                
    for i, line in enumerate(wrapped_lines):
      if i < len(wrapped_lines)-1 and " " in line:
        y = 112 + i * line_height
        words = line.split()
        space_count = len(words) - 1
        total_text_width = sum(font.size(word)[0] for word in words)
        total_space_width = width-200 - total_text_width
        space_width = total_space_width // space_count if space_count > 0 else 0
        x = 80
        for j, word in enumerate(words):
            word_surface = font.render(word, True, pygame.Color(0,0,0))
            screen.blit(word_surface, (x, y))
            x += word_surface.get_width() + (space_width if j < space_count else 0)

      else:
        y += line_height
        line_surface = font.render(line, True, pygame.Color(0,0,0))
        screen.blit(line_surface,(80,y))
    # Point 1
    points =['''- Press CTRL + O to open new HTML file''',
             '''- Click the + button or press CTRL + N to open new tabs''',
             '''- Click the ~ button or press CTRL + R to refresh the tab''',
             '''- Use "<" and ">" buttons or "CTRL + [" and "CTRL + ]" for navigation''']
    y += line_height*1.5
    for p in range(len(points)):
       y += line_height
       point = pygame.font.SysFont("Comic sans", 16)
       point.set_bold(True)
       poi = point.render(points[p], True, pygame.Color(0,0,0))
       screen.blit(poi, (100,y))
    y += line_height*1.5
    content2 = '''To explore supported HTML tags and CSS features, check the console logs....'''
    wrapped_lines = Layout.wrap(content2, font,width-200)
    for i, line in enumerate(wrapped_lines):
       y += line_height
       end = font.render(line, True, pygame.Color(0,0,0))
       screen.blit(end,(80,y))

def paint_error(screen: pygame.Surface,width: int):
    pass
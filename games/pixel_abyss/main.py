"""
PIXEL ABYSS — placeholder main.py

REPLACE THIS FILE with your actual PIXEL_ABYSS-v38/main.py
(and copy the entire game's source + assets into this folder)

The shell will call main() from this file.
Make sure your main.py has:

    if __name__ == "__main__":
        main()

or just a top-level game loop — both work.
"""

import pygame
import sys

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 480))
    pygame.display.set_caption("PIXEL ABYSS")
    font = pygame.font.SysFont("consolas", 24, bold=True)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit(); return

        screen.fill((8, 10, 20))
        msg = font.render("Replace this with PIXEL ABYSS main.py", True, (0, 220, 180))
        screen.blit(msg, (screen.get_width()//2 - msg.get_width()//2,
                          screen.get_height()//2 - msg.get_height()//2))
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()

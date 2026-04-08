"""
games/demo_snake/main.py — Snake, mobile-ready for BLEMAC Shell.

Works with the virtual D-pad: arrow key events injected by VirtualPad
drive the snake exactly like keyboard on desktop.
"""

import pygame
import random
import sys

W, H   = 400, 400
CELL   = 20
COLS   = W // CELL
ROWS   = H // CELL
FPS    = 10

BG    = (10, 12, 22)
SNAKE = (0, 220, 160)
HEAD  = (0, 255, 200)
FOOD  = (220, 60, 100)
GRID  = (20, 28, 45)
TEXT  = (200, 210, 255)


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Snake")
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont("consolas", 18, bold=True)

    snake     = [(COLS//2, ROWS//2)]
    direction = (1, 0)
    food      = _new_food(snake)
    score     = 0
    alive     = True

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); return
                # Arrow keys / WASD — injected by virtual pad
                if event.key in (pygame.K_UP,    pygame.K_w) and direction != (0,-1):
                    direction = (0, 1)
                if event.key in (pygame.K_DOWN,  pygame.K_s) and direction != (0, 1):
                    direction = (0,-1)
                if event.key in (pygame.K_LEFT,  pygame.K_a) and direction != (1, 0):
                    direction = (-1, 0)
                if event.key in (pygame.K_RIGHT, pygame.K_d) and direction != (-1,0):
                    direction = (1, 0)
                if event.key == pygame.K_r and not alive:
                    main(); return

        if alive:
            head = (snake[0][0]+direction[0], snake[0][1]+direction[1])
            if not (0 <= head[0] < COLS and 0 <= head[1] < ROWS) or head in snake:
                alive = False
            else:
                snake.insert(0, head)
                if head == food:
                    score += 1
                    food = _new_food(snake)
                else:
                    snake.pop()

        screen.fill(BG)
        for gx in range(0, W, CELL):
            pygame.draw.line(screen, GRID, (gx, 0), (gx, H))
        for gy in range(0, H, CELL):
            pygame.draw.line(screen, GRID, (0, gy), (W, gy))

        fx, fy = food
        pygame.draw.rect(screen, FOOD,
                         (fx*CELL+3, fy*CELL+3, CELL-6, CELL-6), border_radius=4)

        for i, (sx, sy) in enumerate(snake):
            col = HEAD if i == 0 else SNAKE
            pygame.draw.rect(screen, col,
                             (sx*CELL+1, sy*CELL+1, CELL-2, CELL-2), border_radius=3)

        screen.blit(font.render(f"SCORE {score}", True, TEXT), (8, 6))

        if not alive:
            msg = font.render("GAME OVER  tap R", True, FOOD)
            screen.blit(msg, (W//2 - msg.get_width()//2, H//2))

        pygame.display.flip()
        clock.tick(FPS)


def _new_food(snake):
    while True:
        f = (random.randint(0, COLS-1), random.randint(0, ROWS-1))
        if f not in snake:
            return f


if __name__ == "__main__":
    main()

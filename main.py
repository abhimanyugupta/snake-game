"""Minimal pygame frontend for the Snake game."""

from __future__ import annotations

from dataclasses import replace
import sys

import pygame

from snake.game_logic import (
    STATUS_GAME_OVER,
    STATUS_PAUSED,
    STATUS_RUNNING,
    GameState,
    initial_state,
    restart,
    set_direction,
    tick,
)

CELL_SIZE = 24
GRID_WIDTH = 20
GRID_HEIGHT = 20
TOP_BAR = 48
FPS = 60

COLOR_BG = (24, 24, 24)
COLOR_GRID = (42, 42, 42)
COLOR_SNAKE = (74, 168, 77)
COLOR_FOOD = (220, 76, 70)
COLOR_TEXT = (235, 235, 235)

KEY_TO_DIRECTION = {
    pygame.K_UP: (0, -1),
    pygame.K_w: (0, -1),
    pygame.K_DOWN: (0, 1),
    pygame.K_s: (0, 1),
    pygame.K_LEFT: (-1, 0),
    pygame.K_a: (-1, 0),
    pygame.K_RIGHT: (1, 0),
    pygame.K_d: (1, 0),
}


def draw_board(surface: pygame.Surface, state: GameState, font: pygame.font.Font) -> None:
    surface.fill(COLOR_BG)

    board_rect = pygame.Rect(0, TOP_BAR, GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE)

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            rect = pygame.Rect(x * CELL_SIZE, TOP_BAR + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, COLOR_GRID, rect, 1)

    for x, y in state.snake:
        rect = pygame.Rect(x * CELL_SIZE + 1, TOP_BAR + y * CELL_SIZE + 1, CELL_SIZE - 2, CELL_SIZE - 2)
        pygame.draw.rect(surface, COLOR_SNAKE, rect)

    if state.food is not None:
        fx, fy = state.food
        rect = pygame.Rect(fx * CELL_SIZE + 2, TOP_BAR + fy * CELL_SIZE + 2, CELL_SIZE - 4, CELL_SIZE - 4)
        pygame.draw.rect(surface, COLOR_FOOD, rect)

    score_text = f"Score: {state.score}"
    info = "Arrows/WASD move | P pause | R restart | Esc quit"
    surface.blit(font.render(score_text, True, COLOR_TEXT), (10, 10))
    surface.blit(font.render(info, True, COLOR_TEXT), (140, 10))

    if state.status == STATUS_PAUSED:
        _draw_center_message(surface, board_rect, font, "Paused")
    elif state.status == STATUS_GAME_OVER:
        _draw_center_message(surface, board_rect, font, "Game Over - Press R to Restart")


def _draw_center_message(
    surface: pygame.Surface,
    board_rect: pygame.Rect,
    font: pygame.font.Font,
    text: str,
) -> None:
    label = font.render(text, True, COLOR_TEXT)
    label_rect = label.get_rect(center=board_rect.center)

    pad = 12
    bg_rect = label_rect.inflate(pad * 2, pad)
    pygame.draw.rect(surface, (0, 0, 0), bg_rect, border_radius=6)
    pygame.draw.rect(surface, COLOR_TEXT, bg_rect, 1, border_radius=6)
    surface.blit(label, label_rect)


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Snake")

    width_px = GRID_WIDTH * CELL_SIZE
    height_px = GRID_HEIGHT * CELL_SIZE + TOP_BAR

    screen = pygame.display.set_mode((width_px, height_px))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    state = initial_state(width=GRID_WIDTH, height=GRID_HEIGHT, tick_ms=120)
    elapsed_ms = 0

    while True:
        frame_ms = clock.tick(FPS)
        elapsed_ms += frame_ms

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)
                if event.key == pygame.K_r:
                    state = restart(state)
                    elapsed_ms = 0
                elif event.key == pygame.K_p:
                    if state.status == STATUS_RUNNING:
                        state = replace(state, status=STATUS_PAUSED)
                    elif state.status == STATUS_PAUSED:
                        state = replace(state, status=STATUS_RUNNING)
                elif event.key in KEY_TO_DIRECTION:
                    state = set_direction(state, KEY_TO_DIRECTION[event.key])

        while state.status == STATUS_RUNNING and elapsed_ms >= state.tick_ms:
            state = tick(state)
            elapsed_ms -= state.tick_ms

        draw_board(screen, state, font)
        pygame.display.flip()


if __name__ == "__main__":
    main()
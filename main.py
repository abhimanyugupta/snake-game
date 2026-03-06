"""Minimal pygame frontend for Snake with classic+ options."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import sys

import pygame

from snake.game_logic import (
    STATUS_GAME_OVER,
    STATUS_PAUSED,
    STATUS_RUNNING,
    GameState,
    current_tick_ms,
    initial_state,
    restart,
    set_direction,
    tick,
)

CELL_SIZE = 24
GRID_WIDTH = 20
GRID_HEIGHT = 20
TOP_BAR = 70
FPS = 60
OBSTACLE_COUNT = 18
HIGH_SCORE_PATH = Path(__file__).with_name("high_score.txt")

COLOR_BG = (24, 24, 24)
COLOR_GRID = (42, 42, 42)
COLOR_SNAKE = (74, 168, 77)
COLOR_FOOD = (220, 76, 70)
COLOR_BONUS = (240, 185, 60)
COLOR_OBSTACLE = (100, 100, 100)
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

DIFFICULTIES = (
    {
        "name": "Easy",
        "base_tick_ms": 160,
        "min_tick_ms": 95,
        "speed_step_ms": 4,
        "speed_every_points": 4,
    },
    {
        "name": "Normal",
        "base_tick_ms": 125,
        "min_tick_ms": 75,
        "speed_step_ms": 5,
        "speed_every_points": 3,
    },
    {
        "name": "Hard",
        "base_tick_ms": 95,
        "min_tick_ms": 55,
        "speed_step_ms": 6,
        "speed_every_points": 2,
    },
)


@dataclass
class MenuConfig:
    difficulty_index: int = 1
    wrap_walls: bool = False
    obstacles_mode: bool = False


def load_high_score() -> int:
    try:
        raw = HIGH_SCORE_PATH.read_text(encoding="ascii").strip()
        return max(0, int(raw))
    except (OSError, ValueError):
        return 0


def save_high_score(score: int) -> None:
    try:
        HIGH_SCORE_PATH.write_text(str(max(0, score)), encoding="ascii")
    except OSError:
        # Keep gameplay functional even if persistence fails.
        pass


def build_state(menu: MenuConfig) -> GameState:
    difficulty = DIFFICULTIES[menu.difficulty_index]
    return initial_state(
        width=GRID_WIDTH,
        height=GRID_HEIGHT,
        start_length=3,
        base_tick_ms=difficulty["base_tick_ms"],
        min_tick_ms=difficulty["min_tick_ms"],
        speed_step_ms=difficulty["speed_step_ms"],
        speed_every_points=difficulty["speed_every_points"],
        wrap_walls=menu.wrap_walls,
        obstacle_count=OBSTACLE_COUNT if menu.obstacles_mode else 0,
        bonus_frequency=5,
        bonus_lifetime_ticks=26,
        bonus_points=5,
    )


def draw_menu(
    surface: pygame.Surface,
    title_font: pygame.font.Font,
    font: pygame.font.Font,
    menu: MenuConfig,
    high_score: int,
) -> None:
    surface.fill(COLOR_BG)

    lines = [
        (title_font, "Snake", COLOR_TEXT),
        (font, "Main Menu", COLOR_TEXT),
        (font, f"High Score: {high_score}", COLOR_TEXT),
        (font, "", COLOR_TEXT),
    ]

    for idx, difficulty in enumerate(DIFFICULTIES):
        marker = ">" if menu.difficulty_index == idx else " "
        lines.append((font, f"{marker} {idx + 1}. {difficulty['name']}", COLOR_TEXT))

    wrap_text = "ON" if menu.wrap_walls else "OFF"
    obstacles_text = "ON" if menu.obstacles_mode else "OFF"

    lines.extend(
        [
            (font, "", COLOR_TEXT),
            (font, f"W: Wrap Walls [{wrap_text}]", COLOR_TEXT),
            (font, f"O: Obstacles Mode [{obstacles_text}]", COLOR_TEXT),
            (font, "", COLOR_TEXT),
            (font, "Up/Down or 1/2/3 choose difficulty", COLOR_TEXT),
            (font, "Enter/Space start game", COLOR_TEXT),
            (font, "Esc quit", COLOR_TEXT),
        ]
    )

    y = 40
    for line_font, text, color in lines:
        if text:
            surface.blit(line_font.render(text, True, color), (40, y))
        y += 32


def draw_board(
    surface: pygame.Surface,
    state: GameState,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    difficulty_name: str,
    high_score: int,
) -> None:
    surface.fill(COLOR_BG)

    board_rect = pygame.Rect(0, TOP_BAR, state.width * CELL_SIZE, state.height * CELL_SIZE)

    for y in range(state.height):
        for x in range(state.width):
            rect = pygame.Rect(x * CELL_SIZE, TOP_BAR + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, COLOR_GRID, rect, 1)

    for x, y in state.obstacles:
        rect = pygame.Rect(x * CELL_SIZE + 1, TOP_BAR + y * CELL_SIZE + 1, CELL_SIZE - 2, CELL_SIZE - 2)
        pygame.draw.rect(surface, COLOR_OBSTACLE, rect)

    for x, y in state.snake:
        rect = pygame.Rect(x * CELL_SIZE + 1, TOP_BAR + y * CELL_SIZE + 1, CELL_SIZE - 2, CELL_SIZE - 2)
        pygame.draw.rect(surface, COLOR_SNAKE, rect)

    if state.food is not None:
        fx, fy = state.food
        rect = pygame.Rect(fx * CELL_SIZE + 2, TOP_BAR + fy * CELL_SIZE + 2, CELL_SIZE - 4, CELL_SIZE - 4)
        pygame.draw.rect(surface, COLOR_FOOD, rect)

    if state.bonus_food is not None:
        bx, by = state.bonus_food
        rect = pygame.Rect(bx * CELL_SIZE + 4, TOP_BAR + by * CELL_SIZE + 4, CELL_SIZE - 8, CELL_SIZE - 8)
        pygame.draw.rect(surface, COLOR_BONUS, rect)

    wrap_text = "ON" if state.wrap_walls else "OFF"
    obstacles_text = "ON" if state.obstacle_count > 0 else "OFF"
    bonus_text = f"Bonus: {state.bonus_timer_ticks}" if state.bonus_food is not None else "Bonus: -"

    row1 = f"Score: {state.score}    High: {high_score}    Difficulty: {difficulty_name}"
    row2 = (
        f"Speed: {current_tick_ms(state)}ms/tick    Wrap: {wrap_text}    Obstacles: {obstacles_text}    {bonus_text}"
    )
    row3 = "Arrows/WASD move | P pause | R restart | M menu | Esc quit"

    surface.blit(font.render(row1, True, COLOR_TEXT), (10, 8))
    surface.blit(small_font.render(row2, True, COLOR_TEXT), (10, 32))
    surface.blit(small_font.render(row3, True, COLOR_TEXT), (10, 50))

    if state.status == STATUS_PAUSED:
        _draw_center_message(surface, board_rect, font, "Paused")
    elif state.status == STATUS_GAME_OVER:
        _draw_center_message(surface, board_rect, font, "Game Over - Press R or M")


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
    title_font = pygame.font.SysFont(None, 54)
    font = pygame.font.SysFont(None, 28)
    small_font = pygame.font.SysFont(None, 22)

    menu = MenuConfig()
    screen_mode = "menu"
    state: GameState | None = None
    elapsed_ms = 0

    high_score = load_high_score()
    game_over_recorded = False

    while True:
        frame_ms = clock.tick(FPS)

        if screen_mode == "playing":
            elapsed_ms += frame_ms

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit(0)

            if screen_mode == "menu":
                if event.key == pygame.K_UP:
                    menu.difficulty_index = (menu.difficulty_index - 1) % len(DIFFICULTIES)
                elif event.key == pygame.K_DOWN:
                    menu.difficulty_index = (menu.difficulty_index + 1) % len(DIFFICULTIES)
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    menu.difficulty_index = min(len(DIFFICULTIES) - 1, event.key - pygame.K_1)
                elif event.key == pygame.K_w:
                    menu.wrap_walls = not menu.wrap_walls
                elif event.key == pygame.K_o:
                    menu.obstacles_mode = not menu.obstacles_mode
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    state = build_state(menu)
                    screen_mode = "playing"
                    elapsed_ms = 0
                    game_over_recorded = False
            elif state is not None:
                if event.key == pygame.K_m:
                    screen_mode = "menu"
                    state = None
                    elapsed_ms = 0
                elif event.key == pygame.K_r:
                    state = restart(state)
                    elapsed_ms = 0
                    game_over_recorded = False
                elif event.key == pygame.K_p:
                    if state.status == STATUS_RUNNING:
                        state = replace(state, status=STATUS_PAUSED)
                    elif state.status == STATUS_PAUSED:
                        state = replace(state, status=STATUS_RUNNING)
                elif event.key in KEY_TO_DIRECTION:
                    state = set_direction(state, KEY_TO_DIRECTION[event.key])

        if screen_mode == "playing" and state is not None:
            while state.status == STATUS_RUNNING:
                interval_ms = current_tick_ms(state)
                if elapsed_ms < interval_ms:
                    break
                elapsed_ms -= interval_ms
                state = tick(state)

            if state.status == STATUS_GAME_OVER and not game_over_recorded:
                if state.score > high_score:
                    high_score = state.score
                    save_high_score(high_score)
                game_over_recorded = True

            difficulty_name = DIFFICULTIES[menu.difficulty_index]["name"]
            draw_board(screen, state, font, small_font, difficulty_name, high_score)
        else:
            draw_menu(screen, title_font, font, menu, high_score)

        pygame.display.flip()


if __name__ == "__main__":
    main()
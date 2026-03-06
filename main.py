"""Premium-styled pygame frontend for Snake with classic+ options."""

from __future__ import annotations

from dataclasses import dataclass, replace
import math
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
BOARD_PIXEL_W = GRID_WIDTH * CELL_SIZE
BOARD_PIXEL_H = GRID_HEIGHT * CELL_SIZE
WINDOW_PADDING = 20
TOP_BAR = 96
FPS = 60
OBSTACLE_COUNT = 18
HIGH_SCORE_PATH = Path(__file__).with_name("high_score.txt")

COLOR_TEXT = (236, 238, 246)
COLOR_TEXT_MUTED = (176, 182, 201)
COLOR_ACCENT = (116, 211, 169)
COLOR_ACCENT_ALT = (91, 151, 255)
COLOR_BG_TOP = (11, 16, 28)
COLOR_BG_BOTTOM = (21, 33, 45)
COLOR_BOARD_TOP = (15, 27, 36)
COLOR_BOARD_BOTTOM = (9, 18, 27)
COLOR_GRID = (52, 68, 86)
COLOR_SNAKE_HEAD = (143, 233, 154)
COLOR_SNAKE_BODY = (76, 179, 102)
COLOR_SNAKE_BORDER = (42, 108, 62)
COLOR_FOOD = (255, 110, 90)
COLOR_FOOD_GLOW = (255, 126, 96)
COLOR_BONUS = (255, 202, 87)
COLOR_BONUS_GLOW = (255, 212, 110)
COLOR_OBSTACLE = (95, 113, 132)
COLOR_OBSTACLE_SHADE = (58, 74, 90)

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


def lerp_color(color_a: tuple[int, int, int], color_b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(color_a[0] + (color_b[0] - color_a[0]) * t),
        int(color_a[1] + (color_b[1] - color_a[1]) * t),
        int(color_a[2] + (color_b[2] - color_a[2]) * t),
    )


def draw_vertical_gradient(
    surface: pygame.Surface,
    rect: pygame.Rect,
    top_color: tuple[int, int, int],
    bottom_color: tuple[int, int, int],
) -> None:
    if rect.height <= 0:
        return

    for y in range(rect.height):
        t = y / max(1, rect.height - 1)
        color = lerp_color(top_color, bottom_color, t)
        pygame.draw.line(surface, color, (rect.x, rect.y + y), (rect.right - 1, rect.y + y))


def draw_soft_shadow(surface: pygame.Surface, rect: pygame.Rect, radius: int = 16) -> None:
    shadow_surface = pygame.Surface((rect.width + 14, rect.height + 14), pygame.SRCALPHA)
    pygame.draw.rect(
        shadow_surface,
        (0, 0, 0, 72),
        pygame.Rect(7, 7, rect.width, rect.height),
        border_radius=radius,
    )
    surface.blit(shadow_surface, (rect.x - 7, rect.y - 7))


def draw_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    fill_top: tuple[int, int, int],
    fill_bottom: tuple[int, int, int],
    border_color: tuple[int, int, int],
    radius: int,
) -> None:
    draw_soft_shadow(surface, rect, radius=radius)

    panel_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    draw_vertical_gradient(
        panel_surface,
        pygame.Rect(0, 0, rect.width, rect.height),
        fill_top,
        fill_bottom,
    )
    pygame.draw.rect(panel_surface, border_color, pygame.Rect(0, 0, rect.width, rect.height), 1, border_radius=radius)
    surface.blit(panel_surface, rect.topleft)


def draw_glow(
    surface: pygame.Surface,
    center: tuple[int, int],
    color: tuple[int, int, int],
    radius: int,
    alpha_strength: int,
) -> None:
    glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for layer in range(4, 0, -1):
        layer_radius = max(2, int(radius * (layer / 4.0)))
        alpha = int(alpha_strength * (layer / 4.0) ** 2)
        pygame.draw.circle(glow, (color[0], color[1], color[2], alpha), (radius, radius), layer_radius)
    surface.blit(glow, (center[0] - radius, center[1] - radius))


def draw_chip(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    x: int,
    y: int,
    fill_color: tuple[int, int, int],
    border_color: tuple[int, int, int],
    text_color: tuple[int, int, int] = COLOR_TEXT,
) -> int:
    label = font.render(text, True, text_color)
    chip_rect = pygame.Rect(x, y, label.get_width() + 18, label.get_height() + 10)

    pygame.draw.rect(surface, fill_color, chip_rect, border_radius=12)
    pygame.draw.rect(surface, border_color, chip_rect, 1, border_radius=12)
    surface.blit(label, (chip_rect.x + 9, chip_rect.y + 5))
    return chip_rect.right + 8


def build_background(width_px: int, height_px: int) -> pygame.Surface:
    background = pygame.Surface((width_px, height_px)).convert()
    draw_vertical_gradient(background, pygame.Rect(0, 0, width_px, height_px), COLOR_BG_TOP, COLOR_BG_BOTTOM)

    pattern = pygame.Surface((width_px, height_px), pygame.SRCALPHA)
    spacing = 28
    for x in range(-height_px, width_px, spacing):
        pygame.draw.line(pattern, (255, 255, 255, 8), (x, 0), (x + height_px, height_px), 1)
    background.blit(pattern, (0, 0))

    vignette = pygame.Surface((width_px, height_px), pygame.SRCALPHA)
    edge_steps = 110
    for i in range(edge_steps):
        alpha = int(130 * (i / edge_steps) ** 2)
        rect = pygame.Rect(i, i, width_px - (i * 2), height_px - (i * 2))
        if rect.width <= 0 or rect.height <= 0:
            break
        pygame.draw.rect(vignette, (0, 0, 0, alpha), rect, 1)
    background.blit(vignette, (0, 0))

    return background


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


def board_rect_from_state(state: GameState) -> pygame.Rect:
    return pygame.Rect(
        WINDOW_PADDING,
        TOP_BAR,
        state.width * CELL_SIZE,
        state.height * CELL_SIZE,
    )


def cell_rect(board_rect: pygame.Rect, cell_x: int, cell_y: int, inset: int) -> pygame.Rect:
    return pygame.Rect(
        board_rect.x + (cell_x * CELL_SIZE) + inset,
        board_rect.y + (cell_y * CELL_SIZE) + inset,
        CELL_SIZE - (inset * 2),
        CELL_SIZE - (inset * 2),
    )


def draw_menu(
    surface: pygame.Surface,
    background: pygame.Surface,
    title_font: pygame.font.Font,
    ui_font: pygame.font.Font,
    small_font: pygame.font.Font,
    menu: MenuConfig,
    high_score: int,
    time_seconds: float,
) -> None:
    surface.blit(background, (0, 0))

    card_rect = pygame.Rect(46, 44, surface.get_width() - 92, surface.get_height() - 88)
    draw_panel(surface, card_rect, (30, 42, 58), (18, 26, 38), (87, 109, 132), radius=18)

    title_offset = int(math.sin(time_seconds * 2.3) * 3)
    title_label = title_font.render("SNAKE", True, COLOR_TEXT)
    subtitle_label = small_font.render("Classic Plus Edition", True, COLOR_TEXT_MUTED)
    surface.blit(title_label, (card_rect.x + 28, card_rect.y + 22 + title_offset))
    surface.blit(subtitle_label, (card_rect.x + 32, card_rect.y + 72 + title_offset))

    chip_x = card_rect.right - 165
    draw_chip(
        surface,
        small_font,
        f"High Score {high_score}",
        chip_x,
        card_rect.y + 34,
        (40, 61, 88),
        (86, 117, 151),
    )

    options_start_y = card_rect.y + 128
    for idx, difficulty in enumerate(DIFFICULTIES):
        option_rect = pygame.Rect(card_rect.x + 28, options_start_y + idx * 52, card_rect.width - 56, 42)
        selected = idx == menu.difficulty_index

        fill_top = (55, 88, 124) if selected else (30, 41, 56)
        fill_bottom = (40, 66, 99) if selected else (23, 32, 44)
        border = COLOR_ACCENT_ALT if selected else (76, 94, 114)

        draw_panel(surface, option_rect, fill_top, fill_bottom, border, radius=12)
        text = f"{idx + 1}. {difficulty['name']}"
        value = f"{difficulty['base_tick_ms']}ms"
        surface.blit(ui_font.render(text, True, COLOR_TEXT), (option_rect.x + 14, option_rect.y + 8))
        surface.blit(small_font.render(value, True, COLOR_TEXT_MUTED), (option_rect.right - 84, option_rect.y + 12))

    toggle_y = options_start_y + (len(DIFFICULTIES) * 52) + 8
    wrap_value = "ON" if menu.wrap_walls else "OFF"
    obstacles_value = "ON" if menu.obstacles_mode else "OFF"

    draw_chip(
        surface,
        small_font,
        f"W Wrap {wrap_value}",
        card_rect.x + 28,
        toggle_y,
        (30, 49, 72) if menu.wrap_walls else (35, 36, 45),
        (90, 123, 158) if menu.wrap_walls else (76, 80, 94),
    )
    draw_chip(
        surface,
        small_font,
        f"O Obstacles {obstacles_value}",
        card_rect.x + 170,
        toggle_y,
        (45, 54, 70) if menu.obstacles_mode else (35, 36, 45),
        (126, 142, 169) if menu.obstacles_mode else (76, 80, 94),
    )

    helper_lines = [
        "Up/Down or 1/2/3: Difficulty",
        "W: Wrap mode  |  O: Obstacles mode",
        "Enter/Space: Start   Esc: Quit",
    ]

    helper_y = card_rect.bottom - 92
    for i, line in enumerate(helper_lines):
        label = small_font.render(line, True, COLOR_TEXT_MUTED)
        surface.blit(label, (card_rect.x + 28, helper_y + i * 24))


def draw_game_overlay(
    surface: pygame.Surface,
    board_rect: pygame.Rect,
    title_font: pygame.font.Font,
    ui_font: pygame.font.Font,
    title: str,
    subtitle: str,
) -> None:
    dim_surface = pygame.Surface((board_rect.width, board_rect.height), pygame.SRCALPHA)
    dim_surface.fill((2, 6, 10, 150))
    surface.blit(dim_surface, board_rect.topleft)

    box_rect = pygame.Rect(0, 0, board_rect.width - 120, 108)
    box_rect.center = board_rect.center
    draw_panel(surface, box_rect, (31, 44, 62), (18, 27, 39), (108, 131, 155), radius=14)

    title_label = title_font.render(title, True, COLOR_TEXT)
    subtitle_label = ui_font.render(subtitle, True, COLOR_TEXT_MUTED)
    surface.blit(title_label, title_label.get_rect(center=(box_rect.centerx, box_rect.y + 35)))
    surface.blit(subtitle_label, subtitle_label.get_rect(center=(box_rect.centerx, box_rect.y + 74)))


def draw_board(
    surface: pygame.Surface,
    background: pygame.Surface,
    state: GameState,
    ui_font: pygame.font.Font,
    small_font: pygame.font.Font,
    difficulty_name: str,
    high_score: int,
    time_seconds: float,
) -> None:
    surface.blit(background, (0, 0))

    board_rect = board_rect_from_state(state)
    board_outer = board_rect.inflate(10, 10)
    hud_rect = pygame.Rect(WINDOW_PADDING, 14, board_rect.width, TOP_BAR - 22)

    draw_panel(surface, hud_rect, (28, 42, 58), (17, 27, 39), (82, 104, 127), radius=14)
    draw_panel(surface, board_outer, (22, 33, 45), (15, 21, 30), (68, 88, 108), radius=12)

    board_surface = pygame.Surface((board_rect.width, board_rect.height)).convert()
    draw_vertical_gradient(
        board_surface,
        pygame.Rect(0, 0, board_rect.width, board_rect.height),
        COLOR_BOARD_TOP,
        COLOR_BOARD_BOTTOM,
    )

    for y in range(state.height):
        row_tint = 8 if y % 2 == 0 else 0
        row_rect = pygame.Rect(0, y * CELL_SIZE, board_rect.width, CELL_SIZE)
        pygame.draw.rect(board_surface, (20 + row_tint, 32 + row_tint, 42 + row_tint), row_rect, 0)

    for x in range(state.width + 1):
        px = x * CELL_SIZE
        pygame.draw.line(board_surface, COLOR_GRID, (px, 0), (px, board_rect.height), 1)
    for y in range(state.height + 1):
        py = y * CELL_SIZE
        pygame.draw.line(board_surface, COLOR_GRID, (0, py), (board_rect.width, py), 1)

    surface.blit(board_surface, board_rect.topleft)

    for obstacle_x, obstacle_y in state.obstacles:
        rect = cell_rect(board_rect, obstacle_x, obstacle_y, inset=3)
        pygame.draw.rect(surface, COLOR_OBSTACLE_SHADE, rect, border_radius=6)
        top_half = pygame.Rect(rect.x + 1, rect.y + 1, rect.width - 2, rect.height // 2)
        pygame.draw.rect(surface, COLOR_OBSTACLE, top_half, border_radius=6)
        pygame.draw.rect(surface, (57, 74, 90), rect, 1, border_radius=6)

    for idx, (snake_x, snake_y) in enumerate(state.snake):
        rect = cell_rect(board_rect, snake_x, snake_y, inset=2)
        fill_color = COLOR_SNAKE_HEAD if idx == 0 else COLOR_SNAKE_BODY
        pygame.draw.rect(surface, fill_color, rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_SNAKE_BORDER, rect, 1, border_radius=8)

        highlight = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, max(3, rect.height // 3))
        pygame.draw.rect(surface, (197, 243, 198, 95), highlight, border_radius=7)

    if state.snake:
        head_x, head_y = state.snake[0]
        head_rect = cell_rect(board_rect, head_x, head_y, inset=2)
        dx, dy = state.direction

        eye_y = head_rect.centery - 3 if dy >= 0 else head_rect.centery + 1
        if dx != 0:
            eye_offset = 4 if dx > 0 else -4
            left_eye = (head_rect.centerx + eye_offset, head_rect.centery - 4)
            right_eye = (head_rect.centerx + eye_offset, head_rect.centery + 4)
        else:
            left_eye = (head_rect.centerx - 4, eye_y)
            right_eye = (head_rect.centerx + 4, eye_y)

        pygame.draw.circle(surface, (18, 39, 28), left_eye, 2)
        pygame.draw.circle(surface, (18, 39, 28), right_eye, 2)

    food_pulse = 0.5 + 0.5 * math.sin(time_seconds * 5.2)

    if state.food is not None:
        food_center = (
            board_rect.x + state.food[0] * CELL_SIZE + CELL_SIZE // 2,
            board_rect.y + state.food[1] * CELL_SIZE + CELL_SIZE // 2,
        )
        draw_glow(surface, food_center, COLOR_FOOD_GLOW, 18 + int(food_pulse * 2), 95)
        pygame.draw.circle(surface, COLOR_FOOD, food_center, 6 + int(food_pulse * 1.8))
        pygame.draw.circle(surface, (255, 186, 173), (food_center[0] - 2, food_center[1] - 2), 2)

    if state.bonus_food is not None:
        bonus_center = (
            board_rect.x + state.bonus_food[0] * CELL_SIZE + CELL_SIZE // 2,
            board_rect.y + state.bonus_food[1] * CELL_SIZE + CELL_SIZE // 2,
        )
        bonus_pulse = 0.5 + 0.5 * math.sin(time_seconds * 6.0)
        radius = 8 + int(bonus_pulse * 2)
        draw_glow(surface, bonus_center, COLOR_BONUS_GLOW, 24 + int(bonus_pulse * 2), 128)
        diamond = [
            (bonus_center[0], bonus_center[1] - radius),
            (bonus_center[0] + radius, bonus_center[1]),
            (bonus_center[0], bonus_center[1] + radius),
            (bonus_center[0] - radius, bonus_center[1]),
        ]
        pygame.draw.polygon(surface, COLOR_BONUS, diamond)
        pygame.draw.polygon(surface, (255, 240, 196), diamond, 1)

    draw_chip(surface, small_font, f"Score {state.score}", hud_rect.x + 12, hud_rect.y + 10, (30, 53, 72), (88, 120, 153))
    chip_x = draw_chip(
        surface,
        small_font,
        f"High {high_score}",
        hud_rect.x + 116,
        hud_rect.y + 10,
        (30, 53, 72),
        (88, 120, 153),
    )
    chip_x = draw_chip(
        surface,
        small_font,
        difficulty_name,
        chip_x,
        hud_rect.y + 10,
        (40, 70, 102),
        (91, 151, 255),
    )

    wrap_text = "Wrap ON" if state.wrap_walls else "Wrap OFF"
    obstacle_text = "Obstacles ON" if state.obstacle_count > 0 else "Obstacles OFF"
    bonus_text = f"Bonus {state.bonus_timer_ticks}" if state.bonus_food is not None else "Bonus -"

    draw_chip(surface, small_font, wrap_text, chip_x, hud_rect.y + 10, (40, 57, 78), (95, 117, 142))
    draw_chip(surface, small_font, obstacle_text, hud_rect.x + 12, hud_rect.y + 42, (40, 57, 78), (95, 117, 142))
    draw_chip(
        surface,
        small_font,
        f"Speed {current_tick_ms(state)}ms",
        hud_rect.x + 160,
        hud_rect.y + 42,
        (40, 57, 78),
        (95, 117, 142),
    )
    draw_chip(surface, small_font, bonus_text, hud_rect.x + 312, hud_rect.y + 42, (60, 62, 48), (151, 138, 91))

    controls = "Arrows/WASD move   P pause   R restart   M menu   Esc quit"
    controls_label = small_font.render(controls, True, COLOR_TEXT_MUTED)
    surface.blit(controls_label, (WINDOW_PADDING + 4, board_rect.bottom + 10))

    if state.status == STATUS_PAUSED:
        draw_game_overlay(surface, board_rect, ui_font, small_font, "Paused", "Press P to resume")
    elif state.status == STATUS_GAME_OVER:
        draw_game_overlay(surface, board_rect, ui_font, small_font, "Game Over", "Press R to retry or M for menu")


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Snake")

    width_px = BOARD_PIXEL_W + (WINDOW_PADDING * 2)
    height_px = TOP_BAR + BOARD_PIXEL_H + WINDOW_PADDING + 34

    screen = pygame.display.set_mode((width_px, height_px))
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("segoeui", 58, bold=True)
    ui_font = pygame.font.SysFont("segoeui", 30, bold=True)
    small_font = pygame.font.SysFont("segoeui", 20)

    background = build_background(width_px, height_px)

    menu = MenuConfig()
    screen_mode = "menu"
    state: GameState | None = None
    elapsed_ms = 0

    high_score = load_high_score()
    game_over_recorded = False

    while True:
        frame_ms = clock.tick(FPS)
        time_seconds = pygame.time.get_ticks() / 1000.0

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
            draw_board(
                surface=screen,
                background=background,
                state=state,
                ui_font=ui_font,
                small_font=small_font,
                difficulty_name=difficulty_name,
                high_score=high_score,
                time_seconds=time_seconds,
            )
        else:
            draw_menu(
                surface=screen,
                background=background,
                title_font=title_font,
                ui_font=ui_font,
                small_font=small_font,
                menu=menu,
                high_score=high_score,
                time_seconds=time_seconds,
            )

        pygame.display.flip()


if __name__ == "__main__":
    main()
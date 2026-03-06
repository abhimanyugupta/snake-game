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
CONTROL_AREA_HEIGHT = 72
FPS = 60
OBSTACLE_COUNT = 18
HIGH_SCORE_PATH = Path(__file__).with_name("high_score.txt")

COLOR_TEXT = (236, 238, 246)
COLOR_TEXT_MUTED = (176, 182, 201)
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


def draw_key_hint(
    surface: pygame.Surface,
    font: pygame.font.Font,
    key_text: str,
    label_text: str,
    x: int,
    y: int,
) -> int:
    key_label = font.render(key_text, True, COLOR_TEXT)
    key_rect = pygame.Rect(x, y, key_label.get_width() + 14, key_label.get_height() + 8)
    pygame.draw.rect(surface, (39, 58, 82), key_rect, border_radius=8)
    pygame.draw.rect(surface, (102, 131, 167), key_rect, 1, border_radius=8)
    surface.blit(key_label, (key_rect.x + 7, key_rect.y + 4))

    text_label = font.render(label_text, True, COLOR_TEXT_MUTED)
    surface.blit(text_label, (key_rect.right + 8, key_rect.y + 4))
    return key_rect.right + text_label.get_width() + 20


def wrap_text(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]

    for word in words[1:]:
        trial = f"{current} {word}"
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


def ellipsize_text(font: pygame.font.Font, text: str, max_width: int) -> str:
    if font.size(text)[0] <= max_width:
        return text

    suffix = "..."
    trimmed = text
    while trimmed and font.size(trimmed + suffix)[0] > max_width:
        trimmed = trimmed[:-1]

    return (trimmed + suffix) if trimmed else suffix


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


def board_rect_from_state(state: GameState, shake_offset: tuple[int, int]) -> pygame.Rect:
    return pygame.Rect(
        WINDOW_PADDING + shake_offset[0],
        TOP_BAR + shake_offset[1],
        state.width * CELL_SIZE,
        state.height * CELL_SIZE,
    )


def cell_rect(board_rect: pygame.Rect, cell_x: float, cell_y: float, inset: int) -> pygame.Rect:
    return pygame.Rect(
        board_rect.x + int(round(cell_x * CELL_SIZE)) + inset,
        board_rect.y + int(round(cell_y * CELL_SIZE)) + inset,
        CELL_SIZE - (inset * 2),
        CELL_SIZE - (inset * 2),
    )


def interpolate_cell(
    start: tuple[int, int],
    end: tuple[int, int],
    alpha: float,
    wrap_walls: bool,
    width: int,
    height: int,
) -> tuple[float, float]:
    sx, sy = start
    ex, ey = end

    dx = ex - sx
    dy = ey - sy

    if wrap_walls:
        if dx > width / 2:
            dx -= width
        elif dx < -width / 2:
            dx += width
        if dy > height / 2:
            dy -= height
        elif dy < -height / 2:
            dy += height

        return ((sx + dx * alpha) % width, (sy + dy * alpha) % height)

    return (sx + dx * alpha, sy + dy * alpha)


def interpolated_snake_positions(
    state: GameState,
    previous_state: GameState | None,
    alpha: float,
) -> list[tuple[float, float]]:
    if previous_state is None:
        return [(float(x), float(y)) for x, y in state.snake]

    if alpha <= 0.0:
        return [(float(x), float(y)) for x, y in previous_state.snake]

    if alpha >= 1.0:
        return [(float(x), float(y)) for x, y in state.snake]

    positions: list[tuple[float, float]] = []
    for idx, segment in enumerate(state.snake):
        if idx == 0:
            start = previous_state.snake[0]
        elif idx - 1 < len(previous_state.snake):
            start = previous_state.snake[idx - 1]
        else:
            start = segment

        positions.append(
            interpolate_cell(
                start=start,
                end=segment,
                alpha=alpha,
                wrap_walls=state.wrap_walls,
                width=state.width,
                height=state.height,
            )
        )

    return positions


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
    ui_font: pygame.font.Font,
    small_font: pygame.font.Font,
    state: GameState,
    difficulty_name: str,
    high_score: int,
) -> None:
    dim_surface = pygame.Surface((board_rect.width, board_rect.height), pygame.SRCALPHA)
    dim_surface.fill((2, 6, 10, 150))
    surface.blit(dim_surface, board_rect.topleft)

    if state.status == STATUS_PAUSED:
        box_rect = pygame.Rect(0, 0, board_rect.width - 140, 128)
        box_rect.center = board_rect.center
        draw_panel(surface, box_rect, (31, 44, 62), (18, 27, 39), (108, 131, 155), radius=14)

        title_label = ui_font.render("Paused", True, COLOR_TEXT)
        subtitle_label = small_font.render("Press P to resume", True, COLOR_TEXT_MUTED)
        surface.blit(title_label, title_label.get_rect(center=(box_rect.centerx, box_rect.y + 38)))
        surface.blit(subtitle_label, subtitle_label.get_rect(center=(box_rect.centerx, box_rect.y + 76)))
        draw_key_hint(surface, small_font, "P", "Resume", box_rect.centerx - 40, box_rect.y + 90)
        return

    box_rect = pygame.Rect(0, 0, board_rect.width - 86, 206)
    box_rect.center = board_rect.center
    draw_panel(surface, box_rect, (31, 44, 62), (18, 27, 39), (108, 131, 155), radius=14)

    title_label = ui_font.render("Game Over", True, COLOR_TEXT)
    surface.blit(title_label, title_label.get_rect(center=(box_rect.centerx, box_rect.y + 34)))

    summary_1 = small_font.render(f"Score {state.score}   High {high_score}", True, COLOR_TEXT)
    summary_2 = small_font.render(
        f"Foods {state.foods_eaten}   Speed {current_tick_ms(state)}ms",
        True,
        COLOR_TEXT_MUTED,
    )
    mode_text = f"{difficulty_name} | {'Wrap ON' if state.wrap_walls else 'Wrap OFF'} | {'Obstacles ON' if state.obstacle_count > 0 else 'Obstacles OFF'}"
    summary_3 = small_font.render(mode_text, True, COLOR_TEXT_MUTED)

    surface.blit(summary_1, summary_1.get_rect(center=(box_rect.centerx, box_rect.y + 80)))
    surface.blit(summary_2, summary_2.get_rect(center=(box_rect.centerx, box_rect.y + 108)))
    surface.blit(summary_3, summary_3.get_rect(center=(box_rect.centerx, box_rect.y + 132)))

    draw_key_hint(surface, small_font, "R", "Retry", box_rect.x + 84, box_rect.y + 156)
    draw_key_hint(surface, small_font, "M", "Menu", box_rect.x + 214, box_rect.y + 156)


def draw_board(
    surface: pygame.Surface,
    background: pygame.Surface,
    state: GameState,
    snake_positions: list[tuple[float, float]],
    ui_font: pygame.font.Font,
    small_font: pygame.font.Font,
    difficulty_name: str,
    high_score: int,
    time_seconds: float,
    food_pops: list[dict[str, float]],
    score_pulse_ratio: float,
    shake_offset: tuple[int, int],
) -> None:
    surface.blit(background, (0, 0))

    board_rect = board_rect_from_state(state, shake_offset)
    board_outer = board_rect.inflate(10, 10)
    hud_rect = pygame.Rect(WINDOW_PADDING + shake_offset[0], 14 + shake_offset[1], board_rect.width, TOP_BAR - 22)
    controls_rect = pygame.Rect(
        WINDOW_PADDING + shake_offset[0],
        board_rect.bottom + 8,
        board_rect.width,
        CONTROL_AREA_HEIGHT - 16,
    )

    draw_panel(surface, hud_rect, (28, 42, 58), (17, 27, 39), (82, 104, 127), radius=14)
    draw_panel(surface, board_outer, (22, 33, 45), (15, 21, 30), (68, 88, 108), radius=12)
    draw_panel(surface, controls_rect, (24, 37, 52), (17, 24, 36), (66, 87, 108), radius=12)

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
        rect = cell_rect(board_rect, float(obstacle_x), float(obstacle_y), inset=3)
        pygame.draw.rect(surface, COLOR_OBSTACLE_SHADE, rect, border_radius=6)
        top_half = pygame.Rect(rect.x + 1, rect.y + 1, rect.width - 2, rect.height // 2)
        pygame.draw.rect(surface, COLOR_OBSTACLE, top_half, border_radius=6)
        pygame.draw.rect(surface, (57, 74, 90), rect, 1, border_radius=6)

    for idx, (snake_x, snake_y) in enumerate(snake_positions):
        rect = cell_rect(board_rect, snake_x, snake_y, inset=2)
        fill_color = COLOR_SNAKE_HEAD if idx == 0 else COLOR_SNAKE_BODY
        pygame.draw.rect(surface, fill_color, rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_SNAKE_BORDER, rect, 1, border_radius=8)

        highlight = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, max(3, rect.height // 3))
        pygame.draw.rect(surface, (197, 243, 198, 95), highlight, border_radius=7)

    if state.snake:
        head_x, head_y = snake_positions[0]
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

    for effect in food_pops:
        if effect["duration"] <= 0:
            continue
        progress = 1.0 - (effect["ms"] / effect["duration"])
        progress = max(0.0, min(1.0, progress))

        center = (
            board_rect.x + int(effect["x"] * CELL_SIZE) + CELL_SIZE // 2,
            board_rect.y + int(effect["y"] * CELL_SIZE) + CELL_SIZE // 2,
        )
        glow_color = COLOR_BONUS_GLOW if effect["bonus"] > 0 else COLOR_FOOD_GLOW
        ring_radius = 8 + int(progress * 18)
        alpha = int((1.0 - progress) * 165)

        ring_surface = pygame.Surface((ring_radius * 2, ring_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(ring_surface, (glow_color[0], glow_color[1], glow_color[2], alpha), (ring_radius, ring_radius), ring_radius, 2)
        surface.blit(ring_surface, (center[0] - ring_radius, center[1] - ring_radius))

    score_fill = lerp_color((30, 53, 72), (70, 103, 138), score_pulse_ratio)
    score_border = lerp_color((88, 120, 153), (145, 188, 228), score_pulse_ratio)

    draw_chip(surface, small_font, f"Score {state.score}", hud_rect.x + 12, hud_rect.y + 10, score_fill, score_border)
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

    wrap_text_value = "Wrap ON" if state.wrap_walls else "Wrap OFF"
    obstacle_text_value = "Obstacles ON" if state.obstacle_count > 0 else "Obstacles OFF"
    bonus_text_value = f"Bonus {state.bonus_timer_ticks}" if state.bonus_food is not None else "Bonus -"

    draw_chip(surface, small_font, wrap_text_value, chip_x, hud_rect.y + 10, (40, 57, 78), (95, 117, 142))
    draw_chip(surface, small_font, obstacle_text_value, hud_rect.x + 12, hud_rect.y + 42, (40, 57, 78), (95, 117, 142))
    draw_chip(
        surface,
        small_font,
        f"Speed {current_tick_ms(state)}ms",
        hud_rect.x + 160,
        hud_rect.y + 42,
        (40, 57, 78),
        (95, 117, 142),
    )
    draw_chip(surface, small_font, bonus_text_value, hud_rect.x + 312, hud_rect.y + 42, (60, 62, 48), (151, 138, 91))

    controls_text = "Arrows/WASD move  P pause  R restart  M menu  Esc quit"
    max_controls_width = controls_rect.width - 24
    control_lines = wrap_text(small_font, controls_text, max_controls_width)
    if len(control_lines) > 2:
        control_lines = [control_lines[0], ellipsize_text(small_font, " ".join(control_lines[1:]), max_controls_width)]

    for idx, line in enumerate(control_lines):
        label = small_font.render(line, True, COLOR_TEXT_MUTED)
        surface.blit(label, (controls_rect.x + 12, controls_rect.y + 8 + idx * 22))

    if state.status in (STATUS_PAUSED, STATUS_GAME_OVER):
        draw_game_overlay(surface, board_rect, ui_font, small_font, state, difficulty_name, high_score)


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Snake")

    width_px = BOARD_PIXEL_W + (WINDOW_PADDING * 2)
    height_px = TOP_BAR + BOARD_PIXEL_H + CONTROL_AREA_HEIGHT + WINDOW_PADDING

    screen = pygame.display.set_mode((width_px, height_px))
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("segoeui", 58, bold=True)
    ui_font = pygame.font.SysFont("segoeui", 30, bold=True)
    small_font = pygame.font.SysFont("segoeui", 20)

    background = build_background(width_px, height_px)

    menu = MenuConfig()
    screen_mode = "menu"
    state: GameState | None = None
    previous_state_for_render: GameState | None = None
    elapsed_ms = 0.0

    high_score = load_high_score()
    game_over_recorded = False

    score_pulse_ms = 0.0
    death_flash_ms = 0.0
    shake_ms = 0.0
    food_pops: list[dict[str, float]] = []

    while True:
        frame_ms = float(clock.tick(FPS))
        time_seconds = pygame.time.get_ticks() / 1000.0

        score_pulse_ms = max(0.0, score_pulse_ms - frame_ms)
        death_flash_ms = max(0.0, death_flash_ms - frame_ms)
        shake_ms = max(0.0, shake_ms - frame_ms)

        for effect in food_pops:
            effect["ms"] -= frame_ms
        food_pops = [effect for effect in food_pops if effect["ms"] > 0.0]

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
                    previous_state_for_render = None
                    screen_mode = "playing"
                    elapsed_ms = 0.0
                    game_over_recorded = False
                    food_pops = []
                    score_pulse_ms = 0.0
                    death_flash_ms = 0.0
                    shake_ms = 0.0
            elif state is not None:
                if event.key == pygame.K_m:
                    screen_mode = "menu"
                    state = None
                    previous_state_for_render = None
                    elapsed_ms = 0.0
                elif event.key == pygame.K_r:
                    state = restart(state)
                    previous_state_for_render = None
                    elapsed_ms = 0.0
                    game_over_recorded = False
                    food_pops = []
                    score_pulse_ms = 0.0
                    death_flash_ms = 0.0
                    shake_ms = 0.0
                elif event.key == pygame.K_p:
                    if state.status == STATUS_RUNNING:
                        state = replace(state, status=STATUS_PAUSED)
                    elif state.status == STATUS_PAUSED:
                        state = replace(state, status=STATUS_RUNNING)
                elif event.key in KEY_TO_DIRECTION:
                    state = set_direction(state, KEY_TO_DIRECTION[event.key])

        if screen_mode == "playing" and state is not None:
            while state.status == STATUS_RUNNING:
                interval_ms = float(current_tick_ms(state))
                if elapsed_ms < interval_ms:
                    break

                elapsed_ms -= interval_ms
                before_tick = state
                after_tick = tick(state)

                previous_state_for_render = before_tick

                score_delta = after_tick.score - before_tick.score
                if score_delta > 0:
                    score_pulse_ms = 220.0

                    ate_bonus = (
                        before_tick.bonus_food is not None
                        and score_delta >= before_tick.bonus_points
                        and after_tick.bonus_food != before_tick.bonus_food
                    )
                    effect_cell = before_tick.bonus_food if ate_bonus else before_tick.food
                    if effect_cell is not None:
                        food_pops.append(
                            {
                                "x": float(effect_cell[0]),
                                "y": float(effect_cell[1]),
                                "ms": 200.0,
                                "duration": 200.0,
                                "bonus": 1.0 if ate_bonus else 0.0,
                            }
                        )

                if before_tick.status == STATUS_RUNNING and after_tick.status == STATUS_GAME_OVER:
                    shake_ms = 260.0
                    death_flash_ms = 220.0

                state = after_tick

            if state.status == STATUS_GAME_OVER and not game_over_recorded:
                if state.score > high_score:
                    high_score = state.score
                    save_high_score(high_score)
                game_over_recorded = True

            if state.status == STATUS_RUNNING and previous_state_for_render is not None:
                tick_window = max(1.0, float(current_tick_ms(state)))
                interpolation_alpha = max(0.0, min(1.0, elapsed_ms / tick_window))
            else:
                interpolation_alpha = 1.0

            snake_positions = interpolated_snake_positions(
                state=state,
                previous_state=previous_state_for_render,
                alpha=interpolation_alpha,
            )

            shake_ratio = shake_ms / 260.0 if shake_ms > 0.0 else 0.0
            amplitude = int(6 * shake_ratio)
            shake_offset = (0, 0)
            if amplitude > 0:
                shake_offset = (
                    int(math.sin(time_seconds * 90.0) * amplitude),
                    int(math.cos(time_seconds * 120.0) * max(1, int(amplitude * 0.6))),
                )

            difficulty_name = DIFFICULTIES[menu.difficulty_index]["name"]
            draw_board(
                surface=screen,
                background=background,
                state=state,
                snake_positions=snake_positions,
                ui_font=ui_font,
                small_font=small_font,
                difficulty_name=difficulty_name,
                high_score=high_score,
                time_seconds=time_seconds,
                food_pops=food_pops,
                score_pulse_ratio=max(0.0, min(1.0, score_pulse_ms / 220.0)),
                shake_offset=shake_offset,
            )

            if death_flash_ms > 0.0:
                flash_alpha = int(140 * (death_flash_ms / 220.0))
                flash_surface = pygame.Surface((width_px, height_px), pygame.SRCALPHA)
                flash_surface.fill((170, 35, 35, flash_alpha))
                screen.blit(flash_surface, (0, 0))
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
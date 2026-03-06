
"""Premium-styled pygame frontend for Snake with themes, audio, and progression stats."""

from __future__ import annotations

from array import array
from dataclasses import asdict, dataclass, replace
import json
import math
from pathlib import Path
import sys
from typing import Any

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
TOP_BAR = 102
CONTROL_AREA_HEIGHT = 76
FPS = 60
OBSTACLE_COUNT = 18

HIGH_SCORE_PATH = Path(__file__).with_name("high_score.txt")
SETTINGS_PATH = Path(__file__).with_name("settings.json")
STATS_PATH = Path(__file__).with_name("stats.json")

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

THEMES: tuple[dict[str, Any], ...] = (
    {
        "name": "Midnight Neon",
        "colors": {
            "text": (236, 238, 246),
            "text_muted": (176, 182, 201),
            "accent": (91, 151, 255),
            "bg_top": (11, 16, 28),
            "bg_bottom": (21, 33, 45),
            "board_top": (15, 27, 36),
            "board_bottom": (9, 18, 27),
            "grid": (52, 68, 86),
            "snake_head": (143, 233, 154),
            "snake_body": (76, 179, 102),
            "snake_border": (42, 108, 62),
            "food": (255, 110, 90),
            "food_glow": (255, 126, 96),
            "bonus": (255, 202, 87),
            "bonus_glow": (255, 212, 110),
            "obstacle": (95, 113, 132),
            "obstacle_shade": (58, 74, 90),
            "panel_top": (28, 42, 58),
            "panel_bottom": (17, 27, 39),
            "panel_border": (82, 104, 127),
            "control_top": (24, 37, 52),
            "control_bottom": (17, 24, 36),
            "control_border": (66, 87, 108),
            "death_flash": (170, 35, 35),
        },
    },
    {
        "name": "Emerald Noir",
        "colors": {
            "text": (228, 240, 232),
            "text_muted": (160, 186, 168),
            "accent": (102, 216, 166),
            "bg_top": (8, 20, 19),
            "bg_bottom": (18, 39, 36),
            "board_top": (14, 33, 29),
            "board_bottom": (8, 23, 20),
            "grid": (45, 78, 69),
            "snake_head": (165, 244, 170),
            "snake_body": (86, 194, 117),
            "snake_border": (35, 103, 64),
            "food": (255, 129, 99),
            "food_glow": (255, 151, 121),
            "bonus": (255, 225, 120),
            "bonus_glow": (255, 236, 162),
            "obstacle": (86, 120, 112),
            "obstacle_shade": (54, 80, 75),
            "panel_top": (25, 51, 45),
            "panel_bottom": (14, 31, 28),
            "panel_border": (82, 128, 113),
            "control_top": (20, 45, 38),
            "control_bottom": (13, 30, 27),
            "control_border": (67, 110, 101),
            "death_flash": (181, 53, 53),
        },
    },
    {
        "name": "Sunset Alloy",
        "colors": {
            "text": (245, 235, 226),
            "text_muted": (204, 180, 160),
            "accent": (255, 166, 109),
            "bg_top": (30, 17, 20),
            "bg_bottom": (44, 29, 34),
            "board_top": (43, 28, 33),
            "board_bottom": (29, 18, 22),
            "grid": (92, 67, 74),
            "snake_head": (255, 209, 145),
            "snake_body": (240, 156, 86),
            "snake_border": (143, 87, 46),
            "food": (255, 104, 112),
            "food_glow": (255, 132, 138),
            "bonus": (255, 220, 136),
            "bonus_glow": (255, 233, 179),
            "obstacle": (133, 103, 111),
            "obstacle_shade": (87, 63, 70),
            "panel_top": (64, 41, 47),
            "panel_bottom": (43, 28, 33),
            "panel_border": (138, 102, 111),
            "control_top": (55, 34, 40),
            "control_bottom": (37, 23, 27),
            "control_border": (115, 85, 94),
            "death_flash": (201, 53, 69),
        },
    },
)

ACHIEVEMENT_DEFS: tuple[dict[str, str], ...] = (
    {
        "id": "first_bite",
        "title": "First Bite",
        "description": "Eat your first food.",
    },
    {
        "id": "score_hunter",
        "title": "Score Hunter",
        "description": "Reach score 30 in any run.",
    },
    {
        "id": "long_body",
        "title": "Long Body",
        "description": "Reach snake length 20.",
    },
    {
        "id": "grinder",
        "title": "Grinder",
        "description": "Accumulate total score 300.",
    },
    {
        "id": "veteran",
        "title": "Veteran",
        "description": "Play 20 games.",
    },
)


@dataclass
class UserSettings:
    difficulty_index: int = 1
    wrap_walls: bool = False
    obstacles_mode: bool = False
    theme_index: int = 0
    muted: bool = False
    volume: float = 0.45


class SoundManager:
    def __init__(self, volume: float, muted: bool) -> None:
        self.available = False
        self.muted = muted
        self.volume = max(0.0, min(1.0, volume))
        self.sounds: dict[str, pygame.mixer.Sound] = {}

        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.available = True
            self._build_sounds()
            self.set_volume(self.volume)
        except pygame.error:
            self.available = False

    def _build_sounds(self) -> None:
        self.sounds = {
            "menu": self._synth_tone(410, 60, 0.38),
            "toggle": self._synth_tone(520, 90, 0.35),
            "start": self._synth_tone(620, 120, 0.40),
            "eat": self._synth_tone(700, 65, 0.35),
            "bonus": self._synth_chord((740, 920), 130, 0.34),
            "death": self._synth_tone(180, 240, 0.42, wave="triangle"),
            "achievement": self._synth_chord((520, 780, 1040), 150, 0.30),
        }

    def _synth_tone(self, freq: float, duration_ms: int, amplitude: float, wave: str = "sine") -> pygame.mixer.Sound:
        sample_rate = 22050
        sample_count = max(1, int(sample_rate * duration_ms / 1000))
        values = array("h")

        for i in range(sample_count):
            t = i / sample_rate
            if wave == "triangle":
                cycle = (t * freq) % 1.0
                sample = (4.0 * cycle - 1.0) if cycle < 0.5 else (-4.0 * cycle + 3.0)
            elif wave == "square":
                sample = 1.0 if math.sin(2.0 * math.pi * freq * t) >= 0.0 else -1.0
            else:
                sample = math.sin(2.0 * math.pi * freq * t)

            attack = min(1.0, i / max(1.0, sample_count * 0.08))
            release = min(1.0, (sample_count - i) / max(1.0, sample_count * 0.2))
            envelope = min(attack, release)
            value = int(32767 * amplitude * envelope * sample)
            values.append(value)

        return pygame.mixer.Sound(buffer=values.tobytes())

    def _synth_chord(self, freqs: tuple[float, ...], duration_ms: int, amplitude: float) -> pygame.mixer.Sound:
        sample_rate = 22050
        sample_count = max(1, int(sample_rate * duration_ms / 1000))
        values = array("h")

        for i in range(sample_count):
            t = i / sample_rate
            sample = 0.0
            for freq in freqs:
                sample += math.sin(2.0 * math.pi * freq * t)
            sample /= max(1, len(freqs))

            attack = min(1.0, i / max(1.0, sample_count * 0.06))
            release = min(1.0, (sample_count - i) / max(1.0, sample_count * 0.2))
            envelope = min(attack, release)
            value = int(32767 * amplitude * envelope * sample)
            values.append(value)

        return pygame.mixer.Sound(buffer=values.tobytes())

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))
        if not self.available:
            return

        for sound in self.sounds.values():
            sound.set_volume(self.volume)

    def set_muted(self, muted: bool) -> None:
        self.muted = muted

    def play(self, name: str) -> None:
        if not self.available or self.muted:
            return
        sound = self.sounds.get(name)
        if sound is not None:
            sound.play()

def clamp_int(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def clamp_float(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def default_stats() -> dict[str, Any]:
    return {
        "games_played": 0,
        "total_score": 0,
        "total_foods": 0,
        "best_score": 0,
        "longest_snake": 0,
        "achievements": [],
    }


def load_json_file(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}


def save_json_file(path: Path, data: dict[str, Any]) -> None:
    try:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError:
        pass


def load_settings() -> UserSettings:
    data = load_json_file(SETTINGS_PATH)
    return UserSettings(
        difficulty_index=clamp_int(int(data.get("difficulty_index", 1)), 0, len(DIFFICULTIES) - 1),
        wrap_walls=bool(data.get("wrap_walls", False)),
        obstacles_mode=bool(data.get("obstacles_mode", False)),
        theme_index=clamp_int(int(data.get("theme_index", 0)), 0, len(THEMES) - 1),
        muted=bool(data.get("muted", False)),
        volume=clamp_float(float(data.get("volume", 0.45)), 0.0, 1.0),
    )


def save_settings(settings: UserSettings) -> None:
    save_json_file(SETTINGS_PATH, asdict(settings))


def load_stats() -> dict[str, Any]:
    loaded = load_json_file(STATS_PATH)
    defaults = default_stats()

    stats = {
        "games_played": int(loaded.get("games_played", defaults["games_played"])),
        "total_score": int(loaded.get("total_score", defaults["total_score"])),
        "total_foods": int(loaded.get("total_foods", defaults["total_foods"])),
        "best_score": int(loaded.get("best_score", defaults["best_score"])),
        "longest_snake": int(loaded.get("longest_snake", defaults["longest_snake"])),
        "achievements": list(loaded.get("achievements", defaults["achievements"])),
    }

    stats["games_played"] = max(0, stats["games_played"])
    stats["total_score"] = max(0, stats["total_score"])
    stats["total_foods"] = max(0, stats["total_foods"])
    stats["best_score"] = max(0, stats["best_score"])
    stats["longest_snake"] = max(0, stats["longest_snake"])

    valid_ids = {item["id"] for item in ACHIEVEMENT_DEFS}
    stats["achievements"] = [aid for aid in stats["achievements"] if aid in valid_ids]

    return stats


def save_stats(stats: dict[str, Any]) -> None:
    save_json_file(STATS_PATH, stats)


def achievement_title(achievement_id: str) -> str:
    for item in ACHIEVEMENT_DEFS:
        if item["id"] == achievement_id:
            return item["title"]
    return achievement_id


def unlock_achievements(stats: dict[str, Any]) -> list[str]:
    unlocked = set(stats.get("achievements", []))
    newly_unlocked: list[str] = []

    def unlock(achievement_id: str) -> None:
        if achievement_id in unlocked:
            return
        unlocked.add(achievement_id)
        newly_unlocked.append(achievement_title(achievement_id))

    if stats["total_foods"] >= 1:
        unlock("first_bite")
    if stats["best_score"] >= 30:
        unlock("score_hunter")
    if stats["longest_snake"] >= 20:
        unlock("long_body")
    if stats["total_score"] >= 300:
        unlock("grinder")
    if stats["games_played"] >= 20:
        unlock("veteran")

    stats["achievements"] = sorted(unlocked)
    return newly_unlocked


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
        pass


def theme_colors(settings: UserSettings) -> dict[str, tuple[int, int, int]]:
    return THEMES[settings.theme_index]["colors"]


def theme_name(settings: UserSettings) -> str:
    return THEMES[settings.theme_index]["name"]


def lerp_color(color_a: tuple[int, int, int], color_b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = clamp_float(t, 0.0, 1.0)
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
    text_color: tuple[int, int, int],
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
    text_color: tuple[int, int, int],
    text_muted: tuple[int, int, int],
) -> int:
    key_label = font.render(key_text, True, text_color)
    key_rect = pygame.Rect(x, y, key_label.get_width() + 14, key_label.get_height() + 8)
    pygame.draw.rect(surface, (39, 58, 82), key_rect, border_radius=8)
    pygame.draw.rect(surface, (102, 131, 167), key_rect, 1, border_radius=8)
    surface.blit(key_label, (key_rect.x + 7, key_rect.y + 4))

    text_label = font.render(label_text, True, text_muted)
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


def build_background(width_px: int, height_px: int, colors: dict[str, tuple[int, int, int]]) -> pygame.Surface:
    background = pygame.Surface((width_px, height_px)).convert()
    draw_vertical_gradient(background, pygame.Rect(0, 0, width_px, height_px), colors["bg_top"], colors["bg_bottom"])

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


def build_state(settings: UserSettings) -> GameState:
    difficulty = DIFFICULTIES[settings.difficulty_index]
    return initial_state(
        width=GRID_WIDTH,
        height=GRID_HEIGHT,
        start_length=3,
        base_tick_ms=difficulty["base_tick_ms"],
        min_tick_ms=difficulty["min_tick_ms"],
        speed_step_ms=difficulty["speed_step_ms"],
        speed_every_points=difficulty["speed_every_points"],
        wrap_walls=settings.wrap_walls,
        obstacle_count=OBSTACLE_COUNT if settings.obstacles_mode else 0,
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

def draw_toasts(
    surface: pygame.Surface,
    font: pygame.font.Font,
    toasts: list[dict[str, float | str]],
    colors: dict[str, tuple[int, int, int]],
) -> None:
    if not toasts:
        return

    x = surface.get_width() - 300
    y = 14
    for toast in toasts:
        duration = float(toast["duration"])
        remaining = max(0.0, float(toast["ms"]))
        progress = 1.0 - (remaining / duration)
        alpha_mul = 1.0
        if progress < 0.15:
            alpha_mul = progress / 0.15
        elif progress > 0.85:
            alpha_mul = max(0.0, (1.0 - progress) / 0.15)

        toast_surface = pygame.Surface((280, 40), pygame.SRCALPHA)
        fill = (*colors["panel_top"], int(220 * alpha_mul))
        border = (*colors["accent"], int(220 * alpha_mul))
        pygame.draw.rect(toast_surface, fill, pygame.Rect(0, 0, 280, 40), border_radius=10)
        pygame.draw.rect(toast_surface, border, pygame.Rect(0, 0, 280, 40), 1, border_radius=10)

        label = font.render(str(toast["text"]), True, colors["text"])
        toast_surface.blit(label, (10, 10))

        surface.blit(toast_surface, (x, y))
        y += 46


def draw_menu(
    surface: pygame.Surface,
    background: pygame.Surface,
    title_font: pygame.font.Font,
    ui_font: pygame.font.Font,
    small_font: pygame.font.Font,
    settings: UserSettings,
    high_score: int,
    stats: dict[str, Any],
    toasts: list[dict[str, float | str]],
    time_seconds: float,
) -> None:
    colors = theme_colors(settings)
    surface.blit(background, (0, 0))

    card_rect = pygame.Rect(40, 38, surface.get_width() - 80, surface.get_height() - 76)
    draw_panel(surface, card_rect, colors["panel_top"], colors["panel_bottom"], colors["panel_border"], radius=18)

    title_offset = int(math.sin(time_seconds * 2.3) * 3)
    title_label = title_font.render("SNAKE", True, colors["text"])
    subtitle_label = small_font.render("Premium V3", True, colors["text_muted"])
    surface.blit(title_label, (card_rect.x + 26, card_rect.y + 20 + title_offset))
    surface.blit(subtitle_label, (card_rect.x + 30, card_rect.y + 72 + title_offset))

    draw_chip(
        surface,
        small_font,
        f"High Score {high_score}",
        card_rect.right - 188,
        card_rect.y + 30,
        colors["control_top"],
        colors["panel_border"],
        colors["text"],
    )

    left_col_w = card_rect.width - 270
    options_start_y = card_rect.y + 118

    for idx, difficulty in enumerate(DIFFICULTIES):
        option_rect = pygame.Rect(card_rect.x + 24, options_start_y + idx * 50, left_col_w - 36, 40)
        selected = idx == settings.difficulty_index

        fill_top = lerp_color(colors["panel_top"], colors["accent"], 0.32 if selected else 0.05)
        fill_bottom = lerp_color(colors["panel_bottom"], colors["accent"], 0.22 if selected else 0.0)
        border = colors["accent"] if selected else colors["panel_border"]

        draw_panel(surface, option_rect, fill_top, fill_bottom, border, radius=12)
        surface.blit(ui_font.render(f"{idx + 1}. {difficulty['name']}", True, colors["text"]), (option_rect.x + 12, option_rect.y + 6))
        speed_text = small_font.render(f"{difficulty['base_tick_ms']}ms", True, colors["text_muted"])
        surface.blit(speed_text, (option_rect.right - speed_text.get_width() - 12, option_rect.y + 10))

    toggle_y = options_start_y + (len(DIFFICULTIES) * 50) + 6
    draw_chip(
        surface,
        small_font,
        f"W Wrap {'ON' if settings.wrap_walls else 'OFF'}",
        card_rect.x + 24,
        toggle_y,
        colors["control_top"],
        colors["panel_border"],
        colors["text"],
    )
    draw_chip(
        surface,
        small_font,
        f"O Obstacles {'ON' if settings.obstacles_mode else 'OFF'}",
        card_rect.x + 200,
        toggle_y,
        colors["control_top"],
        colors["panel_border"],
        colors["text"],
    )

    draw_chip(
        surface,
        small_font,
        f"T Theme: {theme_name(settings)}",
        card_rect.x + 24,
        toggle_y + 42,
        colors["control_top"],
        colors["panel_border"],
        colors["text"],
    )
    volume_pct = int(settings.volume * 100)
    draw_chip(
        surface,
        small_font,
        f"X Audio {'Muted' if settings.muted else f'{volume_pct}%'}",
        card_rect.x + 290,
        toggle_y + 42,
        colors["control_top"],
        colors["panel_border"],
        colors["text"],
    )

    side_rect = pygame.Rect(card_rect.right - 230, card_rect.y + 116, 206, card_rect.height - 142)
    draw_panel(
        surface,
        side_rect,
        colors["control_top"],
        colors["control_bottom"],
        colors["control_border"],
        radius=12,
    )

    stats_title = ui_font.render("Stats", True, colors["text"])
    surface.blit(stats_title, (side_rect.x + 12, side_rect.y + 10))

    stat_lines = [
        f"Games: {stats['games_played']}",
        f"Total Score: {stats['total_score']}",
        f"Total Foods: {stats['total_foods']}",
        f"Longest Snake: {stats['longest_snake']}",
        f"Achievements: {len(stats['achievements'])}/{len(ACHIEVEMENT_DEFS)}",
    ]

    sy = side_rect.y + 48
    for line in stat_lines:
        surface.blit(small_font.render(line, True, colors["text_muted"]), (side_rect.x + 12, sy))
        sy += 24

    surface.blit(small_font.render("Recent unlocks", True, colors["text"]), (side_rect.x + 12, sy + 8))
    sy += 34

    unlocked_titles = [achievement_title(aid) for aid in stats.get("achievements", [])]
    recent = unlocked_titles[-4:] if unlocked_titles else []
    if recent:
        for title in recent:
            line = ellipsize_text(small_font, f"- {title}", side_rect.width - 24)
            surface.blit(small_font.render(line, True, colors["text_muted"]), (side_rect.x + 12, sy))
            sy += 22
    else:
        surface.blit(small_font.render("- None yet", True, colors["text_muted"]), (side_rect.x + 12, sy))

    helper_lines = [
        "Up/Down or 1/2/3: Difficulty",
        "W: Wrap  O: Obstacles  T: Theme",
        "X: Mute  -/=: Volume  Enter: Start  Esc: Quit",
    ]

    helper_y = card_rect.bottom - 88
    for i, line in enumerate(helper_lines):
        surface.blit(small_font.render(line, True, colors["text_muted"]), (card_rect.x + 24, helper_y + i * 24))

    draw_toasts(surface, small_font, toasts, colors)


def draw_game_overlay(
    surface: pygame.Surface,
    board_rect: pygame.Rect,
    ui_font: pygame.font.Font,
    small_font: pygame.font.Font,
    settings: UserSettings,
    state: GameState,
    high_score: int,
) -> None:
    colors = theme_colors(settings)
    dim_surface = pygame.Surface((board_rect.width, board_rect.height), pygame.SRCALPHA)
    dim_surface.fill((2, 6, 10, 150))
    surface.blit(dim_surface, board_rect.topleft)

    if state.status == STATUS_PAUSED:
        box_rect = pygame.Rect(0, 0, board_rect.width - 140, 128)
        box_rect.center = board_rect.center
        draw_panel(surface, box_rect, colors["panel_top"], colors["panel_bottom"], colors["panel_border"], radius=14)

        title_label = ui_font.render("Paused", True, colors["text"])
        subtitle_label = small_font.render("Press P to resume", True, colors["text_muted"])
        surface.blit(title_label, title_label.get_rect(center=(box_rect.centerx, box_rect.y + 38)))
        surface.blit(subtitle_label, subtitle_label.get_rect(center=(box_rect.centerx, box_rect.y + 76)))
        draw_key_hint(surface, small_font, "P", "Resume", box_rect.centerx - 44, box_rect.y + 90, colors["text"], colors["text_muted"])
        return

    box_rect = pygame.Rect(0, 0, board_rect.width - 86, 206)
    box_rect.center = board_rect.center
    draw_panel(surface, box_rect, colors["panel_top"], colors["panel_bottom"], colors["panel_border"], radius=14)

    title_label = ui_font.render("Game Over", True, colors["text"])
    surface.blit(title_label, title_label.get_rect(center=(box_rect.centerx, box_rect.y + 34)))

    summary_1 = small_font.render(f"Score {state.score}   High {high_score}", True, colors["text"])
    summary_2 = small_font.render(
        f"Foods {state.foods_eaten}   Speed {current_tick_ms(state)}ms",
        True,
        colors["text_muted"],
    )
    mode_text = (
        f"{DIFFICULTIES[settings.difficulty_index]['name']} | "
        f"{'Wrap ON' if state.wrap_walls else 'Wrap OFF'} | "
        f"{'Obstacles ON' if state.obstacle_count > 0 else 'Obstacles OFF'}"
    )
    summary_3 = small_font.render(mode_text, True, colors["text_muted"])

    surface.blit(summary_1, summary_1.get_rect(center=(box_rect.centerx, box_rect.y + 80)))
    surface.blit(summary_2, summary_2.get_rect(center=(box_rect.centerx, box_rect.y + 108)))
    surface.blit(summary_3, summary_3.get_rect(center=(box_rect.centerx, box_rect.y + 132)))

    draw_key_hint(surface, small_font, "R", "Retry", box_rect.x + 84, box_rect.y + 156, colors["text"], colors["text_muted"])
    draw_key_hint(surface, small_font, "M", "Menu", box_rect.x + 214, box_rect.y + 156, colors["text"], colors["text_muted"])

def draw_board(
    surface: pygame.Surface,
    background: pygame.Surface,
    settings: UserSettings,
    state: GameState,
    snake_positions: list[tuple[float, float]],
    ui_font: pygame.font.Font,
    small_font: pygame.font.Font,
    high_score: int,
    time_seconds: float,
    food_pops: list[dict[str, float]],
    score_pulse_ratio: float,
    shake_offset: tuple[int, int],
    toasts: list[dict[str, float | str]],
) -> None:
    colors = theme_colors(settings)
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

    draw_panel(surface, hud_rect, colors["panel_top"], colors["panel_bottom"], colors["panel_border"], radius=14)
    draw_panel(surface, board_outer, colors["panel_top"], colors["panel_bottom"], colors["panel_border"], radius=12)
    draw_panel(surface, controls_rect, colors["control_top"], colors["control_bottom"], colors["control_border"], radius=12)

    board_surface = pygame.Surface((board_rect.width, board_rect.height)).convert()
    draw_vertical_gradient(
        board_surface,
        pygame.Rect(0, 0, board_rect.width, board_rect.height),
        colors["board_top"],
        colors["board_bottom"],
    )

    for y in range(state.height):
        row_tint = 8 if y % 2 == 0 else 0
        base = colors["board_top"]
        row_color = (
            clamp_int(base[0] + row_tint, 0, 255),
            clamp_int(base[1] + row_tint, 0, 255),
            clamp_int(base[2] + row_tint, 0, 255),
        )
        row_rect = pygame.Rect(0, y * CELL_SIZE, board_rect.width, CELL_SIZE)
        pygame.draw.rect(board_surface, row_color, row_rect, 0)

    for x in range(state.width + 1):
        px = x * CELL_SIZE
        pygame.draw.line(board_surface, colors["grid"], (px, 0), (px, board_rect.height), 1)
    for y in range(state.height + 1):
        py = y * CELL_SIZE
        pygame.draw.line(board_surface, colors["grid"], (0, py), (board_rect.width, py), 1)

    surface.blit(board_surface, board_rect.topleft)

    for obstacle_x, obstacle_y in state.obstacles:
        rect = cell_rect(board_rect, float(obstacle_x), float(obstacle_y), inset=3)
        pygame.draw.rect(surface, colors["obstacle_shade"], rect, border_radius=6)
        top_half = pygame.Rect(rect.x + 1, rect.y + 1, rect.width - 2, rect.height // 2)
        pygame.draw.rect(surface, colors["obstacle"], top_half, border_radius=6)
        pygame.draw.rect(surface, colors["grid"], rect, 1, border_radius=6)

    for idx, (snake_x, snake_y) in enumerate(snake_positions):
        rect = cell_rect(board_rect, snake_x, snake_y, inset=2)
        fill_color = colors["snake_head"] if idx == 0 else colors["snake_body"]
        pygame.draw.rect(surface, fill_color, rect, border_radius=8)
        pygame.draw.rect(surface, colors["snake_border"], rect, 1, border_radius=8)

        highlight = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, max(3, rect.height // 3))
        pygame.draw.rect(surface, (210, 245, 214, 95), highlight, border_radius=7)

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
        draw_glow(surface, food_center, colors["food_glow"], 18 + int(food_pulse * 2), 95)
        pygame.draw.circle(surface, colors["food"], food_center, 6 + int(food_pulse * 1.8))
        pygame.draw.circle(surface, (255, 186, 173), (food_center[0] - 2, food_center[1] - 2), 2)

    if state.bonus_food is not None:
        bonus_center = (
            board_rect.x + state.bonus_food[0] * CELL_SIZE + CELL_SIZE // 2,
            board_rect.y + state.bonus_food[1] * CELL_SIZE + CELL_SIZE // 2,
        )
        bonus_pulse = 0.5 + 0.5 * math.sin(time_seconds * 6.0)
        radius = 8 + int(bonus_pulse * 2)
        draw_glow(surface, bonus_center, colors["bonus_glow"], 24 + int(bonus_pulse * 2), 128)
        diamond = [
            (bonus_center[0], bonus_center[1] - radius),
            (bonus_center[0] + radius, bonus_center[1]),
            (bonus_center[0], bonus_center[1] + radius),
            (bonus_center[0] - radius, bonus_center[1]),
        ]
        pygame.draw.polygon(surface, colors["bonus"], diamond)
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
        glow_color = colors["bonus_glow"] if effect["bonus"] > 0 else colors["food_glow"]
        ring_radius = 8 + int(progress * 18)
        alpha = int((1.0 - progress) * 165)

        ring_surface = pygame.Surface((ring_radius * 2, ring_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            ring_surface,
            (glow_color[0], glow_color[1], glow_color[2], alpha),
            (ring_radius, ring_radius),
            ring_radius,
            2,
        )
        surface.blit(ring_surface, (center[0] - ring_radius, center[1] - ring_radius))

    score_fill = lerp_color(colors["control_top"], colors["accent"], score_pulse_ratio * 0.5)
    score_border = lerp_color(colors["panel_border"], colors["accent"], score_pulse_ratio)

    draw_chip(surface, small_font, f"Score {state.score}", hud_rect.x + 12, hud_rect.y + 10, score_fill, score_border, colors["text"])
    chip_x = draw_chip(
        surface,
        small_font,
        f"High {high_score}",
        hud_rect.x + 116,
        hud_rect.y + 10,
        colors["control_top"],
        colors["panel_border"],
        colors["text"],
    )
    chip_x = draw_chip(
        surface,
        small_font,
        DIFFICULTIES[settings.difficulty_index]["name"],
        chip_x,
        hud_rect.y + 10,
        lerp_color(colors["control_top"], colors["accent"], 0.3),
        colors["accent"],
        colors["text"],
    )

    wrap_text_value = "Wrap ON" if state.wrap_walls else "Wrap OFF"
    obstacle_text_value = "Obstacles ON" if state.obstacle_count > 0 else "Obstacles OFF"
    bonus_text_value = f"Bonus {state.bonus_timer_ticks}" if state.bonus_food is not None else "Bonus -"

    draw_chip(surface, small_font, wrap_text_value, chip_x, hud_rect.y + 10, colors["control_top"], colors["panel_border"], colors["text"])
    draw_chip(surface, small_font, obstacle_text_value, hud_rect.x + 12, hud_rect.y + 42, colors["control_top"], colors["panel_border"], colors["text"])
    draw_chip(
        surface,
        small_font,
        f"Speed {current_tick_ms(state)}ms",
        hud_rect.x + 160,
        hud_rect.y + 42,
        colors["control_top"],
        colors["panel_border"],
        colors["text"],
    )
    draw_chip(surface, small_font, bonus_text_value, hud_rect.x + 312, hud_rect.y + 42, colors["control_top"], colors["panel_border"], colors["text"])

    controls_text = "Arrows/WASD move  P pause  R restart  M menu  T theme  X mute  -/= volume  Esc quit"
    max_controls_width = controls_rect.width - 24
    control_lines = wrap_text(small_font, controls_text, max_controls_width)
    if len(control_lines) > 2:
        control_lines = [control_lines[0], ellipsize_text(small_font, " ".join(control_lines[1:]), max_controls_width)]

    for idx, line in enumerate(control_lines):
        label = small_font.render(line, True, colors["text_muted"])
        surface.blit(label, (controls_rect.x + 12, controls_rect.y + 8 + idx * 22))

    if state.status in (STATUS_PAUSED, STATUS_GAME_OVER):
        draw_game_overlay(surface, board_rect, ui_font, small_font, settings, state, high_score)

    draw_toasts(surface, small_font, toasts, colors)

def main() -> None:
    pygame.mixer.pre_init(22050, -16, 1, 512)
    pygame.init()
    pygame.display.set_caption("Snake")

    width_px = BOARD_PIXEL_W + (WINDOW_PADDING * 2)
    height_px = TOP_BAR + BOARD_PIXEL_H + CONTROL_AREA_HEIGHT + WINDOW_PADDING

    screen = pygame.display.set_mode((width_px, height_px))
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("segoeui", 52, bold=True)
    ui_font = pygame.font.SysFont("segoeui", 24, bold=True)
    small_font = pygame.font.SysFont("segoeui", 18)

    settings = load_settings()
    stats = load_stats()

    high_score = max(load_high_score(), int(stats.get("best_score", 0)))
    if high_score > int(stats.get("best_score", 0)):
        stats["best_score"] = high_score
        save_stats(stats)

    sounds = SoundManager(volume=settings.volume, muted=settings.muted)

    background_cache: dict[int, pygame.Surface] = {}

    def get_background(theme_idx: int) -> pygame.Surface:
        if theme_idx not in background_cache:
            background_cache[theme_idx] = build_background(width_px, height_px, THEMES[theme_idx]["colors"])
        return background_cache[theme_idx]

    screen_mode = "menu"
    state: GameState | None = None
    previous_state_for_render: GameState | None = None
    elapsed_ms = 0.0

    game_over_recorded = False
    score_pulse_ms = 0.0
    death_flash_ms = 0.0
    shake_ms = 0.0

    food_pops: list[dict[str, float]] = []
    toasts: list[dict[str, float | str]] = []

    while True:
        frame_ms = float(clock.tick(FPS))
        time_seconds = pygame.time.get_ticks() / 1000.0

        score_pulse_ms = max(0.0, score_pulse_ms - frame_ms)
        death_flash_ms = max(0.0, death_flash_ms - frame_ms)
        shake_ms = max(0.0, shake_ms - frame_ms)

        for effect in food_pops:
            effect["ms"] -= frame_ms
        food_pops = [effect for effect in food_pops if effect["ms"] > 0.0]

        for toast in toasts:
            toast["ms"] = float(toast["ms"]) - frame_ms
        toasts = [toast for toast in toasts if float(toast["ms"]) > 0.0]

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

            if event.key == pygame.K_t:
                settings.theme_index = (settings.theme_index + 1) % len(THEMES)
                save_settings(settings)
                sounds.play("toggle")

            if event.key == pygame.K_x:
                settings.muted = not settings.muted
                sounds.set_muted(settings.muted)
                save_settings(settings)
                sounds.play("toggle")

            if event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                settings.volume = clamp_float(settings.volume - 0.05, 0.0, 1.0)
                sounds.set_volume(settings.volume)
                save_settings(settings)
                sounds.play("toggle")

            if event.key in (pygame.K_EQUALS, pygame.K_KP_PLUS):
                settings.volume = clamp_float(settings.volume + 0.05, 0.0, 1.0)
                sounds.set_volume(settings.volume)
                save_settings(settings)
                sounds.play("toggle")

            if screen_mode == "menu":
                if event.key == pygame.K_UP:
                    settings.difficulty_index = (settings.difficulty_index - 1) % len(DIFFICULTIES)
                    save_settings(settings)
                    sounds.play("menu")
                elif event.key == pygame.K_DOWN:
                    settings.difficulty_index = (settings.difficulty_index + 1) % len(DIFFICULTIES)
                    save_settings(settings)
                    sounds.play("menu")
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    settings.difficulty_index = min(len(DIFFICULTIES) - 1, event.key - pygame.K_1)
                    save_settings(settings)
                    sounds.play("menu")
                elif event.key == pygame.K_w:
                    settings.wrap_walls = not settings.wrap_walls
                    save_settings(settings)
                    sounds.play("toggle")
                elif event.key == pygame.K_o:
                    settings.obstacles_mode = not settings.obstacles_mode
                    save_settings(settings)
                    sounds.play("toggle")
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    state = build_state(settings)
                    previous_state_for_render = None
                    screen_mode = "playing"
                    elapsed_ms = 0.0
                    game_over_recorded = False
                    food_pops = []
                    score_pulse_ms = 0.0
                    death_flash_ms = 0.0
                    shake_ms = 0.0
                    sounds.play("start")
            elif state is not None:
                if event.key == pygame.K_m:
                    screen_mode = "menu"
                    state = None
                    previous_state_for_render = None
                    elapsed_ms = 0.0
                    sounds.play("menu")
                elif event.key == pygame.K_r:
                    state = restart(state)
                    previous_state_for_render = None
                    elapsed_ms = 0.0
                    game_over_recorded = False
                    food_pops = []
                    score_pulse_ms = 0.0
                    death_flash_ms = 0.0
                    shake_ms = 0.0
                    sounds.play("start")
                elif event.key == pygame.K_p:
                    if state.status == STATUS_RUNNING:
                        state = replace(state, status=STATUS_PAUSED)
                        sounds.play("menu")
                    elif state.status == STATUS_PAUSED:
                        state = replace(state, status=STATUS_RUNNING)
                        sounds.play("menu")
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
                    sounds.play("bonus" if ate_bonus else "eat")

                if before_tick.status == STATUS_RUNNING and after_tick.status == STATUS_GAME_OVER:
                    shake_ms = 260.0
                    death_flash_ms = 220.0
                    sounds.play("death")

                state = after_tick

            if state.status == STATUS_GAME_OVER and not game_over_recorded:
                game_over_recorded = True

                stats["games_played"] = int(stats.get("games_played", 0)) + 1
                stats["total_score"] = int(stats.get("total_score", 0)) + state.score
                stats["total_foods"] = int(stats.get("total_foods", 0)) + state.foods_eaten
                stats["best_score"] = max(int(stats.get("best_score", 0)), state.score)
                stats["longest_snake"] = max(int(stats.get("longest_snake", 0)), len(state.snake))

                new_achievements = unlock_achievements(stats)
                save_stats(stats)

                if state.score > high_score:
                    high_score = state.score
                    save_high_score(high_score)

                for title in new_achievements:
                    toasts.append({"text": f"Achievement Unlocked: {title}", "ms": 2600.0, "duration": 2600.0})
                    sounds.play("achievement")

            if state.status == STATUS_RUNNING and previous_state_for_render is not None:
                tick_window = max(1.0, float(current_tick_ms(state)))
                interpolation_alpha = clamp_float(elapsed_ms / tick_window, 0.0, 1.0)
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

            draw_board(
                surface=screen,
                background=get_background(settings.theme_index),
                settings=settings,
                state=state,
                snake_positions=snake_positions,
                ui_font=ui_font,
                small_font=small_font,
                high_score=high_score,
                time_seconds=time_seconds,
                food_pops=food_pops,
                score_pulse_ratio=clamp_float(score_pulse_ms / 220.0, 0.0, 1.0),
                shake_offset=shake_offset,
                toasts=toasts,
            )

            if death_flash_ms > 0.0:
                colors = theme_colors(settings)
                flash_alpha = int(140 * (death_flash_ms / 220.0))
                flash_surface = pygame.Surface((width_px, height_px), pygame.SRCALPHA)
                flash_surface.fill((colors["death_flash"][0], colors["death_flash"][1], colors["death_flash"][2], flash_alpha))
                screen.blit(flash_surface, (0, 0))
        else:
            draw_menu(
                surface=screen,
                background=get_background(settings.theme_index),
                title_font=title_font,
                ui_font=ui_font,
                small_font=small_font,
                settings=settings,
                high_score=high_score,
                stats=stats,
                toasts=toasts,
                time_seconds=time_seconds,
            )

        pygame.display.flip()


if __name__ == "__main__":
    main()


"""Snake package exposing pure game logic."""

from .game_logic import (
    CellSelector,
    Direction,
    FoodSelector,
    GameState,
    Point,
    STATUS_GAME_OVER,
    STATUS_PAUSED,
    STATUS_RUNNING,
    current_tick_ms,
    initial_state,
    restart,
    set_direction,
    tick,
)

__all__ = [
    "CellSelector",
    "Direction",
    "FoodSelector",
    "GameState",
    "Point",
    "STATUS_GAME_OVER",
    "STATUS_PAUSED",
    "STATUS_RUNNING",
    "current_tick_ms",
    "initial_state",
    "restart",
    "set_direction",
    "tick",
]
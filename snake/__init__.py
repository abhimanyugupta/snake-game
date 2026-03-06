"""Snake package exposing pure game logic."""

from .game_logic import (
    Direction,
    FoodSelector,
    GameState,
    Point,
    initial_state,
    restart,
    set_direction,
    tick,
)

__all__ = [
    "Direction",
    "FoodSelector",
    "GameState",
    "Point",
    "initial_state",
    "restart",
    "set_direction",
    "tick",
]
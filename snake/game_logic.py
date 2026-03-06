"""Pure, deterministic Snake game logic."""

from __future__ import annotations

from dataclasses import dataclass, replace
import random
from typing import Callable, Optional, Sequence, Tuple

Point = Tuple[int, int]
Direction = Tuple[int, int]
FoodSelector = Callable[[Sequence[Point]], Point]

STATUS_RUNNING = "running"
STATUS_PAUSED = "paused"
STATUS_GAME_OVER = "game_over"


@dataclass(frozen=True)
class GameState:
    width: int
    height: int
    snake: Tuple[Point, ...]
    direction: Direction
    food: Optional[Point]
    score: int
    pending_growth: int
    status: str
    start_length: int
    tick_ms: int


def initial_state(
    width: int = 20,
    height: int = 20,
    start_length: int = 3,
    tick_ms: int = 120,
    start_direction: Direction = (1, 0),
    food_selector: Optional[FoodSelector] = None,
    rng: Optional[random.Random] = None,
) -> GameState:
    if width < 2 or height < 2:
        raise ValueError("width and height must both be at least 2")
    if start_length < 2:
        raise ValueError("start_length must be at least 2")
    if start_length > width:
        raise ValueError("start_length cannot exceed board width")

    cx = width // 2
    cy = height // 2

    if cx - (start_length - 1) < 0:
        raise ValueError("start snake does not fit inside board")

    snake = tuple((cx - i, cy) for i in range(start_length))
    food = _spawn_food(width, height, snake, food_selector, rng)

    return GameState(
        width=width,
        height=height,
        snake=snake,
        direction=start_direction,
        food=food,
        score=0,
        pending_growth=0,
        status=STATUS_RUNNING,
        start_length=start_length,
        tick_ms=tick_ms,
    )


def set_direction(state: GameState, new_direction: Direction) -> GameState:
    if state.status != STATUS_RUNNING:
        return state

    if not _is_valid_direction(new_direction):
        return state

    if _is_opposite(state.direction, new_direction):
        return state

    return replace(state, direction=new_direction)


def tick(
    state: GameState,
    food_selector: Optional[FoodSelector] = None,
    rng: Optional[random.Random] = None,
) -> GameState:
    if state.status != STATUS_RUNNING:
        return state

    head_x, head_y = state.snake[0]
    dx, dy = state.direction
    next_head = (head_x + dx, head_y + dy)

    if not _is_inside(next_head, state.width, state.height):
        return replace(state, status=STATUS_GAME_OVER)

    ate_food = state.food is not None and next_head == state.food
    growth_budget = state.pending_growth + (1 if ate_food else 0)

    occupied = set(state.snake if growth_budget > 0 else state.snake[:-1])
    if next_head in occupied:
        return replace(state, status=STATUS_GAME_OVER)

    next_snake = (next_head,) + state.snake

    if growth_budget > 0:
        next_pending_growth = growth_budget - 1
    else:
        next_snake = next_snake[:-1]
        next_pending_growth = 0

    next_score = state.score + (1 if ate_food else 0)
    next_food = state.food
    next_status = state.status

    if ate_food:
        next_food = _spawn_food(state.width, state.height, next_snake, food_selector, rng)
        if next_food is None:
            next_status = STATUS_GAME_OVER

    return GameState(
        width=state.width,
        height=state.height,
        snake=next_snake,
        direction=state.direction,
        food=next_food,
        score=next_score,
        pending_growth=next_pending_growth,
        status=next_status,
        start_length=state.start_length,
        tick_ms=state.tick_ms,
    )


def restart(
    state: GameState,
    food_selector: Optional[FoodSelector] = None,
    rng: Optional[random.Random] = None,
) -> GameState:
    return initial_state(
        width=state.width,
        height=state.height,
        start_length=state.start_length,
        tick_ms=state.tick_ms,
        start_direction=(1, 0),
        food_selector=food_selector,
        rng=rng,
    )


def _is_valid_direction(direction: Direction) -> bool:
    return direction in {(1, 0), (-1, 0), (0, 1), (0, -1)}


def _is_opposite(current: Direction, proposed: Direction) -> bool:
    return current[0] == -proposed[0] and current[1] == -proposed[1]


def _is_inside(point: Point, width: int, height: int) -> bool:
    x, y = point
    return 0 <= x < width and 0 <= y < height


def _spawn_food(
    width: int,
    height: int,
    snake: Sequence[Point],
    food_selector: Optional[FoodSelector] = None,
    rng: Optional[random.Random] = None,
) -> Optional[Point]:
    occupied = set(snake)
    free_cells = [
        (x, y)
        for y in range(height)
        for x in range(width)
        if (x, y) not in occupied
    ]

    if not free_cells:
        return None

    if food_selector is not None:
        selected = food_selector(free_cells)
        if selected not in free_cells:
            raise ValueError("food_selector returned a cell that is not free")
        return selected

    chooser = rng.choice if rng is not None else random.choice
    return chooser(free_cells)
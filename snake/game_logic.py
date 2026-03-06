"""Pure, deterministic Snake game logic with optional advanced modes."""

from __future__ import annotations

from dataclasses import dataclass, replace
import random
from typing import Callable, Optional, Sequence, Tuple

Point = Tuple[int, int]
Direction = Tuple[int, int]
CellSelector = Callable[[Sequence[Point]], Point]
FoodSelector = CellSelector

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
    score: int = 0
    pending_growth: int = 0
    status: str = STATUS_RUNNING
    start_length: int = 3
    base_tick_ms: int = 120
    min_tick_ms: int = 60
    speed_step_ms: int = 5
    speed_every_points: int = 3
    wrap_walls: bool = False
    obstacles: Tuple[Point, ...] = ()
    obstacle_count: int = 0
    bonus_food: Optional[Point] = None
    bonus_timer_ticks: int = 0
    bonus_frequency: int = 5
    bonus_lifetime_ticks: int = 20
    bonus_points: int = 3
    foods_eaten: int = 0


def initial_state(
    width: int = 20,
    height: int = 20,
    start_length: int = 3,
    base_tick_ms: int = 120,
    min_tick_ms: int = 60,
    speed_step_ms: int = 5,
    speed_every_points: int = 3,
    start_direction: Direction = (1, 0),
    wrap_walls: bool = False,
    obstacle_count: int = 0,
    obstacles: Optional[Sequence[Point]] = None,
    bonus_frequency: int = 5,
    bonus_lifetime_ticks: int = 20,
    bonus_points: int = 3,
    food_selector: Optional[CellSelector] = None,
    obstacle_selector: Optional[CellSelector] = None,
    rng: Optional[random.Random] = None,
) -> GameState:
    if width < 2 or height < 2:
        raise ValueError("width and height must both be at least 2")
    if start_length < 2:
        raise ValueError("start_length must be at least 2")
    if start_length > width:
        raise ValueError("start_length cannot exceed board width")
    if base_tick_ms <= 0:
        raise ValueError("base_tick_ms must be positive")
    if min_tick_ms <= 0:
        raise ValueError("min_tick_ms must be positive")
    if min_tick_ms > base_tick_ms:
        raise ValueError("min_tick_ms cannot exceed base_tick_ms")
    if speed_step_ms < 0:
        raise ValueError("speed_step_ms cannot be negative")
    if bonus_frequency < 0:
        raise ValueError("bonus_frequency cannot be negative")
    if bonus_lifetime_ticks < 1:
        raise ValueError("bonus_lifetime_ticks must be at least 1")
    if bonus_points < 1:
        raise ValueError("bonus_points must be at least 1")

    cx = width // 2
    cy = height // 2

    if cx - (start_length - 1) < 0:
        raise ValueError("start snake does not fit inside board")

    snake = tuple((cx - i, cy) for i in range(start_length))

    if obstacles is not None:
        obstacle_cells = tuple(obstacles)
        _validate_obstacles(obstacle_cells, width, height, snake)
    else:
        obstacle_cells = _spawn_cells(
            width=width,
            height=height,
            occupied=snake,
            count=obstacle_count,
            cell_selector=obstacle_selector or food_selector,
            rng=rng,
        )

    food = _spawn_food(
        width=width,
        height=height,
        snake=snake,
        obstacles=obstacle_cells,
        bonus_food=None,
        food_selector=food_selector,
        rng=rng,
    )

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
        base_tick_ms=base_tick_ms,
        min_tick_ms=min_tick_ms,
        speed_step_ms=speed_step_ms,
        speed_every_points=speed_every_points,
        wrap_walls=wrap_walls,
        obstacles=obstacle_cells,
        obstacle_count=len(obstacle_cells),
        bonus_food=None,
        bonus_timer_ticks=0,
        bonus_frequency=bonus_frequency,
        bonus_lifetime_ticks=bonus_lifetime_ticks,
        bonus_points=bonus_points,
        foods_eaten=0,
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
    food_selector: Optional[CellSelector] = None,
    rng: Optional[random.Random] = None,
) -> GameState:
    if state.status != STATUS_RUNNING:
        return state

    next_head = _next_head(state)
    if next_head is None:
        return replace(state, status=STATUS_GAME_OVER)

    ate_food = state.food is not None and next_head == state.food
    ate_bonus = state.bonus_food is not None and next_head == state.bonus_food

    growth_budget = state.pending_growth + (1 if ate_food else 0) + (1 if ate_bonus else 0)
    occupied_snake = set(state.snake if growth_budget > 0 else state.snake[:-1])

    if next_head in occupied_snake or next_head in set(state.obstacles):
        return replace(state, status=STATUS_GAME_OVER)

    next_snake = (next_head,) + state.snake
    if growth_budget > 0:
        next_pending_growth = growth_budget - 1
    else:
        next_snake = next_snake[:-1]
        next_pending_growth = 0

    next_score = state.score + (1 if ate_food else 0) + (state.bonus_points if ate_bonus else 0)
    next_foods_eaten = state.foods_eaten + (1 if ate_food else 0)

    next_bonus_food = state.bonus_food
    next_bonus_timer = state.bonus_timer_ticks

    if ate_bonus:
        next_bonus_food = None
        next_bonus_timer = 0
    elif next_bonus_food is not None:
        next_bonus_timer -= 1
        if next_bonus_timer <= 0:
            next_bonus_food = None
            next_bonus_timer = 0

    next_food = state.food
    if ate_food:
        next_food = _spawn_food(
            width=state.width,
            height=state.height,
            snake=next_snake,
            obstacles=state.obstacles,
            bonus_food=next_bonus_food,
            food_selector=food_selector,
            rng=rng,
        )

    if (
        ate_food
        and next_bonus_food is None
        and state.bonus_frequency > 0
        and next_foods_eaten % state.bonus_frequency == 0
    ):
        next_bonus_food = _spawn_bonus(
            width=state.width,
            height=state.height,
            snake=next_snake,
            obstacles=state.obstacles,
            food=next_food,
            food_selector=food_selector,
            rng=rng,
        )
        if next_bonus_food is not None:
            next_bonus_timer = state.bonus_lifetime_ticks

    next_status = state.status
    if next_food is None and next_bonus_food is None:
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
        base_tick_ms=state.base_tick_ms,
        min_tick_ms=state.min_tick_ms,
        speed_step_ms=state.speed_step_ms,
        speed_every_points=state.speed_every_points,
        wrap_walls=state.wrap_walls,
        obstacles=state.obstacles,
        obstacle_count=state.obstacle_count,
        bonus_food=next_bonus_food,
        bonus_timer_ticks=next_bonus_timer,
        bonus_frequency=state.bonus_frequency,
        bonus_lifetime_ticks=state.bonus_lifetime_ticks,
        bonus_points=state.bonus_points,
        foods_eaten=next_foods_eaten,
    )


def current_tick_ms(state: GameState) -> int:
    if state.speed_every_points <= 0 or state.speed_step_ms <= 0:
        return max(1, state.base_tick_ms)

    level = state.score // state.speed_every_points
    tick_ms = state.base_tick_ms - (level * state.speed_step_ms)
    return max(state.min_tick_ms, tick_ms)


def restart(
    state: GameState,
    food_selector: Optional[CellSelector] = None,
    rng: Optional[random.Random] = None,
) -> GameState:
    return initial_state(
        width=state.width,
        height=state.height,
        start_length=state.start_length,
        base_tick_ms=state.base_tick_ms,
        min_tick_ms=state.min_tick_ms,
        speed_step_ms=state.speed_step_ms,
        speed_every_points=state.speed_every_points,
        start_direction=(1, 0),
        wrap_walls=state.wrap_walls,
        obstacle_count=state.obstacle_count,
        bonus_frequency=state.bonus_frequency,
        bonus_lifetime_ticks=state.bonus_lifetime_ticks,
        bonus_points=state.bonus_points,
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


def _next_head(state: GameState) -> Optional[Point]:
    head_x, head_y = state.snake[0]
    dx, dy = state.direction
    next_x = head_x + dx
    next_y = head_y + dy

    if state.wrap_walls:
        return (next_x % state.width, next_y % state.height)

    next_point = (next_x, next_y)
    if _is_inside(next_point, state.width, state.height):
        return next_point
    return None


def _spawn_food(
    width: int,
    height: int,
    snake: Sequence[Point],
    obstacles: Sequence[Point],
    bonus_food: Optional[Point],
    food_selector: Optional[CellSelector] = None,
    rng: Optional[random.Random] = None,
) -> Optional[Point]:
    occupied = set(snake) | set(obstacles)
    if bonus_food is not None:
        occupied.add(bonus_food)
    return _spawn_cell(width, height, occupied, food_selector, rng)


def _spawn_bonus(
    width: int,
    height: int,
    snake: Sequence[Point],
    obstacles: Sequence[Point],
    food: Optional[Point],
    food_selector: Optional[CellSelector] = None,
    rng: Optional[random.Random] = None,
) -> Optional[Point]:
    occupied = set(snake) | set(obstacles)
    if food is not None:
        occupied.add(food)
    return _spawn_cell(width, height, occupied, food_selector, rng)


def _spawn_cells(
    width: int,
    height: int,
    occupied: Sequence[Point],
    count: int,
    cell_selector: Optional[CellSelector] = None,
    rng: Optional[random.Random] = None,
) -> Tuple[Point, ...]:
    if count <= 0:
        return ()

    occupied_set = set(occupied)
    free_cells = [
        (x, y)
        for y in range(height)
        for x in range(width)
        if (x, y) not in occupied_set
    ]

    if not free_cells:
        return ()

    picks: list[Point] = []
    chooser = rng.choice if rng is not None else random.choice

    for _ in range(min(count, len(free_cells))):
        if cell_selector is not None:
            selected = cell_selector(free_cells)
            if selected not in free_cells:
                raise ValueError("cell_selector returned a cell that is not free")
        else:
            selected = chooser(free_cells)

        picks.append(selected)
        free_cells.remove(selected)

    return tuple(picks)


def _spawn_cell(
    width: int,
    height: int,
    occupied: Sequence[Point],
    cell_selector: Optional[CellSelector] = None,
    rng: Optional[random.Random] = None,
) -> Optional[Point]:
    occupied_set = set(occupied)
    free_cells = [
        (x, y)
        for y in range(height)
        for x in range(width)
        if (x, y) not in occupied_set
    ]

    if not free_cells:
        return None

    if cell_selector is not None:
        selected = cell_selector(free_cells)
        if selected not in free_cells:
            raise ValueError("cell_selector returned a cell that is not free")
        return selected

    chooser = rng.choice if rng is not None else random.choice
    return chooser(free_cells)


def _validate_obstacles(
    obstacles: Sequence[Point],
    width: int,
    height: int,
    snake: Sequence[Point],
) -> None:
    if len(set(obstacles)) != len(tuple(obstacles)):
        raise ValueError("obstacles must be unique")

    snake_set = set(snake)
    for obstacle in obstacles:
        if not _is_inside(obstacle, width, height):
            raise ValueError("obstacle out of bounds")
        if obstacle in snake_set:
            raise ValueError("obstacle cannot overlap snake")
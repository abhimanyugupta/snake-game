import unittest
from dataclasses import replace

from snake.game_logic import (
    STATUS_GAME_OVER,
    STATUS_RUNNING,
    GameState,
    initial_state,
    restart,
    set_direction,
    tick,
)


def pick_first(cells):
    return cells[0]


class SnakeLogicTests(unittest.TestCase):
    def test_tick_moves_snake_forward(self):
        state = initial_state(width=10, height=10, start_length=3, food_selector=pick_first)

        next_state = tick(state, food_selector=pick_first)

        self.assertEqual(next_state.snake[0], (state.snake[0][0] + 1, state.snake[0][1]))
        self.assertEqual(len(next_state.snake), len(state.snake))

    def test_reverse_direction_is_ignored(self):
        state = initial_state(width=10, height=10, food_selector=pick_first)

        next_state = set_direction(state, (-1, 0))

        self.assertEqual(next_state.direction, (1, 0))

    def test_growth_and_score_increase_after_eating(self):
        state = initial_state(width=10, height=10, start_length=3, food_selector=pick_first)
        head_x, head_y = state.snake[0]
        state = replace(state, food=(head_x + 1, head_y))

        next_state = tick(state, food_selector=pick_first)

        self.assertEqual(next_state.score, 1)
        self.assertEqual(len(next_state.snake), len(state.snake) + 1)
        self.assertEqual(next_state.pending_growth, 0)

    def test_wall_collision_causes_game_over(self):
        state = GameState(
            width=5,
            height=5,
            snake=((4, 2), (3, 2), (2, 2)),
            direction=(1, 0),
            food=(0, 0),
            score=0,
            pending_growth=0,
            status=STATUS_RUNNING,
            start_length=3,
            tick_ms=120,
        )

        next_state = tick(state, food_selector=pick_first)

        self.assertEqual(next_state.status, STATUS_GAME_OVER)

    def test_self_collision_causes_game_over(self):
        state = GameState(
            width=6,
            height=6,
            snake=((2, 2), (2, 3), (1, 3), (1, 2), (1, 1), (2, 1)),
            direction=(-1, 0),
            food=(5, 5),
            score=0,
            pending_growth=0,
            status=STATUS_RUNNING,
            start_length=3,
            tick_ms=120,
        )

        next_state = tick(state, food_selector=pick_first)

        self.assertEqual(next_state.status, STATUS_GAME_OVER)

    def test_food_spawns_in_only_remaining_free_cell(self):
        state = GameState(
            width=4,
            height=2,
            snake=((2, 0), (1, 0), (0, 0), (0, 1), (1, 1), (2, 1)),
            direction=(1, 0),
            food=(3, 0),
            score=0,
            pending_growth=0,
            status=STATUS_RUNNING,
            start_length=3,
            tick_ms=120,
        )

        next_state = tick(state, food_selector=pick_first)

        self.assertEqual(next_state.food, (3, 1))
        self.assertNotIn(next_state.food, next_state.snake)

    def test_restart_resets_state(self):
        state = GameState(
            width=10,
            height=10,
            snake=((9, 9), (8, 9), (7, 9), (6, 9)),
            direction=(0, 1),
            food=(0, 0),
            score=42,
            pending_growth=2,
            status=STATUS_GAME_OVER,
            start_length=4,
            tick_ms=150,
        )

        reset_state = restart(state, food_selector=pick_first)

        self.assertEqual(reset_state.status, STATUS_RUNNING)
        self.assertEqual(reset_state.score, 0)
        self.assertEqual(reset_state.direction, (1, 0))
        self.assertEqual(len(reset_state.snake), state.start_length)
        self.assertNotIn(reset_state.food, reset_state.snake)


if __name__ == "__main__":
    unittest.main()
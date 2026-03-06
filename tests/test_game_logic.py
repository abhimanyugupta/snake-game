import unittest
from dataclasses import replace

from snake.game_logic import (
    STATUS_GAME_OVER,
    STATUS_RUNNING,
    GameState,
    current_tick_ms,
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

    def test_wall_collision_causes_game_over(self):
        state = GameState(
            width=5,
            height=5,
            snake=((4, 2), (3, 2), (2, 2)),
            direction=(1, 0),
            food=(0, 0),
            status=STATUS_RUNNING,
        )

        next_state = tick(state, food_selector=pick_first)

        self.assertEqual(next_state.status, STATUS_GAME_OVER)

    def test_wrap_mode_moves_across_boundary(self):
        state = GameState(
            width=5,
            height=5,
            snake=((4, 2), (3, 2), (2, 2)),
            direction=(1, 0),
            food=(0, 0),
            wrap_walls=True,
            status=STATUS_RUNNING,
        )

        next_state = tick(state, food_selector=pick_first)

        self.assertEqual(next_state.status, STATUS_RUNNING)
        self.assertEqual(next_state.snake[0], (0, 2))

    def test_obstacle_collision_causes_game_over(self):
        state = GameState(
            width=6,
            height=6,
            snake=((2, 2), (1, 2), (0, 2)),
            direction=(1, 0),
            food=(5, 5),
            obstacles=((3, 2),),
            obstacle_count=1,
            status=STATUS_RUNNING,
        )

        next_state = tick(state, food_selector=pick_first)

        self.assertEqual(next_state.status, STATUS_GAME_OVER)

    def test_bonus_food_spawns_after_frequency_threshold(self):
        state = initial_state(
            width=10,
            height=10,
            bonus_frequency=1,
            bonus_lifetime_ticks=7,
            food_selector=pick_first,
        )
        head_x, head_y = state.snake[0]
        state = replace(state, food=(head_x + 1, head_y))

        next_state = tick(state, food_selector=pick_first)

        self.assertEqual(next_state.score, 1)
        self.assertIsNotNone(next_state.bonus_food)
        self.assertEqual(next_state.bonus_timer_ticks, 7)

    def test_bonus_timer_expires(self):
        state = initial_state(width=10, height=10, food_selector=pick_first)
        state = replace(state, bonus_food=(0, 0), bonus_timer_ticks=1)

        next_state = tick(state, food_selector=pick_first)

        self.assertIsNone(next_state.bonus_food)
        self.assertEqual(next_state.bonus_timer_ticks, 0)

    def test_eating_bonus_increases_score_and_growth(self):
        state = initial_state(width=10, height=10, bonus_points=4, food_selector=pick_first)
        head_x, head_y = state.snake[0]
        state = replace(state, food=(0, 0), bonus_food=(head_x + 1, head_y), bonus_timer_ticks=5)

        next_state = tick(state, food_selector=pick_first)

        self.assertEqual(next_state.score, 4)
        self.assertEqual(len(next_state.snake), len(state.snake) + 1)
        self.assertIsNone(next_state.bonus_food)

    def test_speed_ramp_respects_min_tick(self):
        state = initial_state(
            width=10,
            height=10,
            base_tick_ms=120,
            min_tick_ms=80,
            speed_step_ms=10,
            speed_every_points=2,
            food_selector=pick_first,
        )

        self.assertEqual(current_tick_ms(state), 120)
        self.assertEqual(current_tick_ms(replace(state, score=4)), 100)
        self.assertEqual(current_tick_ms(replace(state, score=10)), 80)

    def test_restart_preserves_mode_settings(self):
        state = initial_state(
            width=12,
            height=12,
            wrap_walls=True,
            obstacle_count=5,
            bonus_frequency=3,
            bonus_lifetime_ticks=8,
            bonus_points=6,
            base_tick_ms=140,
            min_tick_ms=70,
            speed_step_ms=7,
            speed_every_points=2,
            food_selector=pick_first,
        )

        ended_state = replace(state, score=15, status=STATUS_GAME_OVER)
        reset_state = restart(ended_state, food_selector=pick_first)

        self.assertEqual(reset_state.status, STATUS_RUNNING)
        self.assertEqual(reset_state.score, 0)
        self.assertTrue(reset_state.wrap_walls)
        self.assertEqual(reset_state.obstacle_count, 5)
        self.assertEqual(reset_state.bonus_frequency, 3)
        self.assertEqual(reset_state.bonus_lifetime_ticks, 8)
        self.assertEqual(reset_state.bonus_points, 6)
        self.assertEqual(reset_state.base_tick_ms, 140)
        self.assertEqual(reset_state.min_tick_ms, 70)
        self.assertEqual(reset_state.speed_step_ms, 7)
        self.assertEqual(reset_state.speed_every_points, 2)


if __name__ == "__main__":
    unittest.main()
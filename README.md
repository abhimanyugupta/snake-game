# Snake (Python + pygame)

A minimal Snake game with deterministic core logic and a classic-plus menu.

## Features

- Classic loop: movement, food, growth, score, game-over, restart.
- Main menu with difficulty presets (Easy / Normal / Hard).
- Speed ramp based on score (with per-difficulty min speed cap).
- Persistent high score stored locally in `high_score.txt`.
- Optional wrap-around walls mode.
- Optional obstacles mode.
- Timed bonus food that gives extra points.

## Install

```bash
pip install pygame
```

## Run

```bash
python main.py
```

## Controls

### Menu

- Up/Down or `1`/`2`/`3`: select difficulty
- `W`: toggle wrap mode
- `O`: toggle obstacles mode
- Enter/Space: start game
- Esc: quit

### In game

- Arrow keys / WASD: move
- `P`: pause/resume
- `R`: restart current run
- `M`: return to menu
- Esc: quit

## Tests

```bash
python -m unittest -q
```

## Manual verification checklist

- Menu difficulty selection starts at expected speed.
- Speed increases as score rises and does not pass configured minimum.
- High score updates after game-over and persists across restarts.
- Wrap mode ON allows crossing edges; OFF causes wall game-over.
- Obstacles mode ON spawns blocks and collisions end the game.
- Bonus food appears after threshold, expires on timer, and grants bonus points.
- Pause (`P`) freezes updates and resumes cleanly.
- Restart (`R`) resets current run with selected mode settings.
# Snake (Python + pygame)

A classic-plus Snake game with deterministic core logic, unit tests, and premium visual polish.

## Features

- Classic loop: movement, food, growth, score, game-over, restart.
- Premium V2 visuals: responsive HUD/controls layout, smoother movement interpolation, food/score/death feedback effects.
- Main menu with difficulty presets (Easy / Normal / Hard).
- Speed ramp based on score (with per-difficulty min speed cap).
- Persistent high score stored locally in `high_score.txt`.
- Optional wrap-around walls mode.
- Optional obstacles mode.
- Timed bonus food that gives extra points.

## Install

```bash
pip install -r requirements.txt
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

- Bottom controls text never clips at normal window sizes.
- Snake movement appears smooth between grid ticks.
- Score chip pulses on food pickup; food pop effects render.
- Death shows shake + red flash and summary overlay with retry/menu hints.
- Speed increases as score rises and does not pass configured minimum.
- High score updates after game-over and persists across restarts.
- Wrap mode ON allows crossing edges; OFF causes wall game-over.
- Obstacles mode ON spawns blocks and collisions end the game.
- Bonus food appears after threshold, expires on timer, and grants bonus points.
- Pause (`P`) overlay appears and resumes cleanly.
- Restart (`R`) resets current run with selected mode settings.
# Snake (Python + pygame)

A classic-plus Snake game with deterministic core logic, unit tests, and premium visuals.

## Features

- Classic loop: movement, food, growth, score, game-over, restart.
- Premium visual UI (menu cards, HUD chips, polished overlays, glow effects).
- Resizable window with aspect-ratio-preserving scaling.
- Theme system (3 palettes): cycle with `T`.
- Audio SFX (menu/start/eat/bonus/death/achievement) with mute and volume controls.
- Persistent settings in `settings.json` (difficulty, wrap, obstacles, theme, volume, mute).
- Persistent progression in `stats.json` (games, totals, bests, achievements).
- Main menu with difficulty presets (Easy / Normal / Hard).
- Speed ramp based on score (with per-difficulty min speed cap).
- Persistent high score stored in `high_score.txt`.
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
- `T`: cycle theme
- `X`: mute/unmute audio
- `-` / `=`: volume down/up
- Enter/Space: start game
- Esc: quit

### In game

- Arrow keys / WASD: move
- `P`: pause/resume
- `R`: restart current run
- `M`: return to menu
- `T`: cycle theme
- `X`: mute/unmute audio
- `-` / `=`: volume down/up
- Esc: quit

## Tests

```bash
python -m unittest -q
```

## Runtime files

- `high_score.txt`: best score
- `settings.json`: saved user settings
- `stats.json`: cumulative progression and achievements

## Manual verification checklist

- Window can be resized and the game scales cleanly without overlap.
- Theme switching updates both menu and gameplay visuals.
- Settings persist after restarting the app.
- Audio reacts to events; mute/volume controls work.
- Stats and achievements update after completed runs.
- Bottom controls text does not clip.
- Snake movement remains smooth between ticks.
- Wrap/obstacles/difficulty toggles affect gameplay correctly.
- Pause/restart/menu flow remains stable.


# Snake (Python + pygame)

A minimal classic Snake game with deterministic core logic and unit tests.

## Install

```bash
pip install pygame
```

## Run

```bash
python main.py
```

## Controls

- Arrow keys / WASD: move
- P: pause/resume
- R: restart
- Esc: quit

## Tests

```bash
python -m unittest -q
```

## Manual verification checklist

- Controls respond for both arrows and WASD.
- Snake moves one grid cell per tick.
- Immediate reverse direction is ignored.
- Eating food increases score and length.
- Hitting walls causes game over.
- Hitting snake body causes game over.
- Pause (`P`) freezes updates and resumes cleanly.
- Restart (`R`) resets score, snake, and food.
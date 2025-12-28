# Contributing

Thanks for your interest in improving LocalEval Bench.

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Running checks

```bash
python -m ruff check harness scripts tests
python -m pytest
```

## Adding tasks

- `tasks/md`: short logic checks with `<!-- rubric: ... -->`
- `tasks/synth`: lemma + proof sketch with rubric
- `tasks/lean`: Lean-style ASCII theorem + rubric in `/- ... -/`
- `tasks/py`: add a folder with `impl.py` and `tests.py`

## Submitting changes

- Keep changes focused and well described
- Update docs when you add new task families or metrics
- Avoid adding large generated reports

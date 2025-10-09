# Python Dependency Toolchain Compatibility Experiment

This experiment mirrors the Rust version but for Python packages.

## Methodology

- Take a list of foundational Python packages.
- Make a project that depends on a recent major version using version specifiers
  like `>=2.0` to allow flexibility in resolution.
- Find the oldest Python toolchain we can use while still being able to use
  the latest Python toolchain. They can use different resolved versions
  (like different lockfiles), but must use the same dependency specification.

## Tool: uv

This experiment uses [uv](https://github.com/astral-sh/uv) exclusively:
- `uv python install` - Install Python versions (like `rustup toolchain install`)
- `uv venv` - Create virtual environments
- `uv pip install` - Install packages (much faster than pip)

This is analogous to the Rust experiment using `rustup` and `cargo`.

## The package list

certifi
charset-normalizer
click
idna
jinja2
markupsafe
numpy
packaging
pillow
platformdirs
pluggy
pytest
python-dateutil
pytz
pyyaml
requests
setuptools
six
urllib3

## Running

```bash
cd python
python3 experiment.py
```

Results will be written to `results.json`.

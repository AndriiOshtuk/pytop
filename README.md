pytop -- Htop copycat implemented in Python.
========================================

**pytop** is an interactive process viewer for Unix systems. It is a text-mode application (for console or X terminals) and requires Urwid.

## Local Development

```sh
sudo apt install python3-venv

cd pytop
# Setup venv.
python3 -m venv ./venv
source ./venv/bin/activate
pip install -U pip wheel
# Install in editable mode.
pip install -e .
# Run
python3 -m pytop
```

"""Layout composition helpers.

This package contains higher-level, feature-oriented builders that assemble
rooms/connectors from the low-level primitives in `modules/`.

The generator entrypoints (`main_hostel.py`, etc.) run these in script-mode
(where `src/python_generator` is on `sys.path`), so imports here are written
as top-level package imports (e.g. `from modules...`).
"""

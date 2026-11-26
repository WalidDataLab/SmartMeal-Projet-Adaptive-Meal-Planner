# -*- coding: utf-8 -*-
"""Shared fixtures: every test gets its own fresh copy of the three SQLite databases."""
import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
# Must be set before app.py is imported so the real backend/*.db files are never touched.
os.environ["SMARTMEAL_DATA_DIR"] = tempfile.mkdtemp(prefix="smartmeal-import-")

from backend import db  # noqa: E402
from backend.init_db import init_databases  # noqa: E402


@pytest.fixture
def fresh_db(tmp_path):
    db.set_data_dir(str(tmp_path))
    init_databases()
    return tmp_path


@pytest.fixture
def client(tmp_path):
    from app import create_app
    app = create_app(data_dir=str(tmp_path), testing=True)
    return app.test_client()


CTX_A = {"device_type": "desktop", "available_time": 30, "meal_budget": "medium",
         "connection_quality": "fast", "meal_moment": "any"}
CTX_B = {"device_type": "mobile", "available_time": 10, "meal_budget": "low",
         "connection_quality": "slow", "meal_moment": "any"}
CTX_C = {"device_type": "mobile", "available_time": 10, "meal_budget": "medium",
         "connection_quality": "normal", "meal_moment": "any"}

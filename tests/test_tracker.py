import sys
import os
import json
import pytest
from datetime import date

# Add src to path so we can import tracker
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tracker import log_hours, get_fortnightly_hours, check_status
from config import FORTNIGHTLY_HOUR_LIMIT, ALERT_THRESHOLD

# ── Helpers ──────────────────────────────────────────────────────────────────

def setup_test_data(tmp_path, entries):
    """Create a temporary data file for testing"""
    data_file = tmp_path / "work_hours.json"
    data_file.write_text(json.dumps({"entries": entries}))
    return str(data_file)

# ── Config Tests ──────────────────────────────────────────────────────────────

def test_hour_limit_is_48():
    """Visa limit must be 48 hours"""
    assert FORTNIGHTLY_HOUR_LIMIT == 48

def test_alert_threshold_is_80_percent():
    """Alert should trigger at 80%"""
    assert ALERT_THRESHOLD == 0.8

# ── Data Tests ────────────────────────────────────────────────────────────────

def test_log_hours_saves_entry(tmp_path, monkeypatch):
    """Logging hours should save an entry to the data file"""
    data_file = tmp_path / "work_hours.json"
    monkeypatch.setenv("DATA_FILE", str(data_file))

    import tracker
    monkeypatch.setattr(tracker, "DATA_FILE", str(data_file))

    tracker.log_hours(4, "TestJob")

    with open(str(data_file)) as f:
        data = json.load(f)

    assert len(data["entries"]) == 1
    assert data["entries"][0]["hours"] == 4
    assert data["entries"][0]["job"] == "TestJob"

def test_log_hours_records_today(tmp_path, monkeypatch):
    """Logged entry should have today's date"""
    data_file = tmp_path / "work_hours.json"

    import tracker
    monkeypatch.setattr(tracker, "DATA_FILE", str(data_file))

    tracker.log_hours(3, "TestJob")

    with open(str(data_file)) as f:
        data = json.load(f)

    assert data["entries"][0]["date"] == str(date.today())

# ── Hour Calculation Tests ────────────────────────────────────────────────────

def test_fortnightly_hours_counts_recent(tmp_path, monkeypatch):
    """Should count hours from last 14 days"""
    import tracker
    data_file = tmp_path / "work_hours.json"

    entries = [
        {"date": str(date.today()), "hours": 8, "job": "BP"},
        {"date": str(date.today()), "hours": 6, "job": "TeamKids"},
    ]
    data_file.write_text(json.dumps({"entries": entries}))
    monkeypatch.setattr(tracker, "DATA_FILE", str(data_file))

    total = tracker.get_fortnightly_hours()
    assert total == 14

def test_fortnightly_hours_ignores_old_entries(tmp_path, monkeypatch):
    """Should ignore entries older than 14 days"""
    import tracker
    data_file = tmp_path / "work_hours.json"

    entries = [
        {"date": "2020-01-01", "hours": 20, "job": "OldJob"},
        {"date": str(date.today()), "hours": 5, "job": "NewJob"},
    ]
    data_file.write_text(json.dumps({"entries": entries}))
    monkeypatch.setattr(tracker, "DATA_FILE", str(data_file))

    total = tracker.get_fortnightly_hours()
    assert total == 5

def test_empty_data_returns_zero(tmp_path, monkeypatch):
    """Should return 0 hours when no entries exist"""
    import tracker
    data_file = tmp_path / "work_hours.json"
    data_file.write_text(json.dumps({"entries": []}))
    monkeypatch.setattr(tracker, "DATA_FILE", str(data_file))

    total = tracker.get_fortnightly_hours()
    assert total == 0
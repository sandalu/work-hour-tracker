import sys
import os
import json
import pytest
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import tracker
from config import FORTNIGHTLY_HOUR_LIMIT, ALERT_THRESHOLD

def write_data(tmp_path, entries):
    data_file = tmp_path / "work_hours.json"
    data_file.write_text(json.dumps({"entries": entries}))
    return str(data_file)

def write_settings(tmp_path, settings):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps(settings))
    return str(settings_file)

def patch_files(monkeypatch, tmp_path, entries=None, settings=None):
    data_file = write_data(tmp_path, entries or [])
    settings_file = write_settings(tmp_path, settings or {})
    monkeypatch.setattr(tracker, "DATA_FILE", data_file)
    monkeypatch.setattr(tracker, "SETTINGS_FILE", settings_file)
    return data_file, settings_file

def test_hour_limit_is_48():
    assert FORTNIGHTLY_HOUR_LIMIT == 48

def test_alert_threshold_is_80_percent():
    assert ALERT_THRESHOLD == 0.8

def test_log_hours_saves_entry(tmp_path, monkeypatch):
    patch_files(monkeypatch, tmp_path)
    tracker.log_hours(4, "TestJob", str(date.today()))
    with open(tracker.DATA_FILE) as f:
        data = json.load(f)
    assert len(data["entries"]) == 1
    assert data["entries"][0]["hours"] == 4
    assert data["entries"][0]["job"] == "TestJob"

def test_log_hours_records_today(tmp_path, monkeypatch):
    patch_files(monkeypatch, tmp_path)
    tracker.log_hours(3, "TestJob", str(date.today()))
    with open(tracker.DATA_FILE) as f:
        data = json.load(f)
    assert data["entries"][0]["date"] == str(date.today())

def test_log_hours_uses_work_date(tmp_path, monkeypatch):
    patch_files(monkeypatch, tmp_path)
    work_date = str(date.today() - timedelta(days=3))
    tracker.log_hours(5, "BP", work_date)
    with open(tracker.DATA_FILE) as f:
        data = json.load(f)
    assert data["entries"][0]["work_date"] == work_date

def test_log_hours_decimal(tmp_path, monkeypatch):
    patch_files(monkeypatch, tmp_path)
    tracker.log_hours(1.9, "DeliveryApp", str(date.today()))
    with open(tracker.DATA_FILE) as f:
        data = json.load(f)
    assert data["entries"][0]["hours"] == 1.9

def test_log_multiple_entries(tmp_path, monkeypatch):
    patch_files(monkeypatch, tmp_path)
    tracker.log_hours(4, "BP", str(date.today()))
    tracker.log_hours(3, "TeamKids", str(date.today()))
    with open(tracker.DATA_FILE) as f:
        data = json.load(f)
    assert len(data["entries"]) == 2

def test_fortnightly_hours_counts_current_period(tmp_path, monkeypatch):
    academic_start = date.today() - timedelta(weeks=4)
    settings = {"academic_start": str(academic_start)}
    entries = [
        {"date": str(date.today()), "work_date": str(date.today()), "hours": 8, "job": "BP", "is_break": False},
        {"date": str(date.today()), "work_date": str(date.today()), "hours": 6, "job": "TeamKids", "is_break": False},
    ]
    patch_files(monkeypatch, tmp_path, entries=entries, settings=settings)
    total = tracker.get_fortnightly_hours_by_offset(0)
    assert total == 14

def test_fortnightly_hours_ignores_old_entries(tmp_path, monkeypatch):
    academic_start = date.today() - timedelta(weeks=8)
    settings = {"academic_start": str(academic_start)}
    entries = [
        {"date": "2020-01-01", "work_date": "2020-01-01", "hours": 20, "job": "OldJob", "is_break": False},
        {"date": str(date.today()), "work_date": str(date.today()), "hours": 5, "job": "NewJob", "is_break": False},
    ]
    patch_files(monkeypatch, tmp_path, entries=entries, settings=settings)
    total = tracker.get_fortnightly_hours_by_offset(0)
    assert total == 5

def test_empty_data_returns_zero(tmp_path, monkeypatch):
    academic_start = date.today() - timedelta(weeks=2)
    settings = {"academic_start": str(academic_start)}
    patch_files(monkeypatch, tmp_path, entries=[], settings=settings)
    total = tracker.get_fortnightly_hours_by_offset(0)
    assert total == 0

def test_break_hours_excluded_from_fortnight(tmp_path, monkeypatch):
    academic_start = date.today() - timedelta(weeks=4)
    settings = {"academic_start": str(academic_start)}
    entries = [
        {"date": str(date.today()), "work_date": str(date.today()), "hours": 8, "job": "BP", "is_break": False},
        {"date": str(date.today()), "work_date": str(date.today()), "hours": 10, "job": "BP", "is_break": True},
    ]
    patch_files(monkeypatch, tmp_path, entries=entries, settings=settings)
    total = tracker.get_fortnightly_hours_by_offset(0)
    assert total == 8

def test_get_academic_start(tmp_path, monkeypatch):
    settings = {"academic_start": "2026-02-16"}
    patch_files(monkeypatch, tmp_path, settings=settings)
    result = tracker.get_academic_start()
    assert str(result) == "2026-02-16"

def test_set_academic_start(tmp_path, monkeypatch):
    patch_files(monkeypatch, tmp_path)
    tracker.set_academic_start("2026-02-16")
    with open(tracker.SETTINGS_FILE) as f:
        settings = json.load(f)
    assert settings["academic_start"] == "2026-02-16"

def test_no_academic_start_returns_none(tmp_path, monkeypatch):
    patch_files(monkeypatch, tmp_path, settings={})
    result = tracker.get_academic_start()
    assert result is None

def test_before_academic_start_blocked(tmp_path, monkeypatch):
    academic_start = date.today()
    settings = {"academic_start": str(academic_start)}
    patch_files(monkeypatch, tmp_path, settings=settings)
    before_date = str(date.today() - timedelta(days=1))
    assert tracker.is_before_academic_start(before_date) == True

def test_on_academic_start_allowed(tmp_path, monkeypatch):
    academic_start = date.today()
    settings = {"academic_start": str(academic_start)}
    patch_files(monkeypatch, tmp_path, settings=settings)
    assert tracker.is_before_academic_start(str(academic_start)) == False

def test_after_academic_start_allowed(tmp_path, monkeypatch):
    academic_start = date.today() - timedelta(days=10)
    settings = {"academic_start": str(academic_start)}
    patch_files(monkeypatch, tmp_path, settings=settings)
    assert tracker.is_before_academic_start(str(date.today())) == False

def test_break_not_active_by_default(tmp_path, monkeypatch):
    patch_files(monkeypatch, tmp_path, settings={})
    assert tracker.is_break_active() == False

def test_start_break(tmp_path, monkeypatch):
    patch_files(monkeypatch, tmp_path, settings={})
    tracker.start_break()
    with open(tracker.SETTINGS_FILE) as f:
        settings = json.load(f)
    assert settings["break_active"] == True
    assert "break_start" in settings

def test_end_break(tmp_path, monkeypatch):
    settings = {"break_active": True, "break_start": str(date.today())}
    patch_files(monkeypatch, tmp_path, settings=settings)
    tracker.end_break()
    with open(tracker.SETTINGS_FILE) as f:
        settings = json.load(f)
    assert settings["break_active"] == False
    assert "break_end" in settings

def test_hours_during_break_tagged(tmp_path, monkeypatch):
    settings = {
        "academic_start": str(date.today() - timedelta(weeks=4)),
        "break_active": True,
        "break_start": str(date.today() - timedelta(days=2))
    }
    patch_files(monkeypatch, tmp_path, settings=settings)
    tracker.log_hours(4, "BP", str(date.today()))
    with open(tracker.DATA_FILE) as f:
        data = json.load(f)
    assert data["entries"][0]["is_break"] == True

def test_hours_outside_break_not_tagged(tmp_path, monkeypatch):
    settings = {
        "academic_start": str(date.today() - timedelta(weeks=4)),
        "break_active": False,
    }
    patch_files(monkeypatch, tmp_path, settings=settings)
    tracker.log_hours(4, "BP", str(date.today()))
    with open(tracker.DATA_FILE) as f:
        data = json.load(f)
    assert data["entries"][0]["is_break"] == False
"""Тесты для загрузки/сохранения профиля (core/profile.py).

Профиль хранится в JSON-файле. Тут проверяем, что данные корректно
сохраняются, читаются обратно и что битый/отсутствующий файл не ломает игру.

Путь к файлу подменяется через monkeypatch на временный, чтобы тесты
не трогали настоящий data/profile.json.
"""

import json

import pytest

from core import profile as profile_module


@pytest.fixture
def profile_path(tmp_path, monkeypatch):
    path = tmp_path / "profile.json"
    monkeypatch.setattr(profile_module, "PROFILE_FILE", str(path))
    return path


def test_load_missing_file_returns_default(profile_path):
    assert not profile_path.exists()
    profile = profile_module.load_profile()
    assert profile == {"coins": 0, "upgrades": {}}


def test_save_then_load_roundtrip(profile_path):
    original = {"coins": 250, "upgrades": {"auto_fire": 1, "tavern": 1}}
    profile_module.save_profile(original)
    loaded = profile_module.load_profile()
    assert loaded == original


def test_save_creates_file(profile_path):
    profile_module.save_profile({"coins": 5, "upgrades": {}})
    assert profile_path.exists()


def test_load_corrupted_json_returns_default(profile_path):
    profile_path.write_text("это не json {{{", encoding="utf-8")
    assert profile_module.load_profile() == {"coins": 0, "upgrades": {}}


def test_load_coerces_types(profile_path):
    # coins дробное, уровни строками — должны привестись к int.
    profile_path.write_text(
        json.dumps({"coins": 99.0, "upgrades": {"auto_fire": "2"}}),
        encoding="utf-8",
    )
    loaded = profile_module.load_profile()
    assert loaded["coins"] == 99
    assert loaded["upgrades"]["auto_fire"] == 2


def test_load_handles_missing_keys(profile_path):
    profile_path.write_text(json.dumps({}), encoding="utf-8")
    assert profile_module.load_profile() == {"coins": 0, "upgrades": {}}


def test_load_invalid_coins_falls_back_to_zero(profile_path):
    profile_path.write_text(
        json.dumps({"coins": "много", "upgrades": {}}), encoding="utf-8"
    )
    assert profile_module.load_profile()["coins"] == 0

"""Загрузка и сохранение профиля игрока (монеты и улучшения)."""

import json
from pathlib import Path

from config import PROFILE_FILE


def _default_profile():
    """Возвращает пустой профиль по умолчанию.

    Returns:
        Словарь с нулём монет и пустым набором улучшений.
    """
    return {"coins": 0, "upgrades": {}}


def load_profile():
    """Читает профиль из файла на диске.

    Если файл отсутствует или повреждён, возвращается профиль по
    умолчанию. Прочитанные значения приводятся к корректным типам.

    Returns:
        Словарь профиля с ключами "coins" (int) и "upgrades" (dict).
    """
    path = Path(PROFILE_FILE)
    if not path.exists():
        return _default_profile()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _default_profile()

    coins = data.get("coins", 0)
    upgrades = data.get("upgrades", {})
    return {
        "coins": int(coins) if isinstance(coins, (int, float)) else 0,
        "upgrades": {str(k): int(v) for k, v in upgrades.items()}
        if isinstance(upgrades, dict)
        else {},
    }


def save_profile(profile):
    """Сохраняет профиль в файл в формате JSON.

    Args:
        profile: словарь профиля с ключами "coins" и "upgrades".
    """
    path = Path(PROFILE_FILE)
    path.parent.mkdir(exist_ok=True)
    data = {
        "coins": int(profile["coins"]),
        "upgrades": {k: int(v) for k, v in profile["upgrades"].items()},
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

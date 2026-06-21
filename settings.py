"""Загрузка и сохранение пользовательских настроек экрана."""

import json
from pathlib import Path

from config import AVAILABLE_RESOLUTIONS, BASE_RESOLUTION, SETTINGS_FILE


def load_settings():
    """Читает настройки из файла, подставляя значения по умолчанию.

    При отсутствии или повреждении файла, а также при недопустимом
    разрешении возвращаются безопасные значения по умолчанию.

    Returns:
        Словарь с ключами "is_fullscreen" (bool) и "resolution"
        (кортеж ширина-высота).
    """
    path = Path(SETTINGS_FILE)
    if not path.exists():
        return {"is_fullscreen": True, "resolution": BASE_RESOLUTION}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"is_fullscreen": True, "resolution": BASE_RESOLUTION}

    raw = data.get("resolution", BASE_RESOLUTION)
    try:
        resolution = tuple(raw)
    except TypeError:
        resolution = BASE_RESOLUTION

    if resolution not in AVAILABLE_RESOLUTIONS:
        resolution = BASE_RESOLUTION
    return {
        "is_fullscreen": bool(data.get("is_fullscreen", False)),
        "resolution": resolution,
    }


def save_settings(settings):
    """Сохраняет настройки в файл в формате JSON.

    Args:
        settings: словарь с ключами "is_fullscreen" и "resolution".
    """
    path = Path(SETTINGS_FILE)
    path.parent.mkdir(exist_ok=True)
    data = {
        "is_fullscreen": settings["is_fullscreen"],
        "resolution": list(settings["resolution"]),
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

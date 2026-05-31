import json
from pathlib import Path

from config import AVAILABLE_RESOLUTIONS, BASE_RESOLUTION, SETTINGS_FILE


def load_settings():
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
    path = Path(SETTINGS_FILE)
    path.parent.mkdir(exist_ok=True)
    data = {
        "is_fullscreen": settings["is_fullscreen"],
        "resolution": list(settings["resolution"]),
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

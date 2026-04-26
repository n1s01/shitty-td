import json
from dataclasses import asdict, dataclass
from pathlib import Path

from config import AVAILABLE_RESOLUTIONS, BASE_RESOLUTION

SETTINGS_FILE = Path(__file__).parent.parent / "data" / "settings.json"


@dataclass
class AppSettings:
    is_fullscreen: bool = False
    resolution: tuple[int, int] = BASE_RESOLUTION


def load_settings():
    if not SETTINGS_FILE.exists():
        return AppSettings()

    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return AppSettings()

    raw_resolution = data.get("resolution", BASE_RESOLUTION)
    try:
        resolution = tuple(raw_resolution)
    except TypeError:
        resolution = BASE_RESOLUTION

    if resolution not in AVAILABLE_RESOLUTIONS:
        resolution = BASE_RESOLUTION

    return AppSettings(
        is_fullscreen=bool(data.get("is_fullscreen", False)),
        resolution=resolution,
    )


def save_settings(settings):
    data = asdict(settings)
    data["resolution"] = list(settings.resolution)
    SETTINGS_FILE.parent.mkdir(exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

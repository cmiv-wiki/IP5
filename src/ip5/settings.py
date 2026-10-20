"""Settings remembered between sessions (~/.ip5/settings.json)."""
import json
from pathlib import Path

SETTINGS_PATH = Path.home() / '.ip5' / 'settings.json'

DEFAULTS = {
    'port': '',
    'output_folder': str(Path.home() / 'Documents' / 'IP5 recordings'),
    'file_prefix': 'IP5',
    'selected_data': [],
    'monitor_window_min': 5,
}


def loadSettings():
    settings = dict(DEFAULTS)
    try:
        settings.update(json.loads(SETTINGS_PATH.read_text(encoding='utf-8')))
    except (OSError, ValueError):
        pass
    return settings


def saveSettings(settings):
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding='utf-8')
    except OSError:
        pass

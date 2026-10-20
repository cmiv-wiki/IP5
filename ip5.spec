# PyInstaller spec, build with ./build_app.sh (or: pyinstaller ip5.spec)
import sys

sys.path.insert(0, 'src')
from ip5 import __version__

a = Analysis(
    ['run_app.py'],
    pathex=['src'],
    hiddenimports=['serial.tools.list_ports'],
    excludes=['PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'IPython', 'pandas', 'scipy'],
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='IP5 Recorder',
    console=False,
    argv_emulation=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name='IP5 Recorder')

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='IP5 Recorder.app',
        bundle_identifier='se.liu.ip5recorder',
        version=__version__,
        info_plist={
            'NSHighResolutionCapable': True,
            'CFBundleShortVersionString': __version__,
        },
    )

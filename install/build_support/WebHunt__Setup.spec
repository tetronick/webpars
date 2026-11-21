# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
ROOT = Path(SPECPATH).resolve().parent

payload = str(ROOT / 'dist' / 'app' / 'WebHunt__.exe')

a = Analysis(
    [str(ROOT / 'installer_source/setup_app.py')],
    pathex=[str(ROOT / 'src')],
    binaries=[],
    datas=[(payload, 'payload'), (str(ROOT / 'assets/webhunt_logo.png'), 'assets'), (str(ROOT / 'assets/webhunt_logo.ico'), 'assets'), (str(ROOT / 'assets/webhunt_logo.ico'), 'payload')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WebHunt__Setup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / 'assets/webhunt_logo.ico'),
    version=str(ROOT / 'build_support/setup_version_info.txt'),
)




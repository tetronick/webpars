# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_all
ROOT = Path(SPECPATH).resolve().parent

datas = []
binaries = []
hiddenimports = ['bs4', 'requests', 'dns.resolver', 'dns.rdtypes', 'openpyxl', 'reportlab']
datas += [(str(ROOT / 'assets/webhunt_logo.png'), 'assets'), (str(ROOT / 'assets/webhunt_logo.ico'), 'assets'), (str(ROOT / 'assets/Roboto-Regular.ttf'), 'assets'), (str(ROOT / 'src/webhunt/audit/recommendations.json'), 'webhunt/audit')]
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    [str(ROOT / 'tools/app.py')],
    pathex=[str(ROOT / 'src')],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='WebHunt__',
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
    version=str(ROOT / 'build_support/version_info.txt'),
)




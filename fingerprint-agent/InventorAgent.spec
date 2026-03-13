# -*- mode: python ; coding: utf-8 -*-
import os, sys

# DLL fayllarini to'plash
binaries = []
if os.path.exists('libzkfp.dll'):
    binaries.append(('libzkfp.dll', '.'))

pyzkfp_dlls = [
    'venv/Lib/site-packages/pyzkfp/libzkfpcsharp.dll',
    'venv/Lib/site-packages/pyzkfp/dll/libzkfpcsharp.dll',
]
for p in pyzkfp_dlls:
    if os.path.exists(p):
        binaries.append((p, '.'))

# config.json
datas = []
if os.path.exists('dist/InventorAgent/config.json'):
    datas.append(('dist/InventorAgent/config.json', '.'))

a = Analysis(
    ['launcher.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        'flask', 'flask_cors', 'pyzkfp', 'requests',
        'webview', 'webview.platforms.winforms',
        'clr', 'pythonnet', 'bottle', 'proxy_tools',
        'logging', 'json', 'base64', 'threading',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

# Bitta EXE — konsol yo'q, sayt oyna sifatida ochiladi
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='InventorAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # Konsol oynasi ko'rinmaydi
    windowed=True,       # Windows windowed mode
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['mahjong_game.py'],
    pathex=[],
    binaries=[],
    datas=[('799px-Mahjong_eg_Shanghai.webp', '.'), ('Images', 'Images'), ('Levels', 'Levels'), ('Musiques', 'Musiques'), ('effets', 'effets')],
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
    name='mahjong_game',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = []
datas += collect_data_files('tkinter')


a = Analysis(
    ['src\\app\\desktop_ui.py'],
    pathex=['.'],
    binaries=[('D:/1- VS file menu/Piano Transcription & Arrangement AI/.conda/Library/bin/tcl86t.dll', '.'), ('D:/1- VS file menu/Piano Transcription & Arrangement AI/.conda/Library/bin/tk86t.dll', '.'), ('D:/1- VS file menu/Piano Transcription & Arrangement AI/.conda/Library/bin/ffi.dll', '.'), ('D:/1- VS file menu/Piano Transcription & Arrangement AI/.conda/Library/bin/libexpat.dll', '.'), ('D:/1- VS file menu/Piano Transcription & Arrangement AI/.conda/Library/bin/LIBBZ2.dll', '.'), ('D:/1- VS file menu/Piano Transcription & Arrangement AI/.conda/Library/bin/liblzma.dll', '.'), ('D:/1- VS file menu/Piano Transcription & Arrangement AI/.conda/Library/bin/zstd.dll', '.')],
    datas=datas,
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
    name='PianoTransAI_TempTest_Fixed',
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

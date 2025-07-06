# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['menu.py'],
    pathex=[],
    binaries=[],
    datas=[('facts_200.json', '.'), ('lessons.json', '.'), ('grammar_n5.json', '.'), ('grammar_n4.json', '.'), ('grammar_n3.json', '.'), ('grammar_constructions.json', '.'), ('conjugation_table_with_translations.json', '.')],
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
    name='JapaneseTrainer',
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
    icon=['icon.ico'],
)

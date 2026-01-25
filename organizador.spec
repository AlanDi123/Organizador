# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file para Organizador - Aplicación de Finanzas
Genera un ejecutable optimizado con todas las dependencias incluidas
"""

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/', 'src/'),
        ('assets/', 'assets/'),
        ('data/', 'data/'),
    ],
    hiddenimports=[
        'tkinter',
        'tkcalendar',
        'requests',
        'sqlite3',
        'json',
        'csv',
        'datetime',
        'threading',
        'logging',
        'os',
        'sys',
        'locale',
        'matplotlib',
        'matplotlib.pyplot',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Organizador',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Sin ventana de consola
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Organizador'
)

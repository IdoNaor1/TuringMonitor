# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('layouts', 'layouts'),
        ('config.py', '.'),
        ('device_manager.py', '.'),
        ('monitor.py', '.'),
        ('renderer.py', '.'),
        ('widgets.py', '.'),
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'serial.tools.list_ports',
        'psutil',
        'GPUtil',
        'pystray',
        'pystray._win32',
        'six',
        'config',
        'device_manager',
        'monitor',
        'renderer',
        'widgets',
    ],
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
    name='TuringControlCenter',
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

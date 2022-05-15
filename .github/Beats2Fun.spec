# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

a = Analysis(
    ['Beats2Fun.py', 'Beats2Bar.py', 'Beats2Map.py'],
    pathex=[],
    binaries=[],
    datas=[('Resources', 'Resources')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Fun
exe_fun = EXE(
    pyz,
    [('Beats2Fun.py','Beats2Bar.py', 'PY')],
    [],
    exclude_binaries=True,
    name='Beats2Fun',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="Resources/icon.ico"
)

# Bar
exe_bar = EXE(
    pyz,
    [('Beats2Bar.py','Beats2Bar.py', 'PY')],
    [],
    exclude_binaries=True,
    name='Beats2Bar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="Resources/icon.ico"
)

# Map
exe_map = EXE(
    pyz,
    [('Beats2Map.py','Beats2Map.py', 'PY')],
    [],
    exclude_binaries=True,
    name='Beats2Map',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="Resources/icon.ico"
)

coll = COLLECT(
    exe_fun,
    exe_bar,
    exe_map,
    
    a.binaries,
    a.zipfiles,
    a.datas,
    
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Beats2Fun',
)

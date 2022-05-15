# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

# Fun
a_fun = Analysis(
    ['Beats2Fun.py'],
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
pyz_fun = PYZ(a_fun.pure, a_fun.zipped_data, cipher=block_cipher)
exe_fun = EXE(
    pyz_fun,
    a_fun.scripts,
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
    icon="program_icon.png"
)

# Bar
a_bar = Analysis(
    ['Beats2Bar.py'],
    pathex=[],
    binaries=[],
    datas=[],
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
pyz_bar = PYZ(a_bar.pure, a_bar.zipped_data, cipher=block_cipher)
exe_bar = EXE(
    pyz_bar,
    a_bar.scripts,
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
    icon="program_icon.png"
)

# Map
a_map = Analysis(
    ['Beats2Map.py'],
    pathex=[],
    binaries=[],
    datas=[],
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
pyz_map = PYZ(a_map.pure, a_map.zipped_data, cipher=block_cipher)
exe_map = EXE(
    pyz_map,
    a_map.scripts,
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
    icon="program_icon.png"
)

coll = COLLECT(
    exe_fun,
    a_fun.binaries,
    a_fun.zipfiles,
    a_fun.datas,
    
    exe_bar,
    a_bar.binaries,
    a_bar.zipfiles,
    a_bar.datas,
    
    exe_map,
    a_map.binaries,
    a_map.zipfiles,
    a_map.datas,
    
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Beats2Fun',
)

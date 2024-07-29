# -*- mode: python ; coding: utf-8 -*-


activate_cron_a = Analysis(
    ['activate_cron.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

auto_off_a = Analysis(
    ['auto_off.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

MERGE( (activate_cron_a, 'activate_cron', 'activate_cron'), (auto_off_a, 'auto_off', 'auto_off') )

activate_cron_pyz = PYZ(activate_cron_a.pure)
activate_cron_exe = EXE(
    activate_cron_pyz,
    activate_cron_a.scripts,
    [],
    exclude_binaries=True,
    name='activate_cron',
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
)
activate_cron_coll = COLLECT(
    activate_cron_exe,
    activate_cron_a.binaries,
    activate_cron_a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='activate_cron',
)

auto_off_pyz = PYZ(auto_off_a.pure)
auto_off_exe = EXE(
    auto_off_pyz,
    auto_off_a.scripts,
    [],
    exclude_binaries=True,
    name='auto_off',
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
)
auto_off_coll = COLLECT(
    auto_off_exe,
    auto_off_a.binaries,
    auto_off_a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='auto_off',
)
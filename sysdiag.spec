# -*- mode: python ; coding: utf-8 -*-
# Fichier de configuration PyInstaller pour SysDiag v4
# Build : pyinstaller sysdiag.spec
#
# A LANCER SOUS WINDOWS (PyInstaller produit un exe pour l'OS sur lequel il tourne).

block_cipher = None

a = Analysis(
    ['SysDiag_v4.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'psutil',
        'requests',
        'requests.adapters',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
    ],
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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SysDiag_v4',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                    # False = pas de fenêtre console noire derrière l'UI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='sysdiag.ico',                # Optionnel : retire cette ligne si tu n'as pas d'icône
    manifest='sysdiag.manifest',       # Demande l'élévation admin (UAC) automatiquement
    uac_admin=True,                    # Equivalent redondant mais explicite avec PyInstaller récent
    version='version_info.txt',        # Optionnel : métadonnées (voir fichier fourni)
)

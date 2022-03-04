# -*- mode: python ; coding: utf-8 -*-

# Building the executable:
#
# docker run -v "$$(pwd):/src/" cdrx/pyinstaller-linux "pyinstaller platerec_installer.spec -F"
# docker run -v "$$(pwd):/src/" danleyb2/pyinstaller-windows "pyinstaller platerec_installer.spec -F"

import sys

block_cipher = None

if sys.platform == 'win32':
    site_packages = 'C:/Python37/Lib/site-packages/'
    pathex = ['Z:\\src']
elif sys.platform == 'linux':
    site_packages = '/root/.pyenv/versions/3.7.5/lib/python3.7/site-packages/'
    pathex = ['/src']
else: # MacOs on GH Actions
    site_packages = '/Users/runner/hostedtoolcache/Python/3.7.12/x64/lib/python3.7/site-packages/'
    pathex = [os.path.abspath(SPECPATH)]

a = Analysis(  # noqa
    ['platerec_installer.py'],
    pathex=pathex,
    binaries=[],
    datas=[(site_packages + 'dash_core_components/', 'dash_core_components'),
           (site_packages + 'dash_html_components/', 'dash_html_components'),
           (site_packages + 'dash_renderer/', 'dash_renderer'),
           (site_packages + 'dash_bootstrap_components/',
            'dash_bootstrap_components'),
            ('assets', 'assets')],
    hiddenimports=['pkg_resources.py2_warn'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)  # noqa
exe = EXE(  # noqa
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas, [],
    name='PlateRecognizer-Installer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True)

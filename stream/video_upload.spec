# -*- mode: python ; coding: utf-8 -*-

# Building the executable:
#
# docker run -v "$$(pwd):/src/" cdrx/pyinstaller-linux "pyinstaller video_upload.spec -F"
# docker run -v "$$(pwd):/src/" danleyb2/pyinstaller-windows "pyinstaller video_upload.spec -F"

import sys
import gooey

block_cipher = None

gooey_root = os.path.dirname(gooey.__file__)
gooey_languages = Tree(os.path.join(gooey_root, 'languages'), prefix = 'gooey/languages')
gooey_images = Tree(os.path.join(gooey_root, 'images'), prefix = 'gooey/images')


if sys.platform == 'win32':
    site_packages = 'C:/Python37/Lib/site-packages/'
    pathex = ['Z:\\src']
else:
    site_packages = '/root/.pyenv/versions/3.7.5/lib/python3.7/site-packages/'
    pathex = ['/src']

a = Analysis(  # noqa
    ['video_upload.py'],
    pathex=pathex,
    binaries=[],
    hiddenimports=['pkg_resources.py2_warn'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)  # noqa

options = [('u', None, 'OPTION')]

exe = EXE(  # noqa
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas, 
    options,
    gooey_languages, # Add them in to collected files
    gooey_images, # Same here.
    name='VideoUpload',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False)
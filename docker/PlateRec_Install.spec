# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['PlateRec_Install.py'],
             pathex=['Z:\\src'],
             binaries=[],
             datas=[('C:/Python37/Lib/site-packages/dash_core_components/', 'dash_core_components'), ('C:/Python37/Lib/site-packages/dash_html_components/', 'dash_html_components'), ('C:/Python37/Lib/site-packages/dash_renderer/', 'dash_renderer'), ('C:/Python37/Lib/site-packages/dash_bootstrap_components/', 'dash_bootstrap_components')],
             hiddenimports=['pkg_resources.py2_warn'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='PlateRec_Install',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )

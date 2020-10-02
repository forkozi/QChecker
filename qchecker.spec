# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

home = Path.home()

cwd = Path.cwd()
env_path = Path(os.environ['CONDA_PREFIX'])
dlls = env_path / 'DLLs'
bins = env_path / 'Library' / 'bin'

paths = [
    str(cwd),
    str(env_path),
    str(dlls),
    str(bins),
]

binaries = [
    (str(bins / 'geos.dll'), '.'),
    (str(bins / 'geos_c.dll'), '.'),
    (str(bins / 'spatialindex_c-64.dll'), '.'),
    (str(bins / 'spatialindex-64.dll'), '.'),
    (str(bins / 'pdal.exe'), '.')
]

proj_path = env_path / 'Library' / 'share' / 'proj'
proj_datas = [
    (str(proj_path / 'CH'), 'pyproj'),
    (str(proj_path / 'GL27'), 'pyproj'),
    (str(proj_path / 'ITRF2000'), 'pyproj'),
    (str(proj_path / 'ITRF2008'), 'pyproj'),
    (str(proj_path / 'ITRF2014'), 'pyproj'),
    (str(proj_path / 'nad.lst'), 'pyproj'),
    (str(proj_path / 'nad27'), 'pyproj'),
    (str(proj_path / 'nad83'), 'pyproj'),
    (str(proj_path / 'other.extra'), 'pyproj'),
    (str(proj_path / 'proj.db'), 'pyproj'),
    (str(proj_path / 'proj.ini'), 'pyproj'),
    (str(proj_path / 'world'), 'pyproj')
]

conf_files = [
    (str(cwd / 'assets' / 'config_files' / 'las_classes.json'), '.'),
    (str(cwd / 'assets' / 'config_files' / 'qaqc_config.json'), '.')
]

asset_files = [
    (str(cwd / 'assets/*'), 'asset_files'),
]

datas = collect_data_files('geopandas', subdir='datasets') \
        + collect_data_files('pandas') \
        + collect_data_files('bokeh') \
        + collect_data_files('pyproj') \
        + collect_data_files('rasterio', include_py_files=True) \
        + collect_data_files('osgeo', include_py_files=True) \
        + collect_data_files('assets') \
        + proj_datas \
        + conf_files \
        + asset_files

hidden_imports = ['rasterio._shim',
                  'rasterio.control',
                  'rasterio.crs',
                  'rasterio.sample',
                  'rasterio.vrt',
                  'rasterio._features',
                  'pyproj.datadir',
                  'pyproj._datadir',
                  'fiona._shim',
                  'fiona.schema',
                  'osgeo',
                  'geopandas',
                  'pandas',
                  'pandas._libs.tslibs.base']

runtime_hooks = ['hook.py']

a = Analysis(['qchecker_gui.py'],
             pathex=paths,
             binaries=binaries,
             datas=datas,
             hiddenimports=hidden_imports,
             hookspath=[],
             runtime_hooks=runtime_hooks,
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [('W ignore', None, 'OPTION')],
          exclude_binaries=True,
          name='Q-Checker',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          icon='assets\\images\\qaqc.ico',
          version='CI\\version.py')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='Q-Checker')

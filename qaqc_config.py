import json


config_data = {
    'project_name': 'nantucket',
    'qaqc_dir': r'C:\QAQC_contract\nantucket',
    'las_tile_dir': r'C:\QAQC_contract\nantucket\CLASSIFIED_LAS',
    'qaqc_gdb': r'C:\QAQC_contract\nantucket\qaqc_nantucket.gdb',
    'tile_size': 500,
    'dz_binary_dir': r'C:\QAQC_contract\nantucket\dz',
    'dz_raster_dir': r'C:\QAQC_contract\nantucket\qaqc_nantucket.gdb',
    'contractor_shp': r'C:\QAQC_contract\nantucket\EXTENTS\final\Nantucket_TileGrid.shp',
    'dz_classes_template': r'C:\QAQC_contract\dz_classes.lyr',
    'dz_export_settings': r'C:\QAQC_contract\\dz_export_settings.xml',
    'dz_mxd': r'C:\QAQC_contract\nantucket\QAQC_nantucket.mxd',

    'checks_to_do': {
        'naming_convention': True,
        'version': True,
        'pdrf': True,
        'gps_time_type': True,
        'hor_datum': True,
        'ver_datum': False,
        'point_source_ids': False,
        'unexpected_classes': True,
        'create_dz': False,
    }
}

with open('Z:\qaqc\qaqc_config.json', 'w') as f:
    json.dump(config_data, f)

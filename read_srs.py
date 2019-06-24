import pdal
import json
from osgeo import osr
import base64
from pathlib import Path


las_dir = Path('V:/FL1608/lidar/CLASSIFIED_LIDAR')
las_files = list(las_dir.glob('*.las'))
print(las_files)

for las in las_files:
    las = str(las).replace('\\', '/')
    print(las)

    pdal_json = """{"pipeline": [ """ + '"{}"'.format(las) + """]}"""

    pipeline = pdal.Pipeline(pdal_json)
    #pipeline.validate()

    count = pipeline.execute()
    #arrays = pipeline.arrays
    
    metadata = pipeline.metadata
    meta_dict = json.loads(metadata)

    srs = meta_dict['metadata']['readers.las']['srs']

    hor_wkt = srs['horizontal']
    ver_wkt = srs['vertical']

    hor_srs=osr.SpatialReference(wkt=hor_wkt)
    ver_srs=osr.SpatialReference(wkt=ver_wkt)   

    hor_cs_name = hor_srs.GetAttrValue('projcs')
    ver_cs_name = ver_srs.GetAttrValue('vert_cs')

    print('{:11s}: {}'.format('horizontal', hor_cs_name))
    print('{:11s}: {}'.format('vertical', ver_cs_name))

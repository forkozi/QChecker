import pdal
import json
from osgeo import osr

vdatums = ['ellipsoid', 'mllw', 'mhw', 'navd88']
for vdatum in vdatums:
    las_tile = 'C:/Users/nickf/OneDrive/NOAA/QAQC_Checker/martha_las_test/{}/2016_374000e_4594000n_las.las'.format(vdatum)
    pdal_json = """{"pipeline": [ """ + '"{}"'.format(las_tile) + """]}"""

    pipeline = pdal.Pipeline(pdal_json)
    pipeline.validate()

    count = pipeline.execute()
    arrays = pipeline.arrays
    
    metadata = pipeline.metadata
    meta_dict = json.loads(metadata)
    srs = meta_dict['metadata']['readers.las'][0]['srs']

    hor_wkt = srs['horizontal']
    ver_wkt = srs['vertical']

    hor_srs=osr.SpatialReference(wkt=hor_wkt)
    ver_srs=osr.SpatialReference(wkt=ver_wkt)   
    
    print(hor_srs.ExportToWkt())
    print(hor_srs.ExportToProj4())

    hor_cs_name = hor_srs.GetAttrValue('projcs')
    ver_cs_name = ver_srs.GetAttrValue('vert_cs')

    print(vdatum.upper())
    print('{:11s}: {}'.format('horizontal', hor_cs_name))
    print('{:11s}: {}'.format('vertical', ver_cs_name))
    print()

import pdal
import json
from osgeo import osr
import base64


vdatums = ['ellipsoid', 'mllw', 'mhw', 'navd88']


for vdatum in vdatums:
    #las_tile = 'Z:/martha_las_test/{}/2016_374000e_4594000n_las.las'.format(vdatum)
    las_tile = 'V:/VA1803/Lidar/Classified_LAS/delivery02/2018_342500e_4233000n_las.las'
    #las_tile = 'C:/Users/Nick.Forfinski-Sarko/Downloads/result/sample1000.las'
    #las_tile = 'X:/2016/FL1606-TB-N-880_Sarasota_p/06_RIEGL_PROC/04_EXPORT/Green/02_FL1606-TB-N-880_Sarasota_g_gpsa_rf_ip_wsf_r/S1_160518_180518_Record003_Line263.las'
    #las_tile = 'X:/2016/FL1606-TB-N-880_Sarasota_p/06_RIEGL_PROC/04_EXPORT/Green/03_FL1606-TB-N-880_Sarasota_g_gpsa_rf_ip_wsf_r_adj_blks/000245.las'

    pdal_json = """{"pipeline": [ """ + '"{}"'.format(las_tile) + """]}"""

    pipeline = pdal.Pipeline(pdal_json)
    #pipeline.validate()

    count = pipeline.execute()
    #arrays = pipeline.arrays
    
    metadata = pipeline.metadata
    meta_dict = json.loads(metadata)

    srs = meta_dict['metadata']['readers.las']['srs']

    hor_wkt = srs['horizontal']
    ver_wkt = srs['vertical']

    print(hor_wkt)
    print(ver_wkt)

    hor_srs=osr.SpatialReference(wkt=hor_wkt)
    ver_srs=osr.SpatialReference(wkt=ver_wkt)   

    hor_cs_name = hor_srs.GetAttrValue('projcs')
    ver_cs_name = ver_srs.GetAttrValue('vert_cs')

    #print('=' * 80)
    #print(las_tile)
    #print()
    #print(hor_srs)
    #print()
    #print(ver_srs)
    #print()
    print(vdatum.upper())
    print('{:11s}: {}'.format('horizontal', hor_cs_name))
    print('{:11s}: {}'.format('vertical', ver_cs_name))
    print()

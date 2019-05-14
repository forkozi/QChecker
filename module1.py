import os
import json
import subprocess
from osgeo import gdal, osr


path = r'C:\\Users\\Nick.Forfinski-Sarko\\AppData\\Local\\Continuum\\anaconda3\\Scripts'
os.environ["PATH"] += os.pathsep + path

las_path = r'Y:/2018/TBL_880_Eglin_Santa_Rosa_I_p/06_RIEGL_PROC/04_EXPORT/Green/06_TBL_880_Eglin_Santa_Rosa_I_g_gpsa_rf_wsf_rf_tm_flucs_elh_depth_bias_geocode\2018_513000e_3361000n.las'
cmd_str = 'conda run -n pdal_env pdal info {} --metadata'.format(las_path)


def get_srs(las_path):
    try:
        process = subprocess.Popen(cmd_str.split(' '), shell=True, stdout=subprocess.PIPE)
        output = process.stdout.read()
        return output
    except Exception as e:
        print(e)

wkt = json.loads(get_srs(las_path).decode('utf-8'))['metadata']['comp_spatialreference']
srs = osr.SpatialReference(wkt=wkt)

print(srs.GetAttrValue('PROJCS'))
print(srs.GetAttrValue('VERT_CS'))

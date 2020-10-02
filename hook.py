import os
import sys


pyproj_dir = os.path.dirname(sys.argv[0]) + r'\pyproj'
gdal_dir = os.path.dirname(sys.argv[0]) + r'\gdal'

print(pyproj_dir)
print(gdal_dir)

os.environ['PROJ_LIB'] = pyproj_dir
os.environ['GDAL_DATA'] = gdal_dir

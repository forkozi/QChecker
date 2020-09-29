import os
import sys



os.environ['PROJ_LIB'] = os.path.dirname(sys.argv[0]) + r'\pyproj'
os.environ['GDAL_DATA'] = os.path.dirname(sys.argv[0]) + r'\gdal'

print(os.environ['PROJ_LIB'])
print(os.environ['GDAL_DATA'])
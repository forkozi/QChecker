from pyproj import Proj, transform
import fiona
from fiona.crs import from_epsg
import os


qaqc_dir = r'C:\QAQC_contract\nantucket'
contractor_las_tiles = r'C:\QAQC_contract\nantucket\EXTENTS\final\Nantucket_TileGrid.shp'
las_tiles_geojson = os.path.join(qaqc_dir, 'contractor_tiles.json')

shp = fiona.open(contractor_las_tiles)
original = Proj(init='EPSG:26919')
nad83_2011 = Proj(init='EPSG:6317')
wgs84 = Proj(init='EPSG:4326')

with fiona.open(contractor_las_tiles) as source:
    records = list(source)

geojson = {"type": "FeatureCollection","features": records}
schema = {'geometry': 'Polygon', 'properties': {}}
with fiona.open(las_tiles_geojson, 'w', 'GeoJSON', schema, crs=from_epsg(6317)) as output:
    for feat in geojson['features']:
        out_linear_ring = []

        for point in feat['geometry']['coordinates'][0]:
            print(point)
            easting, northing = point
            lat, lon = transform(original, wgs84, easting, northing)
            feat['geometry']['coordinates'] = (lat, lon)
            print('{} --> {}'.format(point, feat['geometry']['coordinates']))
            out_linear_ring.append((lat, lon))
           
        feat['geometry']['coordinates'] = [out_linear_ring]
        feat['properties'] = {}

        output.write(feat)
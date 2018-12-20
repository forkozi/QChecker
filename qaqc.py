import os
import json
import logging
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, mapping, shape
from shapely import wkt
import numpy as np
import subprocess
from laspy.file import File
import xml.etree.ElementTree as ET
import arcpy
import osgeo.osr as osr
import pathos.pools as pp
from pathos.helpers import mp
import re
import fiona
from fiona.crs import from_epsg
from pyproj import Proj, transform
from geodaisy import GeoObject

project_name = 'nantucket'

qaqc_dir = r'C:\QAQC_contract\nantucket'
qaqc_gdb = r'{}\qaqc_nantucket.gdb'.format(qaqc_dir)

las_tile_dir = r'{}\CLASSIFIED_LAS'.format(qaqc_dir)
dz_binary_dir = r'{}\dz'.format(qaqc_dir)
dz_raster_dir = r'{}'.format(qaqc_gdb)

tiles_geojson = os.path.join(qaqc_dir, 'tiles_WGS84.json')
tiles_centroids_geojson = os.path.join(qaqc_dir, 'tiles_centroids_WGS84.json')
tiles_csv = os.path.join(qaqc_dir, 'tiles.csv')

qaqc_csv = r'C:\QAQC_contract\nantucket\qaqc.csv'
qaqc_geojson_NAD83_UTM_CENTROIDS = r'C:\QAQC_contract\nantucket\qaqc_NAD83_UTM_CENTROIDS.json'
qaqc_geojson_NAD83_UTM_POLYGONS = r'C:\QAQC_contract\nantucket\qaqc_NAD83_UTM_POLYGONS.json'
qaqc_shp_NAD83_UTM_POLYGONS = r'C:\QAQC_contract\nantucket\qaqc_NAD83_UTM.shp'

tiles_shp = r'C:\QAQC_contract\nantucket\EXTENTS\final\Nantucket_TileGrid.shp'

classification_scheme_dir = r'\\ngs-s-rsd\response_dl\Research\transfer\software\LP360'
classification_scheme_xml = 'noaa_topobathy_v02.xml'
classificaiton_scheme_fpath = os.path.join(classification_scheme_dir, classification_scheme_xml)

dz_classes_template = r'C:\QAQC_contract\dz_classes.lyr'
dz_export_settings = r'C:\QAQC_contract\\dz_export_settings.xml'
dz_mxd = r'{}\QAQC_nantucket.mxd'.format(qaqc_dir)

dz_raster_catalog_base_name = r'{}_raster_catalog'.format(project_name)
dz_raster_catalog = r'{}\{}'.format(qaqc_gdb, dz_raster_catalog_base_name)

dz_mosaic_raster_basename = '{}_dz_mosaic'.format(project_name)
dz_mosaic_raster = '{}\{}'.format(qaqc_gdb, dz_mosaic_raster_basename)

dz_bins = {
	0: (0.00, 0.04, 'darkgreen'),
	1: (0.04, 0.08, 'lightgreen'),
	2: (0.08, 0.12, 'cyan'),
	3: (0.12, 0.16, 'yellow'),
	4: (0.16, 0.20, 'orange'),
	5: (0.20, 1000, 'red'),
}

checks_to_do = {
	'naming_convention': True,
	'version': True,
	'pdrf': True,
	'gps_time_type': True,
	'hor_datum': True,
	'ver_datum': False,
	'point_source_ids': False,
	'create_dz': True
}


class LasTileCollection():

	def __init__(self, las_tile_dir):
		self.las_dir = las_tile_dir
		self.num_las = len(self.get_las_names())

	def get_las_tile_paths(self):
		return [os.path.join(self.las_dir, f) for f in os.listdir(self.las_dir) if f.endswith('.las')]

	def get_las_names(self):
		return [f for f in os.listdir(self.las_dir) if f.endswith('.las')]

	def get_las_base_names(self):
		return [os.path.splitext(tile)[0] for tile in self.get_las_names()]

	def get_classification_scheme(xml_fpath):
		root = ET.parse(xml_fpath).getroot()
		classes = {}
		for c in root.iter('Class'):
			label = c.find('Label').text
			value = c.find('Values')[0].text
			classes[label] = value
		classes_json_str = json.dumps(classes, indent=2)
		print(classes_json_str)


class LasTile:

	def __init__(self, las_path):
		self.path = las_path
		self.name = os.path.splitext(las_path.split(os.sep)[-1])[0]
		self.inFile = File(self.path, mode="r")

		def get_useful_las_header_info():
			info_to_get = 'global_encoding,version_major,version_minor,' \
						  'created_day,created_year,' \
						  'data_format_id,x_min,x_max,y_min,y_max'
			header = {}
			for info in info_to_get.split(','):
				header[info] = self.inFile.header.reader.get_header_property(info)
			header['VLRs'] = {}
			for vlr in self.inFile.header.vlrs:
				# get coordinate system name (e.g., NAD_1983_2011_UTM_Zone_19N)
				if vlr.record_id == 34737:
					header['VLRs']['coord_sys'] = vlr.parsed_body[0].decode('utf-8').split('|')[0]
			return header

		self.header = get_useful_las_header_info()
		self.las_extents = {
			'ExtentXMin': self.header['x_min'],
			'ExtentXMax': self.header['x_max'],
			'ExtentYMin': self.header['y_min'],
			'ExtentYMax': self.header['y_max'],
			}

		def calc_las_centroid():
			tile_size = 500  # meters
			data_nw_x = self.las_extents['ExtentXMin']
			data_nw_y = self.las_extents['ExtentYMax']
			las_nw_x = data_nw_x - (data_nw_x % tile_size)
			las_nw_y = data_nw_y + tile_size - (data_nw_y % tile_size)
			las_centroid_x = las_nw_x + tile_size / 2
			las_centroid_y = las_nw_y - tile_size / 2
			return (las_centroid_x, las_centroid_y)

		self.centroid_x, self.centroid_y = calc_las_centroid()

		self.tile_extents = {
			'tile_top': self.centroid_y + 250,
			'tile_bottom': self.centroid_y - 250,
			'tile_left': self.centroid_x - 250,
			'tile_right': self.centroid_x + 250,
			}

		self.tile_poly_wkt = GeoObject(Polygon([
			(self.tile_extents['tile_left'], self.tile_extents['tile_top']), 
			(self.tile_extents['tile_right'], self.tile_extents['tile_top']), 
			(self.tile_extents['tile_right'], self.tile_extents['tile_bottom']), 
			(self.tile_extents['tile_left'], self.tile_extents['tile_bottom']),
			(self.tile_extents['tile_left'], self.tile_extents['tile_top']), 
			])).wkt()

		self.tile_centroid_wkt = GeoObject(Point(self.centroid_x, self.centroid_y)).wkt()
		self.class_counts = self.get_class_counts()
		self.has_bathy = True if '{}26{}'.format('class', 'count') in self.class_counts.keys() else False
		self.has_ground = True if '{}2{}'.format('class', 'count') in self.class_counts.keys() else False

		self.checks_result = {
			'naming_convention': None,
			'version': None,
			'pdrf': None,
			'gps_time': None,
			'hor_datum': None,
			'ver_datum': None,
			'point_src_ids': None,
		}

	def __str__(self):
		info_to_output = {
			'tile_name': self.name,
			'header': self.header,
			'tile_extents': self.las_extents,
			'centroid_x': self.centroid_x,
			'centroid_y': self.centroid_y,
			'class_counts': self.class_counts,
			'check_results': self.checks_result,
			'tile_polygon': self.tile_poly_wkt,
			'tile_centroid': self.tile_centroid_wkt,
			}

		# del keys that are not needed because of repitition
		info_to_output['header'].pop('VLRs', None)
		info_to_output['header'].pop('version_major', None)
		info_to_output['header'].pop('version_minor', None)
		info_to_output['header'].pop('global_encoding', None)
		info_to_output['header'].pop('data_format_id', None)
		return json.dumps(info_to_output, indent=2)

	def output_check_results_to_json(self):
		json_dir = r'C:\QAQC_contract\nantucket\qaqc_check_results' # todo: move to settings dict
		json_file_name = r'{}\{}.json'.format(json_dir, self.name)
		with open(json_file_name, 'w') as json_file:
			json_file.write(str(self))

	def get_class_counts(self):
		class_counts = np.unique(self.inFile.classification, return_counts=True)
		class_counts = dict(zip(['class{}count'.format(str(c)) for c in class_counts[0]],
								[str(c) for c in class_counts[1]]))
		print(class_counts)
		return class_counts

	def get_gps_time_type(self):
		gps_time_types = {0: 'GPS Week Time',
						  1: 'Satellite GPS Time'}
		return gps_time_types[self.header['global_encoding']]

	def get_las_version(self):
		return '{}.{}'.format(self.header['version_major'], self.header['version_minor'])

	def get_las_pdrf(self):
		return self.header['data_format_id']

	def get_hor_datum(self):
		return self.header['VLRs']['coord_sys']


class DzOrthoMosaic:

	def __init__(self):
		pass

	def create_raster_catalog(self):
		try:
			arcpy.CreateRasterCatalog_management(
				qaqc_gdb, dz_raster_catalog_base_name,
				raster_management_type='UNMANAGED')
		except Exception, e:
			print(e)

	def add_dz_dir_to_raster_catalog(self):
		logging.info('adding dz_rasters to {}...'.format(dz_raster_catalog))
		arcpy.WorkspaceToRasterCatalog_management(qaqc_gdb, dz_raster_catalog)

	def mosaic_dz_raster_catalog(self):
		logging.info('mosaicing rasters in {}...'.format(dz_raster_catalog))
		print(dz_raster_catalog)
		print(dz_mosaic_raster)
		try:
			arcpy.RasterCatalogToRasterDataset_management(dz_raster_catalog, dz_mosaic_raster)
		except Exception, e:
			print(e)

	def add_dz_mosaic_to_mxd(self):
		mxd = arcpy.mapping.MapDocument(dz_mxd)
		df = arcpy.mapping.ListDataFrames(mxd)[0]
		arcpy.MakeRasterLayer_management(dz_mosaic_raster, dz_mosaic_raster_basename)
		dz_lyr = arcpy.mapping.Layer(dz_mosaic_raster_basename)
		arcpy.mapping.AddLayer(df, dz_lyr, 'AUTO_ARRANGE')
		mxd.save()

	def update_raster_symbology(self):
		mxd = arcpy.mapping.MapDocument(dz_mxd)
		df = arcpy.mapping.ListDataFrames(mxd)[0]
		raster_to_update = arcpy.mapping.ListLayers(mxd, dz_mosaic_raster_basename, df)[0]
		dz_classes_lyr = arcpy.mapping.Layer(dz_classes_template)
		arcpy.mapping.UpdateLayer(df, raster_to_update, dz_classes_lyr, True)
		mxd.save()


class DzOrtho:

	def __init__(self, las_path, las_name, las_extents,
				 dz_binary_dir, dz_raster_dir, dz_export_settings):
		self.las_path = las_path
		self.las_name = las_name
		self.las_extents = las_extents
		self.dz_binary_dir = dz_binary_dir
		self.dz_raster_dir = dz_raster_dir
		self.dz_binary_path = r'{}\{}_dz_dzValue.flt'.format(self.dz_binary_dir, self.las_name)
		self.dz_raster_path = r'{}\dz_{}'.format(self.dz_raster_dir, self.las_name)
		self.dz_export_settings = dz_export_settings

	def __str__(self):
		return self.dz_raster_path

	def binary_to_raster(self):
		try:
			logging.info('converting {} to {}...'.format(self.dz_binary_path, self.dz_raster_path))
			arcpy.FloatToRaster_conversion(self.dz_binary_path, self.dz_raster_path)
		except Exception as e:
			print(e)

	def update_dz_export_settings_extents(self):
		logging.info('updating dz export settings xml with las extents...')
		tree = ET.parse(self.dz_export_settings)
		root = tree.getroot()
		for extent, val in self.las_extents.iteritems():
			for e in root.findall(extent):
				e.text = str(val)
		new_dz_settings = ET.tostring(root)
		myfile = open(self.dz_export_settings, "w")
		myfile.write(new_dz_settings)

	def gen_dz_ortho(self):
		exe = r'C:\Program Files\Common Files\LP360\LDExport.exe'
		las = self.las_path.replace('CLASSIFIED_LAS\\', 'CLASSIFIED_LAS\\\\')
		dz = r'C:\QAQC_contract\nantucket\dz\{}'.format(self.las_name)
		cmd_str = '{} -s {} -f {} -o {}'.format(exe, self.dz_export_settings, las, dz)
		print('generating dz ortho for {}...'.format(las))
		print(cmd_str)
		try:
			returncode, output = run_console_cmd(cmd_str)
		except Exception as e:
			print(e)


class Hillshade:
	def __init__(self):
		pass

	def gen_hillshade_img(self):
		pass


class QaqcTile:

	passed_text = 'PASSED'
	failed_text = 'FAILED'

	def __init__(self, checks_to_do, dz_binary_dir, dz_raster_dir, dz_export_settings):

		self.checks = {
			'naming_convention': self.check_las_naming_convention,
			'version': self.check_las_version,
			'pdrf': self.check_las_pdrf,
			'gps_time_type': self.check_las_gps_time,
			'hor_datum': self.check_hor_datum,
			'ver_datum': self.check_ver_datum,
			'point_source_ids': self.check_point_source_ids,
			'create_dz': self.create_dz
		}

		self.checks_to_do = checks_to_do
		self.dz_binary_dir = dz_binary_dir
		self.dz_raster_dir = dz_raster_dir
		self.dz_export_settings = dz_export_settings

	def check_las_naming_convention(self, tile):
		"""for now, the checks assume Northern Hemisphere"""

		# for info on UTM, see
		# https://www.e-education.psu.edu/natureofgeoinfo/c2_p23.html
		min_easting = 167000
		max_easting = 833000
		min_northing = 0
		max_northing = 9400000
		#min_northing_sh = 1000000 # sh = southern hemisphere
		#max_northing_sh = 10000000

		# first check general format with regex (e.g.,
		# ####_######e_#[#######]n_las)
		pattern = re.compile(r'[0-9]{4}_[0-9]{6}e_[0-9]{1,8}(n_las)')
		if pattern.match(tile.name):
			# then check name components
			tile_name_parts = tile.name.split('_')
			easting = tile_name_parts[1].replace('e', '')
			northing = tile_name_parts[2].replace('n', '')
			easting_good = self.passed_text if easting >= min_easting and easting <= max_easting else self.failed_text
			northing_good = self.passed_text if northing >= min_northing and northing <= max_northing else self.failed_text
			if easting_good and northing_good:
				passed = self.passed_text
			else:
				passed = self.failed_text
		else:
			passed = self.failed_text
		tile.checks_result['naming_convention'] = tile.name
		tile.checks_result['naming_convention_passed'] = passed
		return passed

	def check_las_version(self, tile):
		version = tile.get_las_version()
		if version in ['1.2', '1.4']:
			passed = self.passed_text
		else:
			passed = self.failed_text
		tile.checks_result['version'] = version
		tile.checks_result['version_passed'] = passed
		return passed

	def check_las_pdrf(self, tile):
		las_pdrf = tile.get_las_pdrf()
		las_version = tile.get_las_version()
		if las_pdrf == 3 and las_version == '1.2' or las_pdrf == 6 and las_version == '1.4':
			passed = self.passed_text
		else:
			passed = self.failed_text
		tile.checks_result['pdrf'] = las_pdrf
		tile.checks_result['pdrf_passed'] = passed
		return passed

	def check_las_gps_time(self, tile):
		gps_time_type = tile.get_gps_time_type()
		if gps_time_type == 'Satellite GPS Time':
			passed = self.passed_text
		else:
			passed = self.failed_text
		tile.checks_result['gps_time'] = gps_time_type
		tile.checks_result['gps_time_passed'] = passed
		return passed

	def check_hor_datum(self, tile):
		hor_datum = tile.get_hor_datum()
		if 2 == 2:
			passed = self.passed_text
		else:
			passed = self.failed_text
		tile.checks_result['hor_datum'] = hor_datum
		tile.checks_result['hor_datum_passed'] = passed
		return passed

	def check_ver_datum(self):
		pass

	def check_point_source_ids(self):
		pass

	def calc_pt_cloud_stats(self):
		pass

	def create_dz(self, tile):
		from qaqc import DzOrtho
		if tile.has_bathy or tile.has_ground:
			tile_dz = DzOrtho(tile.path,
				tile.name,
				tile.las_extents,
				self.dz_binary_dir,
				self.dz_raster_dir,
				self.dz_export_settings)
			tile_dz.update_dz_export_settings_extents()
			tile_dz.gen_dz_ortho()
			tile_dz.binary_to_raster()
		else:
			logging.info('{} has no bathy or ground points; no dz ortho generated'.format(tile.name))

	def create_hillshade(self):
		pass

	def add_tile_check_results(self, tile_check_results):
		print(tile_check_results)

	def update_qaqc_results_table(self):
		pass

	def run_qaqc_checks_multiprocess(self, las_path):
		from qaqc import LasTile, LasTileCollection
		import logging
		import xml.etree.ElementTree as ET
		logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)
		tile = LasTile(las_path)
		for c in [k for k, v in self.checks_to_do.iteritems() if v]:
			logging.info('running {}...'.format(c))
			result = self.checks[c](tile)
			logging.info(result)
		tile.output_check_results_to_json()

	def run_qaqc_checks(self, las_paths):
		for las_path in las_paths:
			tile = LasTile(las_path)
			for c in [k for k, v in self.checks_to_do.iteritems() if v]:
				logging.info('running {}...'.format(c))
				result = self.checks[c](tile)
				logging.info(result)
			tile.output_check_results_to_json()

	def run_qaqc(self, las_paths, multiprocess):
		if multiprocess:
			p = pp.ProcessPool(4)
			print(p)
			p.imap(self.run_qaqc_checks_multiprocess, las_paths)
			p.close()
			p.join()
		else:
			self.run_qaqc_checks(las_paths)


class QaqcTileCollection:

	def __init__(self, dz_export_settings, dz_binary_dir, dz_raster_dir,
				 las_paths, qaqc_gdb, checks_to_do):
		self.dz_binary_dir = dz_binary_dir
		self.dz_raster_dir = dz_raster_dir
		self.las_paths = las_paths
		self.qaqc_gdb = qaqc_gdb
		self.checks_to_do = checks_to_do
		self.dz_export_settings = dz_export_settings
		self.json_dir = r'C:\QAQC_contract\nantucket\qaqc_check_results'

	def run_qaqc_tile_collection_checks(self):
		tiles_qaqc = QaqcTile(self.checks_to_do,
			self.dz_binary_dir,
			self.dz_raster_dir,
			self.dz_export_settings)
		tiles_qaqc.run_qaqc(self.las_paths, multiprocess=False)

	def gen_qaqc_results_dict(self):
		def flatten_dict(d_obj):
			for k, v in d_obj.items():
				if isinstance(v, dict):
					new_dict = {k2:v2 for k2, v2 in v.items()}
					for d in flatten_dict(new_dict):
						yield d
				else:
					yield k, v
		flattened_dicts = []
		for las_json in os.listdir(self.json_dir):
			try:
				las_json = os.path.join(self.json_dir, las_json)
				with open(las_json, 'r') as json_file:
					json_data = json.load(json_file)
					flattened_json_data = {k:v for k,v in flatten_dict(json_data)}
					flattened_dicts.append(flattened_json_data)
			except Exception as e:
				print(e)
		return flattened_dicts

	def get_qaqc_results_df(self):
		df = pd.DataFrame(self.gen_qaqc_results_dict())
		return df

	def gen_qaqc_results_gdf_NAD83_UTM_CENTROIDS(self):
		df = self.get_qaqc_results_df()
		df['Coordinates'] = df.tile_centroid
		df['Coordinates'] = df['Coordinates'].apply(wkt.loads)
		nad83_utm_z19 = {'init': 'epsg:26919'}
		gdf = gpd.GeoDataFrame(df, crs=nad83_utm_z19, geometry='Coordinates')
		return gdf

	def gen_qaqc_results_json_NAD83_UTM_CENTROIDS(self, output):
		gdf = self.gen_qaqc_results_gdf_NAD83_UTM_CENTROIDS()
		try:
			os.remove(output)
		except Exception, e:
			print(e)
		gdf.to_file(output, driver="GeoJSON")

	def gen_qaqc_results_gdf_NAD83_UTM_POLYGONS(self):
		df = self.get_qaqc_results_df()
		df['Coordinates'] = df.tile_polygon
		df['Coordinates'] = df['Coordinates'].apply(wkt.loads)
		nad83_utm_z19 = {'init': 'epsg:26919'}
		gdf = gpd.GeoDataFrame(df, crs=nad83_utm_z19, geometry='Coordinates')		
		return gdf

	def gen_qaqc_results_json_NAD83_UTM_POLYGONS(self, output):
		gdf = self.gen_qaqc_results_gdf_NAD83_UTM_POLYGONS()
		try:
			os.remove(output)
		except Exception, e:
			print(e)
		gdf.to_file(output, driver="GeoJSON")

	def gen_qaqc_results_csv(self, output):
		gdf = self.gen_qaqc_results_gdf_NAD83_UTM_CENTROIDS()
		def get_x(pt): return (pt.x)
		def get_y(pt): return (pt.y)
		gdf['centroid_x'] = map(get_x, gdf['Coordinates'])
		gdf['centroid_y'] = map(get_y, gdf['Coordinates'])
		wgs84 = {'init': 'epsg:4326'}
		gdf = gdf.to_crs(wgs84)
		gdf['centroid_lon'] = map(get_x, gdf['Coordinates'])
		gdf['centroid_lat'] = map(get_y, gdf['Coordinates'])
		gdf.to_csv(output, index=False)

	def gen_qaqc_results_shp_NAD83_UTM(self, output):
		gdf = self.gen_qaqc_results_gdf_NAD83_UTM_POLYGONS()
		gdf.to_file(output, driver='ESRI Shapefile')

	def gen_dz_ortho_mosaic(self):
		dz_mosaic = DzOrthoMosaic()
		dz_mosaic.create_raster_catalog()
		dz_mosaic.add_dz_dir_to_raster_catalog()
		dz_mosaic.mosaic_dz_raster_catalog()
		dz_mosaic.add_dz_mosaic_to_mxd()
		dz_mosaic.update_raster_symbology()


def gen_tile_geojson_WGS84(shp, geojson):
	wgs84 = {'init': 'epsg:4326'}
	gdf = gpd.read_file(shp).to_crs(wgs84)
	try:
		os.remove(geojson)
	except Exception, e:
		print(e)
	gdf.to_file(geojson, driver="GeoJSON")


def gen_tile_centroids_csv(shp, out_csv):
	gdf = gpd.read_file(shp)
	gdf['geometry'] = gdf['geometry'].centroid
	def get_x(pt): return (pt.x)
	def get_y(pt): return (pt.y)
	gdf['centroid_x'] = map(get_x, gdf['geometry'])
	gdf['centroid_y'] = map(get_y, gdf['geometry'])
	wgs84 = {'init': 'epsg:4326'}
	gdf = gdf.to_crs(wgs84)
	gdf['geometry'] = gdf['geometry'].centroid
	gdf['centroid_lon'] = map(get_x, gdf['geometry'])
	gdf['centroid_lat'] = map(get_y, gdf['geometry'])
	gdf.to_csv(out_csv)


def run_console_cmd(cmd):
	process = subprocess.Popen(cmd.split(' '))
	output, error = process.communicate()
	returncode = process.poll()
	return returncode, output


def main():
	logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)
	gen_tile_centroids_csv(tiles_shp, tiles_csv)
	gen_tile_geojson_WGS84(tiles_shp, tiles_geojson)

	nantucket = LasTileCollection(las_tile_dir)
	qaqc = QaqcTileCollection(
		dz_export_settings,
		dz_binary_dir,
		dz_raster_dir,
		nantucket.get_las_tile_paths()[0:50],
		qaqc_gdb,
		checks_to_do)
	
	qaqc.run_qaqc_tile_collection_checks()
	qaqc.gen_qaqc_results_csv(qaqc_csv)  # for dashboard
	qaqc.gen_qaqc_results_json_NAD83_UTM_CENTROIDS(qaqc_geojson_NAD83_UTM_CENTROIDS)
	qaqc.gen_qaqc_results_json_NAD83_UTM_POLYGONS(qaqc_geojson_NAD83_UTM_POLYGONS)
	qaqc.gen_qaqc_results_shp_NAD83_UTM(qaqc_shp_NAD83_UTM_POLYGONS)
	qaqc.gen_dz_ortho_mosaic()  # TODO: project to sr = arcpy.SpatialReference('NAD 1983 2011 UTM Zone 19N')


if __name__ == '__main__':

	main()

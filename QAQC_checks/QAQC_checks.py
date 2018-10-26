import os
import json
import logging
##import pandas as pd
import numpy as np
from scipy import stats
import subprocess
from laspy.file import File
import xml.etree.ElementTree as ET
import arcpy
import osgeo.osr as osr
import pathos.pools as pp


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
			# put various useful tidbits from las header into LasTile header dict
			info_to_get = 'global_encoding,version_major,version_minor,' \
						  'created_day,created_year,point_return_count,' \
						  'data_format_id,x_min,x_max,y_min,y_max'
			header = {}
			for info in info_to_get.split(','):
				header[info] = self.inFile.header.reader.get_header_property(info)

			# run through variable length records (VLRs)
			header['VLRs'] = {}
			for vlr in self.inFile.header.vlrs:
				# get coordinate system name (e.g., NAD_1983_2011_UTM_Zone_19N)
				if vlr.record_id == 34737:
					header['VLRs']['coord_sys'] = vlr.parsed_body[0].decode('utf-8').split('|')[0]

			return header

		self.header = get_useful_las_header_info()
		self.las_extents = {'ExtentXMin': self.header['x_min'],
							'ExtentXMax': self.header['x_max'],
							'ExtentYMin': self.header['y_min'],
							'ExtentYMax': self.header['y_max'],
							}
		self.class_counts = self.get_class_counts()
		self.has_bathy = True if '26' in self.class_counts.keys() else False
		self.has_ground = True if '2' in self.class_counts.keys() else False

		self.checks_result = {
			'naming_convention': None,
			'version': None,
			'pdrf': None,
			'gps_time': None,
			'hor_datum': None,
			'ver_datum': None,
			'point_src_ids': None,
		}

	def output_check_results_to_json(self):
		json_file_name = r'C:\QAQC_contract\nantucket\qaqc_check_results\{}.json'.format(self.name)  # todo: fix hard-coding
		info_to_output = {'las_tile_name': self.name,
					'las_tile_extents': self.las_extents,
					'check_results': self.checks_result}
		with open(json_file_name, 'w') as json_file:
			json.dump(info_to_output, json_file)

	def __str__(self):
		obj_str = {'las_header': self.header,
				   'class_counts': self.class_counts,
				   'has_bathy': self.has_bathy}
		return json.dumps(obj_str, indent=2)

	def get_class_counts(self):
		class_counts = np.unique(self.inFile.classification, return_counts=True)
		class_counts = dict(zip([str(c) for c in class_counts[0]],
								[str(c) for c in class_counts[1]]))
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


class DzOrthoMosaic():

	def __init__(self):
		pass

	def create_raster_catalog(self):
		arcpy.CreateRasterCatalog_management(self.qaqc_gdb, 'nantucket_raster_catalog',
											 raster_management_type='UNMANAGED')
	def mosaic_dz_raster_catalog(cls):
		mosaic_raster = '{}\{}_dz_mosaic'.format(self.qaqc_gdb, 'nantucket')
		logging.info('mosaicing rasters in {}...'.format(self.raster_catalog))
		arcpy.RasterCatalogToRasterDataset_management(self.raster_catalog, mosaic_raster)

	def add_dz_dir_to_raster_catalog(self):
		logging.info('adding dz_rasters to {}...'.format(cls.raster_catalog))
		arcpy.WorkspaceToRasterCatalog_management(self.qaqc_gdb, self.raster_catalog)

	def add_dz_mosaic_to_mxd(self):
		md = arcpy.mapping.MapDocument(self.dz_mxd)
		df = arcpy.mapping.ListDataFrames(md)[0]
		mosaic_raster = '{}\{}_dz_mosaic'.format(self.qaqc_gdb, 'nantucket')
		arcpy.MakeRasterLayer_management(mosaic_raster, 'nantucket_dz_mosaic')
		dz_lyr = arcpy.mapping.Layer('nantucket_dz_mosaic')
		arcpy.mapping.AddLayer(df, dz_lyr, 'AUTO_ARRANGE')
		md.save()

	def update_raster_symbology(self):
		md = arcpy.mapping.MapDocument(self.dz_mxd)
		df = arcpy.mapping.ListDataFrames(md)[0]
		mosaic_raster = '{}_dz_mosaic'.format('nantucket')
		raster_to_update = arcpy.mapping.ListLayers(md, mosaic_raster, df)[0]
		dz_classes_lyr = arcpy.mapping.Layer(self.dz_classes_lyr)
		arcpy.mapping.UpdateLayer(df, raster_to_update, dz_classes_lyr, True)
		md.save()


class DzOrtho(LasTile):   

	def __init__(self, las_path, las_name, las_extents):
		self.las_path = las_path
		self.las_name = las_name
		self.las_extents = las_extents
		self.qaqc_dir = r'C:\QAQC_contract\nantucket'
		self.dz_binary_path = r'{}\dz\{}_dz_dzValue.flt'.format(self.qaqc_dir, self.las_name)
		self.dz_raster_path = r'{}\dz_{}'.format(self.qaqc_gdb, self.las_name)

	def update_dz_raster_symbology(self):
		md = arcpy.mapping.MapDocument(self.dz_mxd)
		df = arcpy.mapping.ListDataFrames(md)[0]
		dz_to_update = arcpy.mapping.ListLayers(md, self.las_name, df)[0]
		dz_classes_lyr = arcpy.mapping.Layer(self.dz_classes_lyr)
		arcpy.mapping.UpdateLayer(df, dz_to_update, dz_classes_lyr, True)
		md.save()

	def add_dz_to_mxd(self):
		md = arcpy.mapping.MapDocument(self.dz_mxd)
		df = arcpy.mapping.ListDataFrames(md)[0]
		arcpy.MakeRasterLayer_management(self.dz_raster_path, self.las_name)
		dz_lyr = arcpy.mapping.Layer(self.las_name)
		arcpy.mapping.AddLayer(df, dz_lyr, 'AUTO_ARRANGE')
		md.save()

	def update_dz_export_settings_extents(self):
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

	def binary_to_raster(self):
		logging.info('converting {} to {}...'.format(self.dz_binary_path, self.dz_raster_path))
		try:
			arcpy.FloatToRaster_conversion(self.dz_binary_path, self.dz_raster_path)
		except Exception as e:
			print(e)

	def project_dz_raster(self):
		pass

	def dz_to_numpy(self):  # TODO
		logging.info('getting dz stat for {}...'.format(self.las_name))
		dz_np = arcpy.RasterToNumPyArray(self.dz_raster_path)
		print(dz_np)
		dz_stats = stats.describe(dz_np.flatten())
		print(dz_stats)
		

class HillShade():

	def __init__(self):
		pass

	def gen_hillshade_img(self):
		pass


class QaqcTile():

	def __init__(self, checks_to_do):

		self.checks = {
			'naming_convention': self.check_las_naming_convention,
			'version': self.check_las_version,
			'pdrf': self.check_las_pdrf,
			'gps_time': self.check_las_gps_time,
			'hor_datum': self.check_hor_datum,
			'ver_datum': self.check_ver_datum,
			'point_source_ids': self.check_point_source_ids,
            'create_dz': self.create_dz
		}

		self.checks_to_do = checks_to_do
		
	def check_las_naming_convention(self):
		pass

	def check_las_version(self, tile):
		version = tile.get_las_version()
		if version in ['1.2', '1.4']:
			passed = True
		else:
			passed = False
		tile.checks_result['las_version'] = (passed, version)
		return 'PASSED' if passed else 'FAILED'

	def check_las_pdrf(self, tile):
		las_pdrf = tile.get_las_pdrf()
		las_version = tile.get_las_version()
		if las_pdrf == 3 and las_version == '1.2' or las_pdrf == 6 and las_version == '1.4':
			passed = True
		else:
			passed = False
		tile.checks_result['las_pdrf'] = (passed, las_pdrf)
		return 'PASSED' if passed else 'FAILED'

	def check_las_gps_time(self, tile):
		gps_time_type = tile.get_gps_time_type()
		if gps_time_type == 'Satellite GPS Time':
			passed = True
		else:
			passed = False
		tile.checks_result['gps_time'] = (passed, gps_time_type)
		return 'PASSED' if passed else 'FAILED'

	def check_hor_datum(self, tile):
		hor_datum = tile.get_hor_datum()
		if 2 == 2:
			passed = True
		else:
			passed = False
		tile.checks_result['hor_datum'] = (passed, hor_datum)
		return 'PASSED' if passed else 'FAILED'

	def check_ver_datum(self):
		pass

	def check_point_source_ids(self):
		pass

	def calc_pt_cloud_stats(self):
		pass

	def create_dz(self, tile):
		if tile.has_bathy or tile.has_ground:
			print('peggy sue########################################################################')
			tile_dz = DzOrtho(tile.path, tile.name, tile.las_extents)
			#tile_dz.update_dz_export_settings_extents()
			#tile_dz.gen_dz_ortho()
			#tile_dz.binary_to_raster()
			#tile_dz.dz_to_numpy()
			#tile_dz.add_dz_to_mxd()
			#tile_dz.update_dz_raster_symbology()
		else:
			logging.info('{} has no bathy or ground points; no dz ortho generated'.format(self.tile.name))

	def create_hillshade(self):
		pass

	def add_tile_check_results(self, tile_check_results):
		print(tile_check_results)

	def update_qaqc_results_table(self):
		pass

	def run_qaqc_checks(self, las_path):
		from QAQC_checks import LasTile, LasTileCollection, DzOrtho
		import logging
		logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)

		tile = LasTile(las_path)
		logging.info('checking {}'.format(tile.name))
		for c in [k for k, v in self.checks_to_do.iteritems() if v]:
			logging.info('running {}...'.format(c))
			result = self.checks[c](tile)
			logging.info(result)
		tile.output_check_results_to_json()

	def run_qaqc(self, las_paths):  
		p = pp.ProcessPool()
		print(p)
		p.imap(self.run_qaqc_checks, las_paths)
		p.close()
		p.join()


class QaqcTileCollection:

	def __init__(self, las_paths, qaqc_gdb, qaqc_fd_name, 
			  qaqcd_tile_fc_name, checks_to_do):
		self.las_paths = las_paths
		self.qaqc_gdb = qaqc_gdb
		self.qaqc_fd_name = qaqc_fd_name
		self.qaqc_fd_path = os.path.join(self.qaqc_gdb, self.qaqc_fd_name)
		self.qaqc_tile_fc_name = qaqcd_tile_fc_name
		self.qaqc_tile_fc_path = os.path.join(self.qaqc_fd_path, self.qaqc_tile_fc_name)
		self.checks_to_do = checks_to_do

	def create_qaqc_feature_dataset(self):
		logging.info('making {} in {}...'.format(self.qaqc_fd_name, self.qaqc_gdb))
		try:
			arcpy.CreateFeatureDataset_management(self.qaqc_gdb, self.qaqc_fd_name)
		except Exception as e:
			print(e)

	def create_qaqc_tile_feature_class(self):
		logging.info('making {} in {}...'.format(self.qaqc_tile_fc_name, self.qaqc_fd_path))
		try:
			arcpy.CreateFeatureclass_management(self.qaqc_fd_path, self.qaqc_tile_fc_name)
		except Exception as e:
			print(e)
	
	def run_qaqc_tile_collection_checks(self):
		tiles_qaqc = QaqcTile(self.checks_to_do)
		tiles_qaqc.run_qaqc(self.las_paths)

	#def gen_dz_ortho_mosaic(self):  # TODO
	#	DzOrtho.create_raster_catalog()
	#	DzOrtho.add_dz_dir_to_raster_catalog()
	#	DzOrtho.mosaic_dz_raster_catalog()
	#	DzOrtho.add_dz_mosaic_to_mxd()
	#	DzOrtho.update_raster_symbology()

def run_console_cmd(cmd):
	process = subprocess.Popen(cmd.split(' '))
	output, error = process.communicate()
	returncode = process.poll()
	return returncode, output


def config_settings():

	qaqc_dir = r'C:\QAQC_contract\nantucket'
	qaqc_gdb = r'{}\qaqc_nantucket.gdb'.format(qaqc_dir)
	qaqc_fd_name = 'QAQC_Layers'
	qaqc_fd_path = r'{}\qaqc_nantucket.gdb\{}'.format(qaqc_dir, qaqc_fd_name)
	qaqc_tile_fc_name = r'QAQC_tile_checks'
	las_tile_dir = r'{}\CLASSIFIED_LAS'.format(qaqc_dir)
	
	classification_scheme_dir = r'\\ngs-s-rsd\response_dl\Research\transfer\software\LP360'
	classification_scheme_xml = 'noaa_topobathy_v02.xml'
	classificaiton_scheme_fpath = os.path.join(classification_scheme_dir, classification_scheme_xml)
		
	dz_raster_catalog = r'{}\{}_raster_catalog'.format(qaqc_gdb, 'nantucket') 
	dz_classes_lyr = r'C:\QAQC_contract\dz_classes.lyr'
	dz_export_settings = r'C:\QAQC_contract\\dz_export_settings.xml'
	dz_mxd = r'{}\QAQC_nantucket.mxd'.format(qaqc_dir)
	
	dz_bins = {
		0: (0.00, 0.04, 'darkgreen'),
		1: (0.04, 0.08, 'lightgree'),
		2: (0.08, 0.12, 'cyan'),
		3: (0.12, 0.16, 'yellow'),
		4: (0.16, 0.20, 'orange'),
		5: (0.20, 1000, 'red'),
	}

	checks_to_do = {
		'naming_convention': False,
		'version': False,
		'pdrf': False,
		'gps_time': False,
		'hor_datum': False,
		'ver_datum': False,
		'point_source_ids': False,
        'create_dz': True
	}

	settings = {
		'qaqc_dir': qaqc_dir,
		'qaqc_gdb': qaqc_gdb,
		'qaqc_fd_name': qaqc_fd_name,
		'qaqc_fd_path': qaqc_fd_path,
		'qaqc_tile_fc_name': qaqc_tile_fc_name,
		'las_tile_dir': las_tile_dir,
		'classification_scheme_xml': classification_scheme_xml,
		'dz_raster_catalog': dz_raster_catalog,
		'dz_classes_lyr': dz_classes_lyr,
		'dz_export_settings': dz_export_settings,
		'dz_mxd': dz_mxd,
		'dz_bins': dz_bins,
		'checks_to_do': checks_to_do,
	}

	return settings


def main():
	logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)
	settings = config_settings()

	nantucket = LasTileCollection(settings['las_tile_dir'])

	qaqc = QaqcTileCollection(
        nantucket.get_las_tile_paths(),
		settings['qaqc_gdb'], 
		settings['qaqc_fd_name'], 
		settings['qaqc_tile_fc_name'],
		settings['checks_to_do'])
	#qaqc.create_qaqc_feature_dataset()
	#qaqc.create_qaqc_tile_feature_class()
	qaqc.run_qaqc_tile_collection_checks()

	# summarize QAQC check json results
	# TODO: read json files to make dashboard


if __name__ == '__main__':
	main()












	

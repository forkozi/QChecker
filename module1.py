import Tkinter as tk
import ttk
import threading
import time

import os
import json
import logging
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
from shapely import wkt
import numpy as np
import subprocess
from laspy.file import File
import xml.etree.ElementTree as ET
import arcpy
import pathos.pools as pp
import re
from geodaisy import GeoObject

import Tkinter as tk
import ttk
import time
import threading


class Configuration:
    def __init__(self, config):

        data = None
        with open(config) as f:
            data = json.load(f)

        self.data = data

        self.project_name = arcpy.ValidateTableName(data['project_name'])
        self.las_tile_dir = data['las_tile_dir']
        self.qaqc_dir = data['qaqc_dir']
        self.qaqc_gdb = data['qaqc_gdb']
        self.raster_dir = data['qaqc_gdb']
        self.tile_size = float(data['tile_size'])

        # checks "answer key"
        self.hdatum_key = data['check_keys']['hdatum']
        self.vdatum_key = data['check_keys']['vdatum']
        self.exp_cls_key = [int(n) for n in data['check_keys']['exp_cls'].split(',')]
        self.pdrf_key = data['check_keys']['pdrf']
        self.gps_time_key = data['check_keys']['gps_time']
        self.version_key = data['check_keys']['version']
        self.pt_src_ids_key = data['check_keys']['pt_src_ids']

        self.dz_mxd  = data['dz_mxd']
        self.dz_export_settings = data['dz_export_settings']
        self.dz_classes_template = data['dz_classes_template']

        self.contractor_shp = data['contractor_shp']
        self.checks_to_do = data['checks_to_do']
        self.surfaces_to_make = data['surfaces_to_make']
        self.mosaics_to_make = data['mosaics_to_make']

        self.qaqc_csv = r'{}\qaqc.csv'.format(self.qaqc_dir)
        self.qaqc_geojson_NAD83_UTM_CENTROIDS = r'{}\qaqc_NAD83_UTM_CENTROIDS.json'.format(self.qaqc_dir)
        self.qaqc_geojson_NAD83_UTM_POLYGONS = r'{}\qaqc_NAD83_UTM_POLYGONS.json'.format(self.qaqc_dir)
        self.qaqc_shp_NAD83_UTM_POLYGONS = r'{}\qaqc_NAD83_UTM.shp'.format(self.qaqc_dir)
        self.json_dir = r'{}\qaqc_check_results'.format(self.qaqc_dir)

        self.contractor_geojson_WGS84 = os.path.join(self.qaqc_dir, 'tiles_WGS84.json')
        self.contractor_centroids_shp_NAD83_UTM = os.path.join(self.qaqc_dir, 'tiles_centroids_NAD83_UTM.shp')
        self.contractor_csv = os.path.join(self.qaqc_dir, 'tiles.csv')

    def __str__(self):
        return json.dumps(self.data, indent=4, sort_keys=True)

    @staticmethod
    def run_console_cmd(cmd):
        process = subprocess.Popen(cmd.split(' '))
        output, error = process.communicate()
        returncode = process.poll()
        return returncode, output

class LasTileCollection():

    def __init__(self, las_tile_dir):
        self.las_tile_dir = las_tile_dir
        self.num_las = len(self.get_las_names())

    def get_las_tile_paths(self):
        return [os.path.join(self.las_tile_dir, f) 
          for f in os.listdir(self.las_tile_dir) 
          if f.endswith('.las')]

    def get_las_names(self):
        return [f for f in os.listdir(self.las_tile_dir) if f.endswith('.las')]

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

    def __init__(self, las_path, config):
        self.path = las_path
        self.name = os.path.splitext(las_path.split(os.sep)[-1])[0]
        self.inFile = File(self.path, mode="r")
        self.to_pyramid = True
        self.is_pyramided = os.path.isfile(self.path.replace('.las', '.qvr'))
        self.config = config

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

        def calc_las_centroid():
            data_nw_x = self.las_extents['ExtentXMin']
            data_nw_y = self.las_extents['ExtentYMax']
            las_nw_x = data_nw_x - (data_nw_x % self.config.tile_size)
            las_nw_y = data_nw_y + self.config.tile_size - (data_nw_y % self.config.tile_size)
            las_centroid_x = las_nw_x + self.config.tile_size / 2
            las_centroid_y = las_nw_y - self.config.tile_size / 2
            return (las_centroid_x, las_centroid_y)

        self.header = get_useful_las_header_info()
        self.las_extents = {
            'ExtentXMin': self.header['x_min'],
            'ExtentXMax': self.header['x_max'],
            'ExtentYMin': self.header['y_min'],
            'ExtentYMax': self.header['y_max'],
            }


        self.centroid_x, self.centroid_y = calc_las_centroid()

        self.tile_extents = {
            'tile_top': self.centroid_y + self.config.tile_size / 2,
            'tile_bottom': self.centroid_y - self.config.tile_size / 2,
            'tile_left': self.centroid_x - self.config.tile_size / 2,
            'tile_right': self.centroid_x + self.config.tile_size / 2,
            }

        self.tile_poly_wkt = GeoObject(Polygon([
            (self.tile_extents['tile_left'], self.tile_extents['tile_top']), 
            (self.tile_extents['tile_right'], self.tile_extents['tile_top']), 
            (self.tile_extents['tile_right'], self.tile_extents['tile_bottom']), 
            (self.tile_extents['tile_left'], self.tile_extents['tile_bottom']),
            (self.tile_extents['tile_left'], self.tile_extents['tile_top']), 
            ])).wkt()

        self.tile_centroid_wkt = GeoObject(Point(self.centroid_x, self.centroid_y)).wkt()
        self.classes_present, self.class_counts = self.get_class_counts()
        self.has_bathy = True if 'class26' in self.class_counts.keys() else False
        self.has_ground = True if 'class2' in self.class_counts.keys() else False

        self.checks_result = {
            'naming': None,
            'version': None,
            'pdrf': None,
            'gps_time': None,
            'hdatum': None,
            'vdatum': None,
            'pnt_src_ids': None,
            'exp_cls': None,
        }

        if self.to_pyramid and not self.is_pyramided:
            self.create_las_pyramids()

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

    def output_las_qaqc_to_json(self):
        json_file_name = r'{}\{}.json'.format(self.config.json_dir, self.name)
        with open(json_file_name, 'w') as json_file:
            json_file.write(str(self))

    def get_class_counts(self):
        class_counts = np.unique(self.inFile.classification, return_counts=True)
        classes_present = [c for c in class_counts[0]]
        class_counts = dict(zip(['class{}'.format(str(c)) for c in class_counts[0]],
                                [int(c) for c in class_counts[1]]))
        print(class_counts)
        return classes_present, class_counts

    def get_gps_time(self):
        gps_times = {0: 'GPS Week Time', 1: 'Satellite GPS Time'}
        return gps_times[self.header['global_encoding']]

    def get_las_version(self):
        return '{}.{}'.format(self.header['version_major'], self.header['version_minor'])

    def get_las_pdrf(self):
        return self.header['data_format_id']

    def get_hdatum(self):
        return self.header['VLRs']['coord_sys']

    def create_las_pyramids(self):
        exe = r'C:\Program Files\Common Files\LP360\LDPyramid.exe'
        thin_factor = 12
        cmd_str = '{} -f {} {}'.format(exe, thin_factor, self.path)
        print('generating pyramids for {}...'.format(self.path))
        print(cmd_str)
        try:
            returncode, output = self.config.run_console_cmd(cmd_str)
        except Exception as e:
            print(e)


class Mosaic:

    def __init__(self, mtype, config):
        self.mtype = mtype
        self.config = config
        self.raster_catalog_base_name = r'{}_{}_raster_catalog'.format(self.config.project_name, self.mtype)
        self.raster_catalog_path = r'{}\{}'.format(self.config.qaqc_gdb, self.raster_catalog_base_name)
        self.mosaic_raster_basename = '{}_{}_mosaic'.format(self.config.project_name, self.mtype)
        self.mosaic_raster_path = '{}\{}'.format(self.config.qaqc_gdb, self.mosaic_raster_basename)

    def create_raster_catalog(self):
        logging.info('creating raster catalog {}'.format(self.raster_catalog_base_name))
        try:
            arcpy.CreateRasterCatalog_management(
                self.config.qaqc_gdb, self.raster_catalog_base_name,
                raster_management_type='UNMANAGED')
        except Exception as e:
            print(e)

    def add_dir_to_raster_catalog(self):
        logging.info('adding {}_rasters to {}...'.format(self.mtype, self.raster_catalog_path))
        arcpy.WorkspaceToRasterCatalog_management(self.config.qaqc_gdb, self.raster_catalog_path)

    def mosaic_raster_catalog(self):
        logging.info('mosaicing {} rasters in {}...'.format(self.mtype, self.raster_catalog_path))
        try:
            arcpy.Delete_management(self.mosaic_raster_path)
        except Exception as e:
            pass
        try:
            arcpy.RasterCatalogToRasterDataset_management(self.raster_catalog_path, 
                                                          self.mosaic_raster_path)
        except Exception as e:            
            print(e)

    def add_mosaic_to_mxd(self):
        mxd = arcpy.mapping.MapDocument(self.config.dz_mxd)
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        arcpy.MakeRasterLayer_management(self.mosaic_raster_path, self.mosaic_raster_basename)
        dz_lyr = arcpy.mapping.Layer(self.mosaic_raster_basename)
        try:
            arcpy.mapping.AddLayer(df, dz_lyr, 'AUTO_ARRANGE')
            mxd.save()
        except Exception as e:
            print(e)

    def update_raster_symbology(self):
        mxd = arcpy.mapping.MapDocument(self.config.dz_mxd)
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        raster_to_update = arcpy.mapping.ListLayers(mxd, self.mosaic_raster_basename, df)[0]
        dz_classes_lyr = arcpy.mapping.Layer(self.config.dz_classes_template)
        arcpy.mapping.UpdateLayer(df, raster_to_update, dz_classes_lyr, True)
        try:
            mxd.save()
        except Exception as e:
            print(e)


class Surface:

    def __init__(self, tile, stype, config):
        self.stype = stype
        self.las_path = tile.path
        self.las_name = tile.name
        self.las_extents = tile.las_extents
        self.config = config

        self.binary_path = {'Dz': r'{}\{}_dz_dzValue.flt'.format(self.config.surfaces_to_make[self.stype][1], 
                                                                 self.las_name),
                            'Hillshade': ''}

        self.raster_path = {'Dz': r'{}\dz_{}'.format(self.config.raster_dir, self.las_name),
                            'Hillshade': ''}

    def __str__(self):
        return self.raster_path[self.stype]

    def binary_to_raster(self):
        try:
            logging.info('converting {} to {}...'.format(self.binary_path[self.stype], 
                                                         self.raster_path[self.stype]))
            arcpy.FloatToRaster_conversion(self.binary_path[self.stype], 
                                           self.raster_path[self.stype])
        except Exception as e:
            print(e)

    def update_dz_export_settings_extents(self):
        logging.info('updating dz export settings xml with las extents...')
        tree = ET.parse(self.config.dz_export_settings)
        root = tree.getroot()
        for extent, val in self.las_extents.iteritems():
            for e in root.findall(extent):
                e.text = str(val)
        new_dz_settings = ET.tostring(root)
        myfile = open(self.config.dz_export_settings, "w")
        myfile.write(new_dz_settings)

    def gen_dz_surface(self):
        exe = r'C:\Program Files\Common Files\LP360\LDExport.exe'
        las = self.las_path.replace('CLASSIFIED_LAS\\', 'CLASSIFIED_LAS\\\\')
        dz = r'C:\QAQC_contract\nantucket\dz\{}'.format(self.las_name)
        cmd_str = '{} -s {} -f {} -o {}'.format(exe, self.config.dz_export_settings, las, dz)
        print('generating dz ortho for {}...'.format(las))
        print(cmd_str)
        try:
            returncode, output = self.config.run_console_cmd(cmd_str)
        except Exception as e:
            print(e)

    def gen_hillshade_surface():
        pass


class QaqcTile:

    passed_text = 'PASSED'
    failed_text = 'FAILED'

    def __init__(self, config):
        self.config = config
        self.checks = {
            'naming': self.check_las_naming,
            'version': self.check_las_version,
            'pdrf': self.check_las_pdrf,
            'gps_time': self.check_las_gps_time,
            'hdatum': self.check_hdatum,
            'vdatum': self.check_vdatum,
            'pt_src_ids': self.check_pt_src_ids,
            'exp_cls': self.check_unexp_cls,
            }

        self.surfaces = {
            'Dz': self.create_dz,
            'Dz_mosaic': None,
            'Hillshade': self.create_hillshade,
            'Hillshade_mosaic': None,
            }

    def check_las_naming(self, tile):
        # for now, the checks assume Northern Hemisphere
        # https://www.e-education.psu.edu/natureofgeoinfo/c2_p23.html
        min_easting = 167000
        max_easting = 833000
        min_northing = 0
        max_northing = 9400000
        #min_northing_sh = 1000000 # sh = southern hemisphere
        #max_northing_sh = 10000000

        # first check general format with regex (e.g., # ####_######e_#[#######]n_las)
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
        tile.checks_result['naming'] = tile.name
        tile.checks_result['naming_passed'] = passed
        return passed

    def check_las_version(self, tile):
        version = tile.get_las_version()
        if version == self.config.version_key:
            passed = self.passed_text
        else:
            passed = self.failed_text
        tile.checks_result['version'] = version
        tile.checks_result['version_passed'] = passed
        return passed

    def check_las_pdrf(self, tile):
        pdrf = tile.get_las_pdrf()
        las_version = tile.get_las_version()
        if pdrf == self.config.pdrf_key:
            passed = self.passed_text
        else:
            passed = self.failed_text
        tile.checks_result['pdrf'] = pdrf
        tile.checks_result['pdrf_passed'] = passed
        return passed

    def check_las_gps_time(self, tile):
        gps_time = tile.get_gps_time()
        if gps_time == self.config.gps_time_key:
            passed = self.passed_text
        else:
            passed = self.failed_text
        tile.checks_result['gps_time'] = gps_time
        tile.checks_result['gps_time_passed'] = passed
        return passed

    def check_hdatum(self, tile):  # TODO
        hdatum = tile.get_hdatum()
        if hdatum == self.config.hdatum_key:
            passed = self.passed_text
        else:
            passed = self.failed_text
        tile.checks_result['hdatum'] = hdatum
        tile.checks_result['hdatum_passed'] = passed
        return passed

    def check_unexp_cls(self, tile):
        unexp_cls = list(set(tile.classes_present).difference(self.config.exp_cls_key))
        if not unexp_cls:
            passed = self.passed_text
        else:
            passed = self.failed_text
        tile.checks_result['exp_clas'] = str(unexp_cls)
        tile.checks_result['exp_clas_passed'] = passed
        return passed

    def check_vdatum(self):
        pass

    def check_pt_src_ids(self):
        pass

    def calc_pt_cloud_stats(self):
        pass

    def create_dz(self, tile):
        from qaqc import Surface
        if tile.has_bathy or tile.has_ground:
            tile_dz = Surface(tile, 'Dz', self.config)
            tile_dz.update_dz_export_settings_extents()
            tile_dz.gen_dz_surface()
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
        tile = LasTile(las_path, self.config)
        for c in [k for k, v in self.config.checks_to_do.iteritems() if v]:
            logging.info('running {}...'.format(c))
            result = self.checks[c](tile)
            logging.info(result)
        tile.output_las_qaqc_to_json()

    def run_qaqc_checks(self, las_paths):       
        num_las = len(las_paths)
        #self.progress[1]['maximum'] = num_las
        tic = time.time()
        for i, las_path in enumerate(las_paths):

            #if i == 0:
            #    self.progress[2]['text'] = '{} of {} tiles\n~{} mins remaining'.format(
            #        i+1, num_las, '?')
            #    self.progress[2].update()

            tile = LasTile(las_path, self.config)

            for c in [k for k, v in self.config.checks_to_do.iteritems() if v]:
                logging.info('running {}...'.format(c))
                result = self.checks[c](tile)
                logging.info(result)

            for c in [k for k, v in self.config.surfaces_to_make.iteritems() if v[0]]:
                logging.info('running {}...'.format(c))
                result = self.surfaces[c](tile)
                logging.info(result)

            tile.output_las_qaqc_to_json()

            #time_elapsed = time.time() - tic
            #num_las_remaining = num_las - (i + 1)
            #mean_delta_time = time_elapsed / (i + 1)
            #time_remaining_est = (mean_delta_time * num_las_remaining) / 60.0

            ## update progress bar and label that was passed form qaqc_gui.py
            #self.progress[1]['value'] = i + 1
            #if i + 1 == num_las:
            #    self.progress[2]['text'] = '{} of {} tiles DONE'.format(i+1, num_las)
            #else:
            #    self.progress[2]['text'] = '{} of {} tiles\n~{:.1f} mins remaining'.format(
            #        i+1, num_las, time_remaining_est)

            #self.progress[1].update()
            #self.progress[2].update()

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

    def __init__(self, las_paths, config,):
        self.las_paths = las_paths
        self.config = config

    def run_qaqc_tile_collection_checks(self, multiprocess):
        tiles_qaqc = QaqcTile(self.config)
        tiles_qaqc.run_qaqc(self.las_paths, multiprocess)

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
        for las_json in os.listdir(self.config.json_dir):
            try:
                las_json = os.path.join(self.config.json_dir, las_json)
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

    def gen_qaqc_json_NAD83_UTM_CENTROIDS(self, output):
        gdf = self.gen_qaqc_results_gdf_NAD83_UTM_CENTROIDS()
        try:
            os.remove(output)
        except Exception as e:
            print(e)
        gdf.to_file(output, driver="GeoJSON")

    def gen_qaqc_results_gdf_NAD83_UTM_POLYGONS(self):
        df = self.get_qaqc_results_df()
        df['Coordinates'] = df.tile_polygon
        df['Coordinates'] = df['Coordinates'].apply(wkt.loads)
        nad83_utm_z19 = {'init': 'epsg:26919'}
        gdf = gpd.GeoDataFrame(df, crs=nad83_utm_z19, geometry='Coordinates')		
        return gdf

    def gen_qaqc_json_NAD83_UTM_POLYGONS(self, output):
        gdf = self.gen_qaqc_results_gdf_NAD83_UTM_POLYGONS()
        try:
            os.remove(output)
        except Exception as e:
            print(e)
        gdf.to_file(output, driver="GeoJSON")

    def gen_qaqc_csv(self, output):
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

    def gen_qaqc_shp_NAD83_UTM(self, output):
        gdf = self.gen_qaqc_results_gdf_NAD83_UTM_POLYGONS()
        gdf = gdf.drop(columns=['ExtentXMax','ExtentXMin', 'ExtentYMax', 
                                'ExtentYMin', 'centroid_x', 'centroid_y', 
                                'created_day', 'created_year', 'tile_polygon', 
                                'x_max', 'x_min', 'y_max', 'y_min'])
        print(gdf)
        gdf.to_file(output, driver='ESRI Shapefile')
        sr = arcpy.SpatialReference('NAD 1983 UTM Zone 19N')  # 2011?
        try:
            arcpy.DefineProjection_management(output, sr)
        except Exception as e:
            print(e)
        print(self.config.dz_mxd)
        mxd = arcpy.mapping.MapDocument(self.config.dz_mxd)
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        qaqc_lyr = arcpy.mapping.Layer(output)
        try:
            arcpy.mapping.AddLayer(df, qaqc_lyr, 'TOP')  # add qaqc tile shp
            mxd.save()
        except Exception as e:
            print(e)

    def gen_mosaic(self, mtype):
        mosaic = Mosaic(mtype, self.config)
        mosaic.create_raster_catalog()
        mosaic.add_dir_to_raster_catalog()
        mosaic.mosaic_raster_catalog()
        mosaic.add_mosaic_to_mxd()
        mosaic.update_raster_symbology()

    def gen_tile_geojson_WGS84(shp, geojson):
        wgs84 = {'init': 'epsg:4326'}
        gdf = gpd.read_file(shp).to_crs(wgs84)
        try:
            os.remove(geojson)
        except Exception as e:
            print(e)
        gdf.to_file(geojson, driver="GeoJSON")

    @staticmethod
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

    def gen_tile_centroids_shp_NAD83_UTM(self):
        logging.info('generating shapefile containing centroids of contractor tile polygons...')
        gdf = gpd.read_file(self.config.contractor_shp)
        gdf['geometry'] = gdf['geometry'].centroid
        gdf.to_file(self.config.contractor_centroids_shp_NAD83_UTM, driver='ESRI Shapefile')
        return self.config.contractor_centroids_shp_NAD83_UTM
        #sr = arcpy.SpatialReference('NAD 1983 UTM Zone 19N')  # 2011?
        #arcpy.DefineProjection_management(output, sr)

    def add_layer_to_mxd(self, layer):
        mxd = arcpy.mapping.MapDocument(self.config.dz_mxd)
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        lyr = arcpy.mapping.Layer(layer)
        try:
            arcpy.mapping.AddLayer(df, lyr, 'TOP')
            mxd.save()
        except Exception as e:
            print(e)

class QaqcApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)


        # start button calls the "initialization" function bar_init, you can pass a variable in here if desired
        self.start_button = ttk.Button(self, text='Start bar', command=lambda: self.bar_init(2500))
        self.start_button.pack()

        # the progress bar will be referenced in the "bar handling" and "work" threads
        self.load_bar = ttk.Progressbar(self)
        self.load_bar.pack()

    def bar_init(self, var):
        # first layer of isolation, note var being passed along to the self.start_bar function
        # target is the function being started on a new thread, so the "bar handler" thread
        self.start_bar_thread = threading.Thread(target=self.start_bar, args=(var,))
        
        # start the bar handling thread
        self.start_bar_thread.start()

    def start_bar(self, var):
        # the load_bar needs to be configured for indeterminate amount of bouncing
        self.load_bar.config(mode='indeterminate', maximum=100, value=0)
        
        # 8 here is for speed of bounce
        self.load_bar.start(1)
        
        # start the work-intensive thread, again a var can be passed in here too if desired
        self.work_thread = threading.Thread(target=self.work_task, args=(var,))
        self.work_thread.start()
       
        # close the work thread
        self.work_thread.join()
        
        # stop the indeterminate bouncing
        self.load_bar.stop()
        
        # reconfigure the bar so it appears reset
        self.load_bar.config(value=0, maximum=0)

    def work_task(self, wait_time):
        logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)
    
        config = Configuration('Z:\qaqc\qaqc_config.json')
        print(config)

        #nantucket = LasTileCollection(config.las_tile_dir)
        #qaqc = QaqcTileCollection(nantucket.get_las_tile_paths()[0:20], config)
    
        #if not os.path.isfile(config.contractor_centroids_shp_NAD83_UTM):
        #    tile_centroids = qaqc.gen_tile_centroids_shp_NAD83_UTM()
        #    qaqc.add_layer_to_mxd(tile_centroids)
        #else:
        #    logging.info('{} alread exists'.format(config.contractor_centroids_shp_NAD83_UTM))
    
        #qaqc.run_qaqc_tile_collection_checks(multiprocess=False)
        #qaqc.gen_qaqc_shp_NAD83_UTM(config.qaqc_shp_NAD83_UTM_POLYGONS)
    
        ## build the mosaics the user checked
        #for m in [k for k, v in config.mosaics_to_make.iteritems() if v[0]]:
        #    qaqc.gen_mosaic(k)

        #logging.info('\n\nYAY, you just QAQC\'d project {}!!!\n\n'.format(config.project_name))

        #with open('finish_message.txt', 'r') as f:
        #    message = f.readlines()
        #print(''.join(message))

if __name__ == '__main__':
    app = QaqcApp()
    app.geometry('400x850')
    app.mainloop()  # tk functionality
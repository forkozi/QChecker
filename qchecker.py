import os
import json
import logging
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
from shapely import wkt
import subprocess
from functools import partial
from laspy.file import File

import pdal
import pathos.pools as pp
import pathos.helpers as ph
import multiprocessing as mp

import re
from geodaisy import GeoObject
import ast
import time
from osgeo import osr
from pathlib import Path
from tqdm import tqdm
import rasterio
import rasterio.merge
from rasterio.io import MemoryFile

from bokeh.models.widgets import Panel, Tabs
from bokeh.io import output_file, show
from bokeh.models import (ColumnDataSource, PrintfTickFormatter, 
                          GeoJSONDataSource, Legend, Range1d)
from bokeh.plotting import figure
from bokeh.tile_providers import get_provider, Vendors
from bokeh.palettes import Blues
from bokeh.transform import log_cmap, factor_cmap
from bokeh.layouts import layout, gridplot


logger = logging.getLogger(__name__)


def worker_configurer(queue):
    h = logging.handlers.QueueHandler(queue)
    root = logging.getLogger()
    root.handlers = []
    root.addHandler(h)
    root.setLevel(logging.INFO)


class SummaryPlots:

    def __init__(self, config, qaqc_results_df):
        self.config = config
        self.results_df = qaqc_results_df
        logging.info('qaqc_results_df')
        logging.info(qaqc_results_df)

        with open(self.config.qaqc_geojson_WebMercator_CENTROIDS) as f:
            qaqc_centroids = f.read()
        self.qaqc_centroids = GeoJSONDataSource(geojson=qaqc_centroids)

        with open(self.config.qaqc_geojson_WebMercator_POLYGONS) as f:
            qaqc_polygons = f.read()
        self.qaqc_polygons = GeoJSONDataSource(geojson=qaqc_polygons)

        self.check_labels = {
            'naming_passed': 'Naming Convention',
            'version_passed': 'Version',
            'pdrf_passed': 'Point Data Record Format',
            'gps_time_passed': 'GPS Time Type',
            'hdatum_passed': 'Horizontal Datum',
            'vdatum_passed': 'Vertical Datum',
            'pt_src_ids_passed': 'Point Source IDs',
            'exp_cls_passed': 'Expected Classes'}

        def get_classes_present(fields):
            present_classes = []
            for f in fields:
                if 'class' in f:
                    present_classes.append(f)
            return present_classes

        def get_test_results():
            fields = self.results_df.columns
            test_result_fields = []
            for f in fields:
                if '_passed' in f:
                    test_result_fields.append(f)
            return self.results_df[test_result_fields]

        def get_las_classes():
            with open(self.config.las_classes_json) as lcf:
                las_classes = json.load(lcf)
            
            def find(key, dictionary):
                for k, v in dictionary.items():
                    if k == key:
                        yield v
                    elif isinstance(v, dict):
                        for result in find(key, v):
                            yield result
                    elif isinstance(v, list):
                        for d in v:
                            if isinstance(d, dict):
                                for result in find(key, d):
                                    yield result

            return find('classes', las_classes)

        self.las_classes = {}

        # recurssively consolidate class dictionaries listed in las_classes.json
        for class_list in get_las_classes():
            self.las_classes.update(class_list)

        results = get_test_results()

        # add column for PASSED or FAILED if it's not there 
        # (to make PASS/FAIL plotting easy)
        result_counts = self.results_df[results.columns].apply(pd.Series.value_counts)
        self.result_counts = result_counts.fillna(0).transpose()

        failed = 'FAILED' in self.result_counts.columns
        passed = 'PASSED' in self.result_counts.columns
        not_failed = 'FAILED' not in self.result_counts.columns
        not_passed = 'PASSED' not in self.result_counts.columns

        if not_failed and passed:
            self.result_counts['FAILED'] = 0
        if not_passed and failed:
            self.result_counts['PASSED'] = 0
        if not_failed and not_passed:
            self.result_counts = pd.DataFrame({'FAILED': 0, 
                                               'PASSED': 0}, 
                                              index=['No_Test_Selected'])

        present_classes = get_classes_present(self.results_df.columns)
        self.class_counts = self.results_df[present_classes].sum().to_frame()
        self.class_counts.columns = ['counts']
        self.TOOLS = 'box_zoom,box_select,crosshair,reset,wheel_zoom'

    @staticmethod
    def add_empty_plots_to_reshape(plot_list):
        """len(plot_list) % 3 needs to = 0"""
        len_check_pass_fail_plots = len(plot_list)
        while len_check_pass_fail_plots % 3 != 0:
            p = figure(plot_width=300, plot_height=300)
            p.outline_line_color = None
            p.toolbar.logo = None
            p.toolbar_location = None
            p.xaxis.major_tick_line_color = None
            p.xaxis.minor_tick_line_color = None
            p.yaxis.major_tick_line_color = None
            p.yaxis.minor_tick_line_color = None
            p.xgrid.grid_line_color = None
            p.ygrid.grid_line_color = None
            p.xaxis.major_label_text_font_size = '0pt'
            p.yaxis.major_label_text_font_size = '0pt'
            p.xaxis.axis_line_color = None
            p.yaxis.axis_line_color = None
            p.circle(0, 0, alpha=0.0)
            plot_list.append(p)
            len_check_pass_fail_plots += 1
        return plot_list

    def draw_pass_fail_bar_chart(self):
        source = ColumnDataSource(self.result_counts)
        if source.data['index'][0] != 'No_Test_Selected':
            labels = [f'{self.check_labels[i]}' for i in source.data['index']]
            source.data.update({'labels': labels})

            failed = source.data.get('FAILED')
            passed = source.data.get('PASSED')

            source.data.update({'FAILED_stack': failed + passed})

            cats = ['PASSED', 'FAILED']
            p1 = figure(y_range=source.data['labels'], 
                        title="Check PASS/FAIL Results", 
                        plot_width=400, plot_height=400)
            
            p1.min_border_top = 100
            p1.min_border_bottom = 50

            p1.toolbar.logo = None
            p1.toolbar_location = None

            r_pass = p1.hbar(left=0, right='PASSED', y='labels',  
                             height=0.9, color='#3cb371', 
                             source=source, name='PASSED', line_color=None)

            r_fail = p1.hbar(left='PASSED', right='FAILED_stack', y='labels', 
                             height=0.9, color='#FF0000', 
                             source=source, name='FAILED', line_color=None)

            p1.xgrid.grid_line_color = None

            max_passed = max(passed)
            max_failed = max(failed)
            max_val = max(max_passed, max_failed)

            p1.x_range = Range1d(0, max_val + 0.1 * max_val)
            p1.axis.minor_tick_line_color = None
            p1.outline_line_color = None

            legend = Legend(items=[
                ("PASSED", [r_pass]),
                ("FAILED", [r_fail]),
                ], location=(1, 15))
            p1.add_layout(legend, 'above')
            p1.legend.orientation = "horizontal"
        else:
            p1 = figure(title="No Tests Selected", 
                        plot_width=400, 
                        plot_height=300) 

        return p1

    def draw_class_count_bar_chart(self):

        def check_for_undefined_classes():
            obs_class_nums = [c.replace('class', '') for c in source.data['index']]
            for ocn in obs_class_nums:
                if ocn not in self.las_classes:
                    self.las_classes.update({ocn: 'UNDEFINED'})


        self.class_counts['Expected'] = np.zeros(self.class_counts.index.size)
        self.class_counts['Unexpected'] = np.zeros(self.class_counts.index.size)
        for i, class_name in enumerate(self.class_counts.index):
            class_num = int(class_name.replace('class', ''))
            if class_num in self.config.exp_cls_key:
                self.class_counts['Expected'][i] = self.class_counts['counts'][i]
            else:
                self.class_counts['Unexpected'][i] = self.class_counts['counts'][i]

        source = ColumnDataSource(self.class_counts)
        check_for_undefined_classes()
        source.data.update({'labels': ['{} (Class {})'.format(
            self.las_classes[c.replace('class', '').zfill(2)], 
            c.replace('class', '').zfill(2)) for c in source.data['index']]})

        p2 = figure(y_range=source.data['labels'], 
                    plot_width=400, plot_height=400, 
                    title="Class Counts", tools="")
        p2.min_border_top = 100
        p2.outline_line_color = None
        p2.toolbar.logo = None
        p2.toolbar_location = None
        p2.xaxis[0].formatter = PrintfTickFormatter(format='%4.1e')

        p2_expected = p2.hbar(y='labels', right='Expected', 
                                height=0.9, color='#0074D9', source=source)

        p2_unexpected = p2.hbar(y='labels', right='Unexpected', 
                                height=0.9, color='#FF851B', source=source)

        max_count = max(source.data['counts'])
        self.class_counts = self.class_counts.drop(['counts'], axis=1)
        p2.x_range = Range1d(0, max_count + 0.1 * max_count)
        p2.xgrid.grid_line_color = None
        p2.xaxis.major_label_orientation = "vertical"
        p2.xaxis.minor_tick_line_color = None

        legend = Legend(items=[('EXPECTED', [p2_expected]), 
                               ('UNEXPECTED', [p2_unexpected])], 
                        location=(0, 10))
        p2.add_layout(legend, 'above')

        return p2

    def draw_pass_fail_maps(self):
        check_pass_plots = []
        if self.result_counts.index[0] != 'No_Test_Selected':
            for i, check_field in enumerate(self.result_counts.index):
                title = self.check_labels[check_field]

                if i > 0:
                    p = figure(title=title, 
                               x_axis_type="mercator", 
                               y_axis_type="mercator", 
                               x_range=check_pass_plots[0].x_range,
                               y_range=check_pass_plots[0].y_range,
                               plot_width=300, plot_height=300, 
                               match_aspect=True, tools=self.TOOLS)
                else:
                    p = figure(title=title, 
                               x_axis_type="mercator", 
                               y_axis_type="mercator", 
                               plot_width=300, plot_height=300, 
                               match_aspect=True, tools=self.TOOLS)

                p.toolbar.logo = None

                cmap = {
                    'PASSED': '#3cb371',
                    'FAILED': '#FF0000',
                    }

                color_mapper = factor_cmap(field_name=check_field, 
                                            palette=list(cmap.values()), 
                                            factors=list(cmap.keys()))

                p.add_tile(get_provider(Vendors.CARTODBPOSITRON))
                p.patches('xs', 'ys', source=self.qaqc_polygons, 
                          alpha=0.1, color=color_mapper)
                p.circle(x='x', y='y', size=5, alpha=0.5, 
                         source=self.qaqc_centroids, color=color_mapper)
                
                check_pass_plots.append(p)

        check_pass_plots = self.add_empty_plots_to_reshape(check_pass_plots)
        pass_fail_grid_plot = gridplot(check_pass_plots, ncols=3, 
                                       plot_height=300, 
                                       toolbar_location='right')

        tab1 = Panel(child=pass_fail_grid_plot, title="Checks Pass/Fail")

        return tab1

    def draw_class_count_maps(self):
        min_count = self.results_df[self.class_counts.index].min().min()
        max_count = self.results_df[self.class_counts.index].max().max()
        
        palette = list(Blues[9])
        palette.reverse()

        class_count_plots = []
        for i, class_field in enumerate(self.class_counts.index):

            color_mapper = log_cmap(field_name=class_field, palette=palette, 
                                    low=min_count, high=max_count, 
                                    nan_color='white')

            las_class = class_field.replace('class', '').zfill(2)
            title = f'Class {las_class} ({self.las_classes[las_class]})'

            if i > 0:
                p = figure(title=title,
                           x_axis_type="mercator", y_axis_type="mercator", 
                           x_range=class_count_plots[0].x_range,
                           y_range=class_count_plots[0].y_range,
                           plot_width=300, plot_height=300,
                           match_aspect=True, tools=self.TOOLS)
            else:
                p = figure(title=title,
                           x_axis_type="mercator", y_axis_type="mercator", 
                           plot_width=300, plot_height=300,
                           match_aspect=True, tools=self.TOOLS)

            if int(las_class) in self.config.exp_cls_key:
                title_color = '#0074D9'
            else:
                title_color = '#FF851B'

            p.title.text_color = title_color
            p.toolbar.logo = None

            p.add_tile(get_provider(Vendors.CARTODBPOSITRON))
            p.patches('xs', 'ys', source=self.qaqc_polygons, alpha=0.1)
            p.circle(x='x', y='y', size=5, alpha=0.5, 
                     source=self.qaqc_centroids, color=color_mapper)

            class_count_plots.append(p)

        class_count_plots = self.add_empty_plots_to_reshape(class_count_plots)
        class_count_grid_plot = gridplot(class_count_plots, ncols=3, 
                                         plot_height=300, 
                                         toolbar_location='right')

        tab2 = Panel(child=class_count_grid_plot, title="Class Counts")

        return tab2

    def gen_dashboard(self):
        bars_elements = []
        maps_elements = []
        bars_elements.append(self.draw_pass_fail_bar_chart())
        maps_elements.append(self.draw_pass_fail_maps())
        if self.config.checks_to_do['exp_cls']:
            bars_elements.append(self.draw_class_count_bar_chart())
            maps_elements.append(self.draw_class_count_maps())

        file_name = f'QAQC_DashboardSummary_{self.config.project_name}.html'
        output_file(str(self.config.qaqc_dir / 'dashboard' / file_name))

        tabs = Tabs(tabs=maps_elements)

        l = layout([
            [bars_elements, tabs],
            ])
        show(l)


class Configuration:
    def __init__(self, config):

        data = None
        with open(config) as f:
            data = json.load(f)

        self.data = data
        self.project_dir = Path(data['project_dir'])
        self.project_name = self.project_dir.name
        self.las_tile_dir = Path(data['las_tile_dir'])
        self.qaqc_dir = Path(data['qaqc_dir'])
        self.tile_size = float(data['tile_size'])
        self.to_pyramid = data['to_pyramid']
        self.multiprocess = data['multiprocess']
        self.projects_unc = data['projects_unc']
        self.check_keys = data['check_keys']
        self.hdatum_key = data['check_keys']['hdatum']
        self.vdatum_key = data['check_keys']['vdatum']
        self.exp_cls_key = [int(n) for n in data['check_keys']['exp_cls'].split(',')]
        self.pdrf_key = int(data['check_keys']['pdrf'])
        self.gps_time_key = data['check_keys']['gps_time']
        self.version_key = data['check_keys']['version']
        self.pt_src_ids_key = data['check_keys']['pt_src_ids']
        self.las_classes_json = Path(data['las_classes_json'])
        self.srs_wkts = Path(data['srs_wkts'])
        self.wkts_df = pd.read_csv(self.srs_wkts, index_col=1, header=None)
        self.epsg_code = int(self.wkts_df.loc[self.hdatum_key][0])
        self.crs = {'init': 'epsg:{}'.format(self.epsg_code)}
        self.web_mercator_epsg = {'init': 'epsg:3857'}
        self.wgs84_epsg = {'init': 'epsg:4326'}
        self.checks_to_do = data['checks_to_do']
        self.surfaces_to_make = data['surfaces_to_make']
        self.qaqc_geojson_NAD83_UTM_CENTROIDS = self.qaqc_dir / 'qaqc_NAD83_UTM_CENTROIDS.json'
        self.qaqc_geojson_NAD83_UTM_POLYGONS = self.qaqc_dir / 'qaqc_NAD83_UTM_POLYGONS.json'
        self.qaqc_geojson_WebMercator_CENTROIDS = self.qaqc_dir / 'dashboard' / '{}_qaqc_WebMercator_CENTROIDS.json'.format(self.project_name)
        self.qaqc_geojson_WebMercator_POLYGONS = self.qaqc_dir / 'dashboard' / '{}_qaqc_WebMercator_POLYGONS.json'.format(self.project_name)
        self.qaqc_shp_NAD83_UTM_POLYGONS = self.qaqc_dir / 'tile_results' / '{}_qaqc_NAD83_UTM.shp'.format(self.project_name)
        self.json_dir = self.qaqc_dir / 'tile_results' / 'json'

        if not self.json_dir.exists():
            os.makedirs(self.json_dir)

        self.tile_geojson_WebMercator_POLYGONS = self.qaqc_dir / 'tiles_WebMercator_POLYGONS.json'
        self.tile_shp_NAD83_UTM_CENTROIDS = self.qaqc_dir / 'tiles_centroids_NAD83_UTM.shp'
        #self.epsg_json = Path(data['epsg_json'])

    def __str__(self):
        return json.dumps(self.data, indent=4, sort_keys=True)

        
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


class LasTile:

    def __init__(self, las_path, config):

        def get_useful_las_header_info():
            info_to_get = 'global_encoding,version_major,version_minor,' \
                          'created_day,created_year,data_format_id,' \
                          'x_min,x_max,y_min,y_max'
            header = {}
            for info in info_to_get.split(','):
                header[info] = self.inFile.header.reader.get_header_property(info)           
            self.version = f"{header['version_major']}.{header['version_minor']}"
            return header

        def get_vlrs():
            vlrs = {}
            for i, vlr in enumerate(self.inFile.header.vlrs):
                vlrs.update({vlr.record_id: vlr.parsed_body})
            return vlrs

        def get_srs(las_path):
            try:
                las = str(las_path).replace('\\', '/')
                cmd_str = 'pdal info {} --metadata'.format(las)
                metadata = self.run_console_cmd(cmd_str)[1].decode('utf-8')
                meta_dict = json.loads(metadata)
                srs = meta_dict['metadata']['srs']
                hor_wkt = srs['horizontal']
                ver_wkt = srs['vertical']
                hor_srs=osr.SpatialReference(wkt=hor_wkt)
                ver_srs=osr.SpatialReference(wkt=ver_wkt)   
                hor_srs = hor_srs.GetAttrValue('projcs')
                ver_srs = ver_srs.GetAttrValue('vert_cs')               
            except Exception as e:
                logging.debug(e)
                hor_srs = ver_srs = None

            return hor_srs, ver_srs

        def calc_las_centroid():
            dx = self.las_extents['ExtentXMax'] - self.las_extents['ExtentXMin']
            dy = self.las_extents['ExtentYMax'] - self.las_extents['ExtentYMin']
            #las_nw_x = data_nw_x - (data_nw_x % self.config.tile_size)
            #las_nw_y = data_nw_y + self.config.tile_size - (data_nw_y % self.config.tile_size)
            las_centroid_x = self.las_extents['ExtentXMin'] + dx / 2
            las_centroid_y = self.las_extents['ExtentYMax'] - dy / 2
            return (las_centroid_x, las_centroid_y)

        tic = time.time()

        self.path = las_path
        self.las_str = str(self.path).replace('\\', '/')
        self.name = os.path.splitext(las_path.split(os.sep)[-1])[0]
        self.version = None
        self.has_wkt = None
        self.refraction_bit_set = None
        self.inFile = File(self.path, mode="r")
        self.config = config
        self.is_pyramided = os.path.isfile(self.path.replace('.las', '.qvr'))
        self.to_pyramid = self.config.to_pyramid

        self.header = get_useful_las_header_info()
        self.las_extents = {
            'ExtentXMin': self.header['x_min'],
            'ExtentXMax': self.header['x_max'],
            'ExtentYMin': self.header['y_min'],
            'ExtentYMax': self.header['y_max'],
            }

        self.las_centroid_x, self.las_centroid_y = calc_las_centroid()

        self.las_poly_wkt = GeoObject(Polygon([
            (self.header['x_min'], self.header['y_max']), 
            (self.header['x_max'], self.header['y_max']), 
            (self.header['x_max'], self.header['y_min']), 
            (self.header['x_min'], self.header['y_min']),
            (self.header['x_min'], self.header['y_max']), 
            ])).wkt()

        point = Point(self.las_centroid_x, self.las_centroid_y)
        self.las_centroid_wkt = GeoObject(point).wkt()
        
        self.ground_class = {'1.2': '2', '1.4': '2'}
        self.bathy_class = {'1.2': '26', '1.4': '40'}

        self.checks_result = {
            'naming': None,
            'version': None,
            'pdrf': None,
            'gps_time': None,
            'hdatum': None,
            'vdatum': None,
            'pt_src_ids': None,
            'exp_cls': None,
        }

        self.vlrs = get_vlrs()
        self.hor_srs, self.ver_srs = get_srs(self.path)

        self.info_to_output = {
            'tile_name': self.name,
            'header': self.header,
            'las_extents': self.las_extents,
            'centroid_x': self.las_centroid_x,
            'centroid_y': self.las_centroid_y,
            'check_results': self.checks_result,
            'tile_polygon': self.las_poly_wkt,
            'tile_centroid': self.las_centroid_wkt,
            }

        if self.version == '1.4':
            self.has_wkt = self.inFile.header.get_wkt()

    @staticmethod
    def run_console_cmd(cmd):
        process = subprocess.Popen(cmd.split(' '), 
                                   shell=False, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.DEVNULL)
        output, error = process.communicate()
        returncode = process.poll()
        return returncode, output

    def __str__(self):
        # del keys that are not needed because of repitition
        self.info_to_output['header'].pop('VLRs', None)
        self.info_to_output['header'].pop('version_major', None)
        self.info_to_output['header'].pop('version_minor', None)
        self.info_to_output['header'].pop('global_encoding', None)
        self.info_to_output['header'].pop('data_format_id', None)
        return json.dumps(self.info_to_output, indent=2)

    def output_las_qaqc_to_json(self):
        json_file_name = r'{}\{}.json'.format(self.config.json_dir, self.name)
        with open(json_file_name, 'w') as json_file:
            json_file.write(str(self))

    def get_class_counts(self):
        points = self.inFile.points['point']
        bin_counts = np.bincount(points['raw_classification'])  # or 'classification_byte'
        self.classes_present = np.where(bin_counts > 0)[0]  # i.e., indices
        class_counts = bin_counts[self.classes_present]
        class_labels = [f'class{str(c)}' for c in self.classes_present]
        self.class_counts = dict(zip(class_labels, [int(c) for c in class_counts]))   
        self.info_to_output['class_counts'] = self.class_counts

    def get_gps_time(self):
        gps_times = {0: 'GPS Week Time', 1: 'Satellite GPS Time'}
        bit_num = 0
        global_encoding = self.header['global_encoding']
        bit = int(bin(global_encoding)[2:].zfill(16)[::-1][bit_num])
        return gps_times[bit]

    def get_las_version(self):
        major = self.header['version_major']
        minor = self.header['version_minor']
        return f'{major}.{minor}'

    def get_las_pdrf(self):
        return self.header['data_format_id']

    def get_pt_src_ids(self):
        return np.unique(self.inFile.pt_src_id)

    def get_refraction_bit(self):
        try:
           vlr_104 = self.vlrs['104']
           self.refraction_bit_set = True
        except Exception as e:
            logging.info(e)
            self.refraction_bit_set = 'not_present'


class Mosaic:

    def __init__(self, mtype, config):
        self.mtype = mtype
        self.config = config
        self.stem = f'{self.config.project_name}_{self.mtype}_mosaic'
        self.basename = self.stem + '.tif'
        self.path = Path(self.config.surfaces_to_make[self.mtype][1]) / self.basename

    def gen_mosaic(self, vrts):
        if vrts:
            logging.info(f'generating {self.path}...')
            mosaic, out_trans = rasterio.merge.merge(vrts)
            out_meta = vrts[0].profile  # uses last src made
            out_meta.update({
                'driver': "GTiff",
                'height': mosaic.shape[1],
                'width': mosaic.shape[2],
                'transform': out_trans})

            # save mosaic DEMs
            with rasterio.open(self.path, 'w', **out_meta) as dest:
                dest.write(mosaic)
            for vrt in vrts:
                vrt.close()
        else:
            logging.info('No {self.mtype} tiles were generated.')


class Surface:

    def __init__(self, tile, stype, config):
        self.stype = stype
        self.las_path = tile.path
        self.las_name = tile.name
        self.las_str = tile.las_str
        self.las_extents = tile.las_extents
        self.config = config
        self.tif_dir = Path(self.config.surfaces_to_make[self.stype][1])
        self.tile = tile

    def __str__(self):
        return self.raster_path[self.stype]

    def create_dz_dem(self):
        
        def gen_pipeline(las_bounds):

            ground_class = self.tile.ground_class[self.tile.version]
            bathy_class = self.tile.bathy_class[self.tile.version]

            pdal_json = """{
                "pipeline":[
                    {
                        "type": "readers.las",
                        "filename": """ + '"{}"'.format(self.las_str) + """
                    },
                    {
                        "type":"filters.range",
                        "limits": "Classification[""" + \
                            '{}'.format(ground_class) + """:""" + \
                            '{}'.format(ground_class) + """],Classification[""" + \
                            '{}'.format(bathy_class) + """:""" + \
                            '{}'.format(bathy_class) + """]"
                    },
                    {
                        "type":"filters.returns",
                        "groups":"last,only"
                    },
                    {
                        "type":"filters.groupby",
                        "dimension":"PointSourceId"
                    },
                    {
                        "type": "writers.gdal",
                        "gdaldriver": "GTiff",
                        "output_type": "mean",
                        "resolution": "1.0",
                        "bounds": """ + '"{}",'.format(las_bounds) + """
                        "filename":  """ + '"{}"'.format(self.gtiff_path) + """
                    }
                ]
            }"""

            return pdal_json

        def create_dz():
            tifs = []
            profile = None
            for t in self.tif_dir.glob(f'{self.las_name}*.tif'):
                with rasterio.open(t, 'r') as tif:
                    data = tif.read(1)
                    tifs.append(data)
                    if not profile:
                        profile = tif.profile
                os.remove(t)

            if tifs:
                tifs = np.stack(tifs, axis=0)
                tifs[tifs == -9999] = np.nan
                tifs = np.nanmax(tifs, axis=0) - np.nanmin(tifs, axis=0)
                tifs[(np.isnan(tifs)) | (tifs == 0)] = -9999
                return profile, np.expand_dims(tifs, axis=0)
            else:
                logging.info(f'{self.las_name} has no tifs :(...')

        cmd_str = 'pdal info {} --summary'.format(self.las_str)
        stats = self.tile.run_console_cmd(cmd_str)[1]
        stats_dict = json.loads(stats)

        bounds = stats_dict['summary']['bounds']
        minx = bounds['minx']
        maxx = bounds['maxx']
        miny = bounds['miny']
        maxy = bounds['maxy']
        las_bounds = ([minx ,maxx], [miny, maxy])
        
        self.gtiff_path = self.tif_dir / f'{self.las_name}_PSI_#.tif'
        self.gtiff_path = str(self.gtiff_path).replace('\\', '/')
        
        logging.info('generating {} surface for {}...'.format(self.stype, self.las_name))
        try:
            pipeline = pdal.Pipeline(gen_pipeline(las_bounds))
            __ = pipeline.execute()
        except Exception as e:
            logging.info(e)

        return create_dz()

    def gen_mean_z_surface(self, dem_type):
        ground_class = self.tile.ground_class[self.tile.version]
        bathy_class = self.tile.bathy_class[self.tile.version]

        las_str = str(self.las_path).replace('\\', '/')
        gtiff_path = f'/vsimem/{self.las_name}_{self.stype}.tif'

        pdal_json = """{
            "pipeline":[
                {
                    "type": "readers.las",
                    "filename": """ + '"{}"'.format(las_str) + """
                },
                {
                    "type":"filters.returns",
                    "groups":"last,only"
                },
                {
                    "type":"filters.range",
                    "limits": "Classification[""" + \
                        '{}'.format(ground_class) + """:""" + \
                        '{}'.format(ground_class) + """],Classification[""" + \
                        '{}'.format(bathy_class) + """:""" + \
                        '{}'.format(bathy_class) + """]"
                },
                {
                    "filename": """ + '"{}"'.format(gtiff_path) + """,
                    "gdaldriver": "GTiff",
                    "output_type": """ + '"{}"'.format(dem_type) + """,
                    "resolution": "1.0",
                    "type": "writers.gdal"
                }
            ]
        }"""

        logging.info('generating {} surface for {}...'.format(self.stype, self.las_name))

        try:
            pipeline = pdal.Pipeline(pdal_json)
            count = pipeline.execute()
            self.path = gtiff_path
        except Exception as e:
            logging.info(e)
            self.path = None
            
    def detect_spikes(self):
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
            'DEM': self.create_DEM
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
            easting = int(tile_name_parts[1].replace('e', ''))
            northing = int(tile_name_parts[2].replace('n', ''))



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
        logging.debug(tile.checks_result['naming'])
        return passed

    def check_las_version(self, tile):
        version = tile.get_las_version()
        if version == self.config.version_key:
            passed = self.passed_text
        else:
            passed = self.failed_text
        tile.checks_result['version'] = version
        tile.checks_result['version_passed'] = passed
        logging.debug(tile.checks_result['version'])
        return passed

    def check_refraction_bit(self, tile):
        pass

    def check_las_pdrf(self, tile):
        pdrf = tile.get_las_pdrf()
        if pdrf == self.config.pdrf_key:
            passed = self.passed_text
        else:
            passed = self.failed_text
        tile.checks_result['pdrf'] = pdrf
        tile.checks_result['pdrf_passed'] = passed
        logging.debug(tile.checks_result['pdrf'])
        return passed

    def check_las_gps_time(self, tile):
        gps_time = tile.get_gps_time()
        if gps_time == self.config.gps_time_key:
            passed = self.passed_text
        else:
            passed = self.failed_text
        tile.checks_result['gps_time'] = gps_time
        tile.checks_result['gps_time_passed'] = passed
        logging.debug(tile.checks_result['gps_time'])
        return passed

    def check_hdatum(self, tile):
        hdatum = tile.hor_srs
        if tile.version == '1.4':
            if hdatum == self.config.hdatum_key and tile.has_wkt:
                passed = self.passed_text
            else:
                passed = self.failed_text
        elif tile.version == '1.2':
            if hdatum == self.config.hdatum_key:
                passed = self.passed_text
            else:
                passed = self.failed_text
        else:
            passed = self.failed_text

        tile.checks_result['hdatum'] = str(hdatum)
        tile.checks_result['hdatum_passed'] = passed
        logging.debug(tile.checks_result['hdatum'])
        return passed

    def check_unexp_cls(self, tile):
        tile.get_class_counts()
        unexp_cls = list(set(tile.classes_present).difference(self.config.exp_cls_key))
        if not unexp_cls:
            passed = self.passed_text
        else:
            passed = self.failed_text
        tile.checks_result['exp_cls'] = str(list(unexp_cls))
        tile.checks_result['exp_cls_passed'] = passed
        logging.debug(tile.checks_result['exp_cls'])
        return passed

    def check_vdatum(self, tile):
        vdatum = tile.ver_srs
        if vdatum == self.config.vdatum_key:
            passed = self.passed_text
        else:
            passed = self.failed_text
        tile.checks_result['vdatum'] = str(vdatum)
        tile.checks_result['vdatum_passed'] = passed
        logging.debug(tile.checks_result['vdatum'])
        return passed

    def check_pt_src_ids(self, tile):
        unq_pt_src_ids = tile.get_pt_src_ids()
        if len(unq_pt_src_ids) > 1:
            passed = self.passed_text
        else:
            passed = self.failed_text
        tile.checks_result['pt_src_ids'] = str(list(unq_pt_src_ids))
        tile.checks_result['pt_src_ids_passed'] = passed
        logging.debug(tile.checks_result['pt_src_ids'])
        return passed

    def create_dz(self, tile):
        from qchecker import Surface
        #if tile.has_bathy or tile.has_ground:
        tile_dz = Surface(tile, 'Dz', self.config)
        profile, data = tile_dz.create_dz_dem()
        return profile, data
        #else:
        #    logging.debug(f'{tile.name} has no bathy or ground points; no dz surface generated')
        #    return None

    def create_DEM(self, tile):
        from qchecker import Surface
        #if tile.has_bathy or tile.has_ground:
        tile_DEM = Surface(tile, 'DEM', self.config)
        tile_DEM.gen_mean_z_surface('mean')            
        with rasterio.open(tile_DEM.path) as src:
            data = src.read()
            profile = src.profile
        return profile, data
        #else:
        #    logging.debug('{tile.name} has no bathy or ground points; no DEM generated')
        #    return None

    def run_qaqc_checks_multiprocess(self, las_path):
        from qchecker import LasTile, LasTileCollection
        import logging
        logging.basicConfig(format='%(asctime)s:%(message)s', 
                            level=logging.WARNING)
        tile = LasTile(las_path, self.config)
        for c in [k for k, v in self.config.checks_to_do.items() if v]:
            logging.debug('running {}...'.format(c))
            result = self.checks[c](tile)
            logging.debug(result)
        tile.output_las_qaqc_to_json()

    def run_qaqc_surfaces_multiprocess(self, shared_dict, stype, las_path):
        from qchecker import LasTile, LasTileCollection
        import logging
        logging.basicConfig(format='%(asctime)s:%(message)s', 
                            level=logging.WARNING)
        tile = LasTile(las_path, self.config)

        #tile.get_class_counts()
        #bathy_class = tile.bathy_class[tile.version]
        #ground_class = tile.ground_class[tile.version]
        #tile.has_bathy = True if 'class{}'.format(bathy_class) in tile.class_counts.keys() else False
        #tile.has_ground = True if 'class{}'.format(ground_class) in tile.class_counts.keys() else False

        logging.debug('running {}...'.format(stype))
        profile, data = self.surfaces[stype](tile)
        shared_dict[tile.name] = [profile, data]
        tile.output_las_qaqc_to_json()

    def run_qaqc_checks(self, las_paths):
        p = mp.Pool(processes=max(int(ph.cpu_count() / 2), 1))
        num_las = len(las_paths)
        for _ in tqdm(p.imap_unordered(self.run_qaqc_checks_multiprocess, 
                                       las_paths), 
                      total=num_las, ascii=True):
            pass
        p.close()
        p.join()

    def run_qaqc_surfaces(self, las_paths, stype):
        shared_dict = mp.Manager().dict()
        p = mp.Pool(processes=max(int(ph.cpu_count() / 2), 1))
        num_las = len(las_paths)
        func = partial(self.run_qaqc_surfaces_multiprocess, shared_dict, stype)
        for _ in tqdm(p.imap_unordered(func, las_paths), 
                      total=num_las, ascii=True):
            pass
        p.close()
        p.join()
        return shared_dict


class QaqcTileCollection:

    def __init__(self, las_paths, config,):
        self.las_paths = las_paths
        self.config = config
        self.qaqc_results_df = None

    @staticmethod
    def create_src(v):
        memfile = MemoryFile()
        src = memfile.open(**v[0])
        src.write(v[1])
        return src

    def run_qaqc_tile_collection_checks(self):
        tiles_qaqc = QaqcTile(self.config)
        tiles_qaqc.run_qaqc_checks(self.las_paths)

    def run_qaqc_tile_collection_surfaces(self, stype):
        tiles_qaqc = QaqcTile(self.config)
        tile_surfaces = tiles_qaqc.run_qaqc_surfaces(self.las_paths, stype)
        return tile_surfaces

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
                logging.debug(e)
        return flattened_dicts

    def get_unq_pt_src_ids(self):
        unq_pt_src_ids = set([])
        pnt_src_ids = self.qaqc_results_df['pnt_src_ids'].tolist()
        for i, pnt_src_id_str in enumerate(pnt_src_ids):
            pnt_src_ids_set = set(ast.literal_eval(pnt_src_id_str))
            unq_pt_src_ids = unq_pt_src_ids.union(pnt_src_ids_set)
        return unq_pt_src_ids

    def set_qaqc_results_df(self):
        self.qaqc_results_df = pd.DataFrame(self.gen_qaqc_results_dict())
    
    # todo: refactor these 3 into one maybe?
    def gen_qaqc_results_gdf_NAD83_UTM_CENTROIDS(self):
        df = self.qaqc_results_df
        df['Coordinates'] = df.tile_centroid
        df['Coordinates'] = df['Coordinates'].apply(wkt.loads)
        gdf = gpd.GeoDataFrame(df, crs=self.config.crs, geometry='Coordinates')
        return gdf

    def gen_qaqc_results_gdf_WebMercator_CENTROIDS(self):
        df = self.qaqc_results_df
        df['Coordinates'] = df.tile_centroid
        df['Coordinates'] = df['Coordinates'].apply(wkt.loads)
        gdf = gpd.GeoDataFrame(df, crs=self.config.crs, geometry='Coordinates')
        gdf = gdf.to_crs(self.config.web_mercator_epsg)
        return gdf

    def gen_qaqc_results_gdf_WebMercator_POLYGONS(self):
        df = self.qaqc_results_df
        df['Coordinates'] = df.tile_polygon
        df['Coordinates'] = df['Coordinates'].apply(wkt.loads)
        gdf = gpd.GeoDataFrame(df, crs=self.config.crs, geometry='Coordinates')
        gdf = gdf.to_crs(self.config.web_mercator_epsg)
        return gdf

    def gen_qaqc_json_NAD83_UTM_CENTROIDS(self, output):
        gdf = self.gen_qaqc_results_gdf_NAD83_UTM_CENTROIDS()
        try:
            os.remove(output)
        except Exception as e:
            logging.debug(e)
        gdf.to_file(output, driver="GeoJSON")

    def gen_qaqc_json_WebMercator_CENTROIDS(self):
        output = self.config.qaqc_geojson_WebMercator_CENTROIDS
        gdf = self.gen_qaqc_results_gdf_WebMercator_CENTROIDS()
        try:
            os.remove(output)
        except Exception as e:
            logging.debug(e)
        gdf.to_file(output, driver="GeoJSON")
        return output

    def gen_qaqc_json_WebMercator_POLYGONS(self):
        output = self.config.qaqc_geojson_WebMercator_POLYGONS
        gdf = self.gen_qaqc_results_gdf_WebMercator_POLYGONS()
        try:
            os.remove(output)
        except Exception as e:
            logging.debug(e)
        gdf.to_file(output, driver="GeoJSON")

    def gen_qaqc_results_gdf_NAD83_UTM_POLYGONS(self):
        df = self.qaqc_results_df
        df['Coordinates'] = df.tile_polygon
        df['Coordinates'] = df['Coordinates'].apply(wkt.loads)
        gdf = gpd.GeoDataFrame(df, crs=self.config.crs, geometry='Coordinates')		
        return gdf

    def gen_qaqc_json_NAD83_UTM_POLYGONS(self, output):
        gdf = self.gen_qaqc_results_gdf_NAD83_UTM_POLYGONS()
        try:
            os.remove(output)
        except Exception as e:
            logging.debug(e)
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
        logging.debug('creating shp of qaqc results...')
        gdf = self.gen_qaqc_results_gdf_NAD83_UTM_POLYGONS()
        gdf = gdf.drop(columns=['ExtentXMax','ExtentXMin', 'ExtentYMax', 
                                'ExtentYMin', 'centroid_x', 'centroid_y', 
                                'created_day', 'created_year', 'tile_polygon', 
                                'x_max', 'x_min', 'y_max', 'y_min'])

        schema = gpd.io.file.infer_schema(gdf)
        gdf.to_file(output, driver='ESRI Shapefile', schema=schema)

    def gen_mosaic(self, mtype, vrts):
        mosaic = Mosaic(mtype, self.config)
        mosaic.gen_mosaic(vrts)

    def gen_tile_geojson_WGS84(shp, geojson):
        gdf = gpd.read_file(shp).to_crs(self.config.wgs84_epsg)
        try:
            os.remove(geojson)
        except Exception as e:
            logging.debug(e)
        gdf.to_file(geojson, driver="GeoJSON")

    @staticmethod
    def gen_tile_centroids_csv(shp, out_csv):
        gdf = gpd.read_file(shp)
        gdf['geometry'] = gdf['geometry'].centroid
        def get_x(pt): return (pt.x)
        def get_y(pt): return (pt.y)
        gdf['centroid_x'] = map(get_x, gdf['geometry'])
        gdf['centroid_y'] = map(get_y, gdf['geometry'])
        gdf = gdf.to_crs(self.config.wgs84_epsg)
        gdf['geometry'] = gdf['geometry'].centroid
        gdf['centroid_lon'] = map(get_x, gdf['geometry'])
        gdf['centroid_lat'] = map(get_y, gdf['geometry'])
        gdf.to_csv(out_csv)

    def gen_tile_geojson_WebMercator_POLYGONS(self, geojson):
        gdf = gpd.read_file(self.config.contractor_shp)
        try:
            os.remove(geojson)
        except Exception as e:
            logging.debug(e)

        gdf = gdf.to_crs(self.web_mercator_epsg)
        gdf.to_file(geojson, driver="GeoJSON")


def run_qaqc(config_json):
    config = Configuration(config_json)
    
    logging.info('-' * 50)
    logging.info('Ignore the following laspy-generated warning, which doesn\'t effect Q-Checker:')
    logging.info('WARNING: Invalid body length for classification lookup, not parsing.')
    logging.info('It has to do with the self.rec_len_after_header attribute of VLR record_id 0.')
    logging.info('(self.rec_len_after_header % 16 != 0)')
    logging.info('-' * 50)

    qaqc_tile_collection = LasTileCollection(config.las_tile_dir)
    qaqc = QaqcTileCollection(qaqc_tile_collection.get_las_tile_paths()[0:], config)

    logging.info(config.checks_to_do)
    if any(list(config.checks_to_do.values())):    
        qaqc.run_qaqc_tile_collection_checks()
        qaqc.set_qaqc_results_df()
        qaqc.gen_qaqc_shp_NAD83_UTM(config.qaqc_shp_NAD83_UTM_POLYGONS)
        qaqc.gen_qaqc_json_WebMercator_CENTROIDS()
        qaqc.gen_qaqc_json_WebMercator_POLYGONS()

        dashboard = SummaryPlots(config, qaqc.qaqc_results_df)
        dashboard.gen_dashboard()  
    else:
        logging.info('no checks are selected')

    # build the surfaces the user checked
    surface_types = [k for k, v in config.surfaces_to_make.items() if v[0]]
    logging.info(surface_types)
    for stype in surface_types:
        logging.info(f'building {stype} mosaic...')
        tile_surfaces = qaqc.run_qaqc_tile_collection_surfaces(stype)
        vrts = [qaqc.create_src(v) for k, v in tile_surfaces.items()]
        qaqc.gen_mosaic(stype, vrts)

    logging.info('YAY, you just QAQC\'d project {}!!!'.format(config.project_name).upper())

    
if __name__ == '__main__':
    pass

from pathlib import Path
import pdal
import rasterio
import rasterio.merge
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np
import json
import subprocess


def get_directories():
    #in_dir = Path(input('Enter tpu las directory:  '))
    #out_dir = Path(input('Enter results diretory:  '))

    in_dir = Path(r'V:\FL1607\lidar\CLASSIFIED_LIDAR')
    out_dir = Path(r'V:\FL1607\lidar\QAQC\hillshade\hillshade_tiles')

    return in_dir, out_dir


def get_tile_dems(dem_type):
    dems = []
    for dem in list(out_dir.glob('*_Hillshade.tif'.format(dem_type.upper()))):
        print('retreiving {}...'.format(dem))
        src = rasterio.open(dem)
        dems.append(src)

    out_meta = src.meta.copy()  # uses last src made

    return dems, out_meta

        
def gen_mosaic(dems, out_meta):
    mosaic_path = str(out_dir / '{}_DEM.tif'.format(dem_type.upper()))
    print('generating {}...'.format(mosaic_path))
    mosaic, out_trans = rasterio.merge.merge(dems)

    out_meta.update({
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_trans})

    # save TPU mosaic DEMs
    with rasterio.open(mosaic_path, 'w', **out_meta) as dest:
        dest.write(mosaic)
    
    return mosaic


def gen_pipline(las_str, pt_src_id, gtiff_path):


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
                "limits": """ + '"PointSourceId[{}:{}]"'.format(pt_src_id, pt_src_id) + """
            },
            {
                "filename": """ + '"{}"'.format(gtiff_path) + """,
                "gdaldriver": "GTiff",
                "output_type": "mean",
                "resolution": "1.0",
                "type": "writers.gdal",
            }
        ]
    }"""
    print(pdal_json)

    return pdal_json


def create_dz_dem(las):

    pt_src_id_dems = []

    las_str = str(las).replace('\\', '/')
    pt_src_ids = get_pt_src_ids(las)
    for psi in pt_src_ids:
        print('making mean Z DEM for pt_src_id {}...'.format(psi))
        gtiff_path = out_dir / '{}_{}.tif'.format(las.stem, psi)
        gtiff_path = str(gtiff_path).replace('\\', '/')

        try:
            pipeline = pdal.Pipeline(gen_pipline(las_str, psi, gtiff_path))
            count = pipeline.execute()

            with rasterio.open(gtiff_path, 'r') as dem:
                pt_src_id_dems.append(dem.read(1))

        except Exception as e:
            print(e)

        dem_stack = np.vstack(pt_src_id_dems)
        print(dem_stack.shape)


def run_console_cmd(cmd):
    process = subprocess.Popen(cmd.split(' '), shell=False, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    output, error = process.communicate()
    returncode = process.poll()
    return returncode, output


def get_pt_src_ids(las):
    options = [
            '--stats',
            '--filters.stats.dimensions=PointSourceId',
            '--filters.stats.enumerate=PointSourceId'
            ]

    cmd_str = 'pdal info {} {} {} {}'.format(las, *options)
    stats = run_console_cmd(cmd_str)[1].decode('utf-8')
    stats_dict = json.loads(stats)

    print(stats_dict)
    
    return stats_dict['stats']['statistic'][0]['values']


def gen_summary_graphic(mosaic, dem_type):
    fig = plt.figure(figsize=(7, 4))
    fig.suptitle('Standard Deviation DEM (DZ Surface Alternative)\n{}'.format('Eglin_Santa_Rosa_Island'))
    plt.subplots_adjust(left=0.15)

    gs = GridSpec(1, 2, width_ratios=[4, 1], height_ratios=[1], wspace=0.3)
    ax0 = fig.add_subplot(gs[0, 1])
    ax1 = fig.add_subplot(gs[0, 0])

    mosaic_stats = [np.nanmin(mosaic), np.nanmax(mosaic), 
                    np.nanmean(mosaic), np.nanstd(mosaic)]
    mosaic_stats = np.asarray([mosaic_stats]).T

    stats = ['min', 'max', 'mean', 'std']
    ax0.axis('tight')
    ax0.axis('off')
    ax0.table(cellText=mosaic_stats.round(3), colLabels=[dem_type], 
              rowLabels=stats, bbox=[0, 0, 1, 1])

    count, __, __ = ax1.hist(mosaic.ravel(), bins=np.arange(0, mosaic_stats[1], 0.01), 
                             color='gray')

    ax1.set(xlabel='meters', ylabel='Count')
    ax1.set_xlim(0, mosaic_stats[2] + 10 * mosaic_stats[3])

    #plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    dem_type = 'mean'
    las_dir, out_dir = get_directories()

    # generate individual tile DEMs
    for las in list(las_dir.glob('*.las'))[0:5]:
        

        create_dz_dem(las)

    ## mosaic tile DEMs
    #dems, out_meta = get_tile_dems(dem_type)
    #mosaic = gen_mosaic(dems, out_meta)
    #gen_summary_graphic(mosaic, dem_type)

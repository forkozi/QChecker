import laspy
from collections import OrderedDict
import os
import math
import json

xy_data_type = 7  # 10 = laspy unsigned long long (8 bytes)
z_data_type = 5  # 5 = laspy unsigned long (4 bytes)
tpu_data_type = 5

extra_byte_dimensions = OrderedDict([
    ('cblue_x', ('calculated x', xy_data_type)),
    ('cblue_y', ('calculated y', xy_data_type)),
    ('cblue_z', ('calculated z', z_data_type)),
    ('subaerial_thu', ('subaerial thu', tpu_data_type)),
    ('subaerial_tvu', ('subaerial tvu', tpu_data_type)),
    ('subaqueous_thu', ('subaqueous thu', tpu_data_type)),
    ('subaqueous_tvu', ('subaqueous tvu', tpu_data_type)),
    ('total_thu', ('total thu', tpu_data_type)),
    ('total_tvu', ('total tvu', tpu_data_type))
    ])

#las_dir = r'Z:\martha_las_test'
drives = 'Y'
las_dir = r'Y:\2018\FL1815-TB-N_880_Keys_Blks_S_U_p\FL1815-TB-N_880_Keys_Blks_S_U_02_p\06_RIEGL_PROC\04_EXPORT\GR\02_FL1815_BLKS_S_U_02_g_gpsa_rf_ip_wsf_r'

#for drive in drives:
#    las_dir = '{}:\\'.format(drive)
#for root, dirs, files in os.walk(las_dir):
#    print(root)
#    print(len(files))

with open('LAS_v14.txt', 'r') as f:
    line = f.readline()

    while line:


#for name in files:
#    if name.endswith('S1_181005_141008_Record261_Line237.las'):
            
        try:
            #las_file = os.path.join(root, name)

            print('-' * 80)
            las_file = line.split('|')[1].strip()
            print(las_file)
            inFile = laspy.file.File(las_file, mode="r")

            headerformat = inFile.header.header_format
   
            print(inFile.header.get_wkt())

            version_major = inFile.header.reader.get_header_property('version_major')
            version_minor = inFile.header.reader.get_header_property('version_minor')
            version = r'v{}.{}'.format(version_major, version_minor)

            vlrs = {}
            for i, vlr in enumerate(inFile.header.vlrs):
                data = {vlr.record_id: vlr.parsed_body}
                vlrs.update(data)

            for k, v in vlrs.items():
                print('{}\n{}\n'.format(k, v))

            geotiff_info = {}
            key_entries = list(vlrs[34735])  # GeoKeyDirectoryTag
            nth = 4
            keys = [key_entries[nth*i:nth*i+nth] for i in range(0, int(math.ceil(len(key_entries)/nth)))]
            # KeyEntry = {KeyID, TIFFTagLocation, Count, Value_Offset}
            for key in keys:
                new_key = {
                    key[0]: {
                        'TIFFTagLocation': key[1],
                        'Count': key[2],
                        'Value_Offset': key[3],
                        }
                    }
                print(new_key)
                geotiff_info.update(new_key)

            vcs_keys = [4096, 4097]
            contains_vcs_info = any(key in geotiff_info.keys() for key in vcs_keys)


            #if not contains_vcs_info:
            #    with open('LAS_no_ver_cs.txt', 'a') as f:
            #        line_to_write = '{} | {} | {}\n'.format(version, contains_vcs_info, las_file)
            #        print(line_to_write)
            #        f.write(line_to_write)

            #if version == 'v1.4':
            #    with open('LAS_v14.txt', 'a') as f:
            #        line_to_write = '{} | {}\n'.format(version, las_file)
            #        print(line_to_write)
            #        f.write(line_to_write)

            ## get epsg json data
            #epsg_json_file = r'Z:\qaqc\epsg_lut.json'
            #with open(epsg_json_file) as f:
            #    epsgs = json.load(f)

            #hor_key_id = 3072  # ProjectedCSTypeGeoKey
            #hor_srs_epsg = str(geotiff_info[hor_key_id]['Value_Offset'])
            #hor_srs = epsgs[hor_srs_epsg]
            #print(hor_srs)

            ##ver_key_id = 4096  # VerticalCSTypeGeoKey           
            #ver_key_id = 4097  # VerticalCitationGeoKey
            #start_i = geotiff_info[ver_key_id]['Value_Offset']
            #end_i = start_i + geotiff_info[ver_key_id]['Count']
            #ver_datum = vlrs[34737][0].decode('utf-8')[start_i:end_i-1]
            #print(ver_datum)

            ##point_records = inFile.points
            ##print(point_records.dtype)

            ## for dim in extra_byte_dimensions:
            ##     print(dim),
            ##     print(inFile.reader.get_dimension(dim))

            ##print inFile.extra_bytes

        except Exception as e:
            pass
        
        line = f.readline()

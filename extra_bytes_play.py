import laspy
from collections import OrderedDict
import os

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

las_dir = r'Z:\martha_las_test'
#las_dir = r'C:\QAQC_contract\nantucket\CLASSIFIED_LAS'
las_tile = 'Z:/martha_las_test/mhw/2016_374000e_4594000n_las.las'
las_tile = 'C:/QAQC_contract/nantucket/CLASSIFIED_LAS/2016_399500e_4574000n_las.las'

#for root, dirs, files in os.walk(las_dir):
#    for name in files:
#        las_file = os.path.join(root, name)

#        if las_file.endswith('.las'):

inFile = laspy.file.File(las_tile, mode="r")
headerformat = inFile.header.header_format

#for spec in headerformat:
#    print(spec.name),
#    print(inFile.header.reader.get_header_property(spec.name))
    
header = {}
header['VLRs'] = {}
#print('{}{} has {} VLR(s){}'.format('#' * 20, os.path.join(*las_file.split('\\')[-2:]), len(inFile.header.vlrs), '#' * 20))
for i, vlr in enumerate(inFile.header.vlrs):
    print('{}VLR {} (Record ID {}) {}'.format('-' * 10, i, vlr.record_id, '-' * 10))
    print(vlr.body_summary())
    print(vlr.parsed_body)

#point_records = inFile.points
#print(point_records.dtype)

# for dim in extra_byte_dimensions:
#     print(dim),
#     print(inFile.reader.get_dimension(dim))

#print inFile.extra_bytes


import laspy
from collections import OrderedDict
import os
import math
import json


las_dir = r'X:/2017/FL1606-TB-N-880_DeSoto_to_BocaGrande_p/FL1606-TB-N-880_DeSoto_to_BocaGrande_01_p/06_RIEGL_PROC/04_EXPORT/Green/02_FL1606_DeSoto_Sarasota_01_g_gpsa_rf_ip_wsf_r'
os.chdir(las_dir)


for las in [f for f in os.listdir(las_dir)if f.endswith('.las')][0:1]:

    inFile = laspy.file.File(las, mode = "r")

    #Lets take a look at the header also.
    headerformat = inFile.header.header_format
    for spec in headerformat:
        print(spec.name, inFile.header.reader.get_header_property(spec.name))

    for i, vlr in enumerate(inFile.header.vlrs):
        print('-' * 30)
        print(vlr.record_id)
        print(vlr.parsed_body)
        
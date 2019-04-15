import json

epsg_file = r'Z:\qaqc\epsg_lut.csv'
epsg_json_file = r'Z:\qaqc\epsg_lut.json'

epsgs = {}
with open(epsg_file, 'r') as f:
    line = f.readline().strip()
    while line:
        line = line.split(',')
        epsgs.update({int(line[0]): line[1]})
        line = f.readline().strip()

with open(epsg_json_file, 'w') as f:
    json.dump(epsgs, f)
import os
import laspy


las_dir = r'V:\VA1803\Lidar\Classified_LAS\delivery02'

for root, dirs, files in os.walk(las_dir):
    for name in files:
        if name.endswith('.las'):
            las_file = os.path.join(root, name)
            inFile = laspy.file.File(las_file, mode="r")
            for i, vlr in enumerate(inFile.header.vlrs):
                print({vlr.record_id: vlr.parsed_body})
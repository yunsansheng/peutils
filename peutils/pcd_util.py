# -*- coding: UTF-8 -*-

'''
Author: vincent yao
Date: 2023/5/23
Short Description:

Change History:

'''
import numpy as np
import plyfile


# common ply convert pcd tool
def ply2pcd(ply_file_path, compression="binary"):
    with open(ply_file_path, "rb") as ff:
        plydata = plyfile.PlyData.read(ff)

    metadata = dict()
    metadata["version"] = "0.7"
    metadata["fields"] = [prop.name for prop in plydata["vertex"].properties]
    metadata["size"] = [int(val_dtype[1]) for val_dtype in [prop.val_dtype for prop in plydata["vertex"].properties]]
    metadata["type"] = [val_dtype[0].upper() for val_dtype in [prop.val_dtype for prop in plydata["vertex"].properties]]
    metadata["count"] = " ".join("1" * len(plydata["vertex"].properties))
    metadata["width"] = len(plydata["vertex"])
    metadata["height"] = 1
    metadata["points"] = metadata["width"] * metadata["height"]
    metadata["viewpoint"] = [0, 0, 0, 1, 0, 0, 0]
    metadata["data"] = compression

    points_data = np.array([plydata['vertex'][prop.name] for prop in plydata["vertex"].properties]).T

    return metadata, points_data

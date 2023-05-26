# -*- coding: UTF-8 -*-

'''
Author: vincent yao
Date: 2023/5/23
Short Description:

Change History:

'''
import numpy as np
import plyfile
from pypcd import pypcd


# common ply convert pcd tool
def ply2pcd(ply_file_path, compression="binary"):
    with open(ply_file_path, "rb") as ff:
        plydata = plyfile.PlyData.read(ff)

    prop_names = [prop.name for prop in plydata["vertex"].properties]
    prop_val_dtypes = [prop.val_dtype for prop in plydata["vertex"].properties]

    metadata = dict()
    metadata["version"] = "0.7"
    metadata["fields"] = prop_names
    metadata["size"] = [int(val_dtype[1]) for val_dtype in prop_val_dtypes]
    metadata["type"] = [val_dtype[0].upper() for val_dtype in prop_val_dtypes]
    metadata["count"] = " ".join("1" * len(plydata["vertex"].properties))
    metadata["width"] = len(plydata["vertex"])
    metadata["height"] = 1
    metadata["points"] = metadata["width"] * metadata["height"]
    metadata["viewpoint"] = [0, 0, 0, 1, 0, 0, 0]
    metadata["data"] = compression

    points_data = np.array([plydata['vertex'][prop.name] for prop in plydata["vertex"].properties]).T
    result_pc = pypcd.PointCloud(metadata, points_data)
    return result_pc


# common merge pcds tool
def merge_pcds(pcd_paths):
    metadata = new_pc_data = None
    for pcd_path in pcd_paths:
        pc = pypcd.PointCloud.from_path(pcd_path)
        if not metadata:
            metadata = pc.get_metadata()
        else:
            metadata["points"] += pc.get_metadata()["points"]
            metadata["width"] += pc.get_metadata()["width"]

        if new_pc_data is None:
            new_pc_data = pc.pc_data
        else:
            new_pc_data = np.concatenate((new_pc_data, pc.pc_data), axis=0)

    result_pc = pypcd.PointCloud(metadata, new_pc_data)
    return result_pc

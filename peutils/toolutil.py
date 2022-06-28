# -*- coding: UTF-8 -*-

'''
Author: Henry Wang
Date: 2021-09-18 13:09
Short Description:

Change History:

'''
import numpy as np
from scipy.spatial.transform import Rotation

def remove_key_if_exists(info_dict: dict, rm_list: list):
    for rm_name in rm_list:
        if rm_name in info_dict:
            del info_dict[rm_name]
    return info_dict


def get_name_without_suffix_from_path(path_like, ignore=False):
    # print(path_like)
    name = path_like.split("/")[-1]
    if ignore == False:
        assert name.count(".") == 1, "文件名存在多个.后缀或者没有.，请确认处理方式"
        name_without_suffix = name.split(".")[0]
    else:
        name_without_suffix = '.'.join(name.split(".")[:-1])
    return name_without_suffix


def get_abs_cube_points_list(*args,quaternion, position, dimension):
    '''
       0 # # # # # # # #5
      #-               ##
     # -              # #
    1 # # # # # # # #4  #
    #  2 - - - - - - - -7
    # -              # #
    #-               # #
    3 # # # # # # #  6
    '''
    l = dimension["x"]  # 长
    w = dimension["y"]  # 宽
    h = dimension["z"] # 高

    position_arr = np.array([position["x"],
                              position["y"],
                              position["z"]])

    ### 物体相对于中心点的坐标
    p0 = np.array([-w / 2, l / 2, h / 2])
    p1 = np.array([-w / 2, -l / 2, h / 2])
    p2 = np.array([-w / 2, l / 2, -h / 2])
    p3 = np.array([-w / 2, -l / 2, -h / 2])
    p4 = np.array([w / 2, -l / 2, h / 2])
    p5 = np.array([w / 2, l / 2, h / 2])
    p6 = np.array([w / 2, -l / 2, -h / 2])
    p7 = np.array([w / 2, l / 2, -h / 2])

    ### 计算旋转矩阵
    m1 = Rotation.from_quat([
        quaternion["x"],
        quaternion["y"],
        quaternion["z"],
        quaternion["w"],
    ]).as_matrix()

    ###根据中心点进行矩线性变换，并且加上原来中心点位置得到空间坐标点位置
    point_arr = np.array([
        np.dot(m1, p0) + position_arr,
        np.dot(m1, p1) + position_arr,
        np.dot(m1, p2) + position_arr,
        np.dot(m1, p3) + position_arr,
        np.dot(m1, p4) + position_arr,
        np.dot(m1, p5) + position_arr,
        np.dot(m1, p6) + position_arr,
        np.dot(m1, p7) + position_arr,
    ])
    #### 保留6为小数
    point_arr = np.around(point_arr,6)
    # print(point_arr.tolist())
    return point_arr


# print(get_abs_cube_points(quaternion={"x":0,"y":0,"z":-0.7071067811865475,"w":0.7071067811865476},
#                     dimension = {"x":4.343,"y":2.123,"z":1,},position={"x":1.2344,"y":1,"z":1}))

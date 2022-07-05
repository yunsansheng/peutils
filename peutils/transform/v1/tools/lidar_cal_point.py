# -*- coding: UTF-8 -*-

'''
Author: Henry Wang
Date: 2022-07-05 14:36
Short Description:

Change History:

'''
from peutils.transform.v1.tools.lidar import get_abs_cube_points_list

import numpy as np
import open3d as o3d
from peutils.transform.v1.base import deco_execution_time


def array_to_pointcloud(np_array):
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(np_array)
    return pcd

# def _data_trans(data):
#     lst = []
#     for num in data:
#         num_list = num.split()
#         lst.append([eval(i) for i in num_list])
#     lst.pop()
#     return lst
#
# def load_data_txt(path):
#     file = open(path, 'r')
#     data = file.read().split('\n')
#     lst = _data_trans(data)
#     return lst

def conv_hull(points: np.ndarray):
    """
    生成凸包 参考文档：https://blog.csdn.net/io569417668/article/details/106274172
    :param points: 待生成凸包的点集
    :return: 索引 list
    """
    pcl = array_to_pointcloud(points)
    hull, lst = pcl.compute_convex_hull()
    return lst
    # '''
	# 这里的load_data_txt是我自己写的函数，主要是读入三维点坐标，返回list
	# array_to_point_cloud是用来把NdArray类型的点坐标转换成o3d.geometry.PointCloud类型的函数
    # '''

@deco_execution_time
def in_convex_polyhedron(points_set: np.ndarray, test_points: np.ndarray,x_range,y_range,z_range):
    """
    检测点是否在凸包内
    :param points_set: 凸包，需要对分区的点进行凸包生成 具体见conv_hull函数
    :param test_points: 需要检测的点 可以是多个点
    :return: bool类型
    """
    assert type(points_set) == np.ndarray
    assert type(test_points) == np.ndarray
    # bol = np.zeros((test_points.shape[0], 1), dtype=np.bool)
    bol = []
    ori_set = points_set
    ori_edge_index = conv_hull(ori_set)
    ori_edge_index = np.sort(np.unique(ori_edge_index))

    for i in range(test_points.shape[0]):
        # print(test_points[i])
        p = test_points[i]
        if (p[0]< x_range[0] or p[0]>x_range[1]) \
               or  (p[1]< y_range[0] or p[1]>y_range[1])  \
               or  (p[2]< z_range[0] or p[2]>z_range[1]) :
            bol.append(False)
            continue

        new_set = np.concatenate((points_set, test_points[i, np.newaxis]), axis=0)
        new_edge_index = conv_hull(new_set)
        new_edge_index = np.sort(np.unique(new_edge_index))
        # print(new_edge_index,ori_edge_index)
        # bol[i] = (new_edge_index.tolist() == ori_edge_index.tolist())
        bol.append(new_edge_index.tolist() == ori_edge_index.tolist())
    return bol


if __name__ == '__main__':
    # test1
    # A = np.array([[0, 0, 0], [0, 0, 1], [0, 1, 0], [0, 1, 1],
    #               [1, 0, 0], [1, 0, 1], [1, 1, 0], [1, 1, 1]])

    # p = np.array([[.5, .5, .5], [.2, .3, .6], [1, 1, 1.1]])
    # print(in_convex_polyhedron(A, p))  # True True False

    from peutils import pcd_py3
    import numpy as np

    position = {
        "x": 14.261273256231854,
        "y": 5.648096363559942,
        "z": -1.2077789711217282
    }
    dimension = {
        "x": 4.2,
        "y": 1.8,
        "z": 1.6
    }

    points8 = get_abs_cube_points_list(
        quaternion= {
            "x": 0,
            "y": 0,
            "z": -0.7071067811865475,
            "w": 0.7071067811865476
          }
        ,
        position=position,
        dimension= dimension
    )
    max_l = max(dimension.values())/2
    x_range = tuple([position["x"]-max_l,position["x"] +max_l])
    y_range = tuple([position["y"]-max_l,position["y"] +max_l])
    z_range = tuple([position["z"]-max_l,position["z"] +max_l])
    # print(max_l)
    # x_range =


    # print(points8)


    dt = pcd_py3.PointCloud.from_path("/Users/hwang2/Downloads/release_bundle_center_128_lidar-8_camera_pcd_txt_2022_04_14_icu30_HP-30-V71-AC-021_center_128_lidar_scan_data_1649928997301941.pcd")
    points_iter = ((p["x"], p["y"], p["z"]) for p in dt.pc_data)
    point_list = np.array(list(points_iter), dtype="float32")

    out_rs = in_convex_polyhedron(points8,point_list,x_range,y_range,z_range)


    print("outrs",len([x for x in out_rs if x ]))



    ## 中心点，分别加上，长宽高的最长的一边，
    ## 中心点x y z 分别+- 长宽高最长一边的一半， 先判断，如果 x,y ,z 都不在这个区间内，那么点不在框内
    ## 不满足上面判断的时候，再用剩余的点再用上面的方法进行一轮计算，得出再框内的点有哪些



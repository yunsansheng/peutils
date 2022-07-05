# -*- coding: UTF-8 -*-

'''
Author: Henry Wang
Date: 2022-06-29 13:08
Short Description:

Change History:

'''
import numpy as np
from scipy.spatial.transform import Rotation

def get_abs_cube_points_list(*args,quaternion, position, dimension):
    '''
    平台上看物体的方向，默认视角下，红色y 超做

    平台默认坐标系下， x(蓝色) 朝前， y(红色) 朝左， z(绿色) 朝上。对于空间中的点顺序信息应该下面这样的表示
    ## 矩形框的8个点是这样的，注意坐标系! 这个坐标系y朝左的
       0 # # # # # # # #5
      #-               ##
     # -              # #
    1 # # # # # # # #4  #
    #  2 - - - - - - - -7
    # -              # #
    #-               # #
    3 # # # # # # #  6

    注意仅用于平台的坐标检查和平台的映射，使用在其他场景下，注意坐标系可能是不一样的
    '''
    l = dimension["y"]  # 注意这里换了!
    w = dimension["x"]  # 注意这里换了!
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
    # print(point_arr.tolist())
    # print( np.around(point_arr,6))
    return point_arr


#### 平台的内参是p






#
# reflect_p = np.array([   #内参
#         [
#             1008.1225510456396, 0, 950.3588419440797, 0
#         ],
#         [
#             0,1006.7553649514471, 494.18050876561534,  0
#         ],
#         [
#             0,
#             0,
#             1,
#             0
#         ]
#     ])
#
# reflect_t = np.array([  # extrinsic 外参
#         [
#             0.01918035167711185, -0.9997238513378927, 0.01357700908423043, 0.0638903133639305
#         ],
#         [
#             0.005652852030982758,  -0.01347085648209917, -0.9998932849507265, -0.11562536332370445
#         ],
#         [
#             0.9998000596986669, 0.019255053668314093,  0.005392915238738749, -0.209613714252867
#         ],
#         [
#             0,
#             0,
#             0,
#             1
#         ]
# ])


def lidar_pos_to_camera_pos(*args, lidar_pos, external_arr):
    '''
    ### 用于3D坐标系下的点云位置，转到相机坐标系的三维位置
    '''
    camera_pos = np.dot(external_arr, np.array([
        [ lidar_pos[0]], [ lidar_pos[1]], [ lidar_pos[2]], [1]
    ]))
    return [camera_pos[0][0],camera_pos[1][0],camera_pos[2][0]]

# camera_pos = lidar_pos_to_camera_pos(lidar_pos =[12.620720042768912, 3.6885788192013638,1],external_arr=reflect_t)
# print("camera_pos",camera_pos)  # [-3.368023051808521, -1.0938639012445723, 12.48499963630992]



def camera_pos_to_image_loc(*args,camera_pos,internal_arr,adapter=None):
    '''
        ####用于将相机坐标系转到2D
        # 先通过上面的方法拿到相机坐标系
        # 再计算图像中的平面位置
        "p": [
            [
                cam_fx, 0 , cam_cx, 0
            ],
            [
                0 , cam_fy, cam_cy, 0
            ],
            [
                0, 0, 1, 0
            ]
        ]
        ix = fx * x / z + cx + 0.5
        iy = fy * y / z + cy + 0.5
    '''
    fx = internal_arr[0][0]
    fy = internal_arr[1][1]
    cx = internal_arr[0][2]
    cy = internal_arr[1][2]

    # print(fx, fy, cx, cy)

    ix = fx * camera_pos[0] / camera_pos[2] + cx + 0.5
    iy = fy * camera_pos[1] / camera_pos[2] + cy + 0.5
    if adapter is None:
        return  (ix, iy)
    else:
        return ( adapter(ix) , adapter(iy) )


# image_locate = camera_pos_to_image_loc(camera_pos=[-3.368023051808521, -1.0938639012445723, 12.48499963630992],internal_arr=reflect_p)
# print("image_locate",image_locate)  # [678.9020866475078, 406.47439076926906]



def lidar_pos_to_camera_loc(*args,lidar_pos,internal_arr,external_arr,adapter=None):
    camera_pos = lidar_pos_to_camera_pos(lidar_pos=lidar_pos,external_arr=external_arr)
    image_locate = camera_pos_to_image_loc(camera_pos=camera_pos,internal_arr=internal_arr,adapter=adapter)
    return image_locate

# image_locate2 = lidar_pos_to_camera_loc(lidar_pos=[12.620720042768912, 3.6885788192013638,1],internal_arr=reflect_p,external_arr=reflect_t)
# print("image_locate from lidar pos",image_locate2)


# def point_to_img2():
#     import cv2
#     img = cv2.imread(f"/Users/hwang2/Desktop/frm_d9ac3fbf-458d-34f2-b7fa-5c939fa19ff0.jpeg")
#     point_size = 10
#     point_color = (0, 0, 255)  # BGR
#     thickness = -1
#
#     points8 = get_abs_cube_points_list(
#         quaternion ={
#             "x": 0,
#             "y": 0,
#             "z": 0.7071067811865476,
#             "w": -0.7071067811865475
#           }
#         ,
#         position = {
#             "x": 12.620720042768912,
#             "y": 3.6885788192013638,
#             "z": 1
#           },
#         dimension = {
#             "x": 2.5147194754442883,
#             "y": 5.5304166242425215,
#             "z": 2
#           }
#     )
#     for idx,p in enumerate(points8):
#         img_loc = lidar_pos_to_camera_loc(lidar_pos=p,internal_arr=reflect_p,external_arr=reflect_t,adapter=lambda i :int(i))
#         print(img_loc)
#         # cv2.circle(img, img_loc, point_size, point_color, thickness)
#         cv2.putText(img, str(idx), img_loc, cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
#     cv2.imshow('URL2Image', img)
#     cv2.waitKey()
#
# point_to_img2()
#

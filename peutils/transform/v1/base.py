# -*- coding: UTF-8 -*-

'''
Author: Henry Wang
Date: 2022-05-30 13:08
Short Description:

Change History:

'''

import requests
from requests.adapters import HTTPAdapter
import inspect

def get_session(retry=3):
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=retry))
    session.mount('https://', HTTPAdapter(max_retries=retry))

    return session


def dict_adapter(d:dict,out_adapter=None, rename:dict=None):
    d = {k: v for k, v in d.items()}
    if out_adapter is not None:
        if inspect.isfunction(out_adapter):
            for k,v in d.items():
                d[k] = out_adapter(v)
        elif isinstance(out_adapter,dict):
            for key, out_func in out_adapter.items():
                d[key] = out_func(d[key])
        else:
            raise Exception("参数必须是函数或者字典. 如果是字典，那么就是对应的值是方法")

    if rename is not None:
        ## 重写一遍所有的，但是这边不能有原来存在过的键，否则会冲突
        if len(set(rename.values()) & set(d.keys())) > 0:
            raise Exception("新的名称不能存在之前的名称中")
        else:
            d = {rename.get(k, k): v for k, v in d.items()}
    return d





#
# class SturctMixIn():
#     def to_dict(self, out_adapter_dict=None, rename_dict=None):
#         data = {k: v for k, v in self.__dict__.items()}  # 重新创建字典
#
#         #### 如果没有的话
#         if out_adapter_dict is not None:
#             for key, ad_func in out_adapter_dict.items():
#                 data.update({key: ad_func(data[key])})
#         ### 重命名
#         if rename_dict is not None:
#             data = {rename_dict.get(k, k): v for k, v in data.items()}
#         return data

#
# class Struct(SturctMixIn):
#     def __init__(self,**entries):
#         self.__dict__.update(entries)
#
#     def __repr__(self):
#         return repr(self.__dict__)
#
#
#
# class XYZ(SturctMixIn):
#     __slots__ = ["x", "y", "z"]
#
#     def __init__(self,d, adapter=None):
#         if adapter is None:
#             self.x = d["x"]
#             self.y = d["y"]
#             self.z = d["z"]
#         else:
#             self.x = adapter(d["x"])
#             self.y = adapter(d["y"])
#             self.z = adapter(d["z"])
#
#     def __repr__(self):
#         return f"x:{self.x} ,y:{self.y} ,z:{self.z}"
#
#
# class XYZW(SturctMixIn):
#     __slots__ = ["x", "y", "z", "w"]
#
#     def __init__(self, d, adapter=None):
#         if adapter is None:
#             self.x = d["x"]
#             self.y = d["y"]
#             self.z = d["z"]
#             self.w = d["w"]
#         else:
#             self.x = adapter(d["x"])
#             self.y = adapter(d["y"])
#             self.z = adapter(d["z"])
#             self.w = adapter(d["w"])
#
#     def __repr__(self):
#         return f"x:{self.x} ,y:{self.y} ,z:{self.z}, w:{self.w}"




class Lidar3dObj():
    def __init__(self, frameNum, id, number, category, position, rotation, dimension,
                 lidar_attr=None, quaternion=None,pointCount=None):
        self.frameNum = frameNum
        self.id = id
        self.number = number
        self.category = category
        self.position = position
        self.rotation = rotation
        self.dimension = dimension

        self.lidar_attr = lidar_attr  # 属性
        self.quaternion = quaternion
        self.pointCount = pointCount

    def __repr__(self):
        return f"{self.id} {self.category} {self.number}"


### type

class Lidar3dImageRect():
    def __init__(self, frameNum,imageNum, id, number, category, position, dimension,
                 img_attr=None):
        self.frameNum = frameNum
        self.imageNum = imageNum
        self.id = id
        self.number = number
        self.category = category
        self.position = position
        self.dimension = dimension
        self.bbox =self.get_bbox()

        self.img_attr = img_attr  # 属性

    def get_bbox(self):
        return ["min_x","min_y","w","h"]

    def __repr__(self):
        return f"{self.id} {self.category} {self.number} {self.imageNum}"


class CommonBaseMixIn():
    session = get_session(3)


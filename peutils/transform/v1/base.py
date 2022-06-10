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
import json
from peutils.textutil import gen_uuid

def get_session(retry=3):
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=retry))
    session.mount('https://', HTTPAdapter(max_retries=retry))

    return session

# print(inspect.isbuiltin(int))

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
            raise Exception(f"新的名称不能存在之前的名称中 {repr(set(rename.values()) & set(d.keys()))}")
        else:
            d = {rename.get(k, k): v for k, v in d.items()}
    return d

from peutils.pcd_py3 import PointCloud
import numpy as np

def get_pointlist_from_path(path,fltype=None,dtype=None):
    # path可以是当时标注的点云对应文件，也可以是客户标注的对应文件，如果是客户的文件，我们要注意是否有去过Nan点，这种需要补点.
    # path可以是url 也可以是路径

    if fltype not in ("pcd","bin"):
        raise Exception("fltype必须是pcd或者bin类型")
    if fltype =="bin":
        if dtype is None:
            raise Exception("bin文件必须指定数据类型")

    if fltype =="bin":
        bin_data = np.fromfile(path,dtype=dtype)
        return bin_data
    elif fltype =="pcd":
        dt = PointCloud.from_path(path)
        return dt.pc_data

def get_pointlist_from_url(session,url,fltype=None,dtype=None):

    if fltype not in ("pcd","bin"):
        raise Exception("fltype必须是pcd或者bin类型")
    if fltype =="bin":
        if dtype is None:
            raise Exception("bin文件必须指定数据类型")

    bin_r = session.get(url, stream=True)
    if fltype == "bin":
        bin_data = np.frombuffer(bin_r.content, dtype=dtype)
        bin_r.close()
        return bin_data  # np的一维数组
    elif fltype == "pcd":
        dt = PointCloud.from_buffer(bin_r.content)
        bin_r.close()
        return dt.pc_data  # 通过 x y z 等取数据

'''
ss = get_session()
p_list = get_pointlist_from_url(ss,"https://appen-storage.oss-cn-shanghai.aliyuncs.com/humor_3d/bucket-dataengine/release/preparation/card_data/icu30/data_label_preprocess/619c8ea93842dacdbf91b66e/center_128_lidar/1636006959490492.pcd",
                                    fltype="pcd")
for p in p_list:
    print(p["x"],p["y"],p["z"],p["intensity"])

p_list = get_pointlist_from_path("/Users/hwang2/Downloads/1636006959490492.pcd",fltype="pcd")
for p in p_list:
    print(p["x"],p["y"],p["z"],p["intensity"])

p_array = get_pointlist_from_url(ss,"https://projecteng.oss-cn-shanghai.aliyuncs.com/haomo_3d/segmentation/20210602/HDR006_60b0599b50eb3fa074e490d9_3034_QA/point_cloud/bin_v1/1620539160100000.bin",
            fltype="bin",dtype="float32")
p_array = get_pointlist_from_path("/Users/hwang2/Downloads/1620539160100000.bin", fltype="bin",dtype="float32")
print(p_array[:10])

'''

### 不兼容老的Plss模版，只兼容新的模版.
### 都存在的 id, msg, category(可选). number(可选). frameNum(可选，如果单帧就是0)
class ErrorUnit():
    def __init__(self,id,message,category=None,number=None,frameNum=None,block=True):
        self.id = id
        self.message = message
        self.category = category
        self.number = number
        self.frameList = self.get_frameList(frameNum)
        self.bock = block

    def get_frameList(self,frameNum):
        if frameNum is None:
            return [0]
        elif isinstance(frameNum,int):
            return [frameNum]
        elif isinstance(frameNum,list):
            return list(frameNum)
        else:
            raise Exception(f"不正确的frameNum定义 {frameNum}")

    def __repr__(self):
        if self.frameList !=[0]:
            err_str = f"帧:{self.frameList} ID:{self.id} Message:{self.message} "
        else:
            err_str = f"ID:{self.id} Message:{self.message} "

        if self.category!="":
            err_str += f"物体:{self.category} {self.number}"

        return err_str

'''
平台错误的格式
'''

class ErrorMsgLogV1():

    def __init__(self):
        self.error_list = []

    def create_error(self,msg,obj=None,frameNum=None,block=True):
        if obj is None:
            self.error_list.append(ErrorUnit(
                id = "common-" + gen_uuid(),
                message= msg,
                category="",
                number="",
                frameNum=frameNum,
                block=block
            ))
        else:
            self.error_list.append(ErrorUnit(
                id = obj.id,
                message = msg,
                category = obj.category,
                number = obj.number,
                frameNum=obj.frameNum,
                block=block
            ))


    def fomart_error_str(self)->str:
        return json.dumps([repr(e) for e in self.error_list],ensure_ascii=False)
        # 如果frame是0，不打印。

    def format_a9_error_str(self)->str:
        # 平台只接受id,message,frames,block四个属性。
        return json.dumps([{
            "id": e.id,
            "message": e.message,
            "frames":e.frameList,
            "block":e.block
        } for e in self.error_list],ensure_ascii=False)




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

    def to_dict(self):
        _data_dict = {
            "frameNum":self.frameNum,
            "id":self.id,
            "number":self.number,
            "category":self.category,
            "position":self.position,
            "rotation":self.rotation,
            "dimension":self.dimension,
            "labels":json.dumps(self.lidar_attr,ensure_ascii=False),
        }
        return _data_dict


class Lidar3dImageRect():
    def __init__(self, frameNum,imageNum, id, number,type, category, position, dimension,
                 img_attr=None):
        self.frameNum = frameNum
        self.imageNum = imageNum # 图像的次序。从0开始
        self.id = id
        self.number = number
        self.type = type
        self.category = category
        self.position = position
        self.dimension = dimension

        self.img_attr = img_attr  # 属性

        self.bbox =self.get_bbox()


    def get_bbox(self):
        # xmin ymin w h
        return [
            self.position["x"],self.position["y"],
            self.dimension["x"],self.dimension["y"]
        ]

    def to_dict(self):
        _data_dict = {
            "type":self.type,
            "id":self.id,
            "number":self.number,
            "category":self.category,
            "position":self.position,
            "dimension":self.dimension,
            "labels":json.dumps(self.img_attr,ensure_ascii=False),
        }
        return _data_dict

    def __repr__(self):
        return f"{self.id} {self.category} {self.number} {self.imageNum}"


'''
categoryColor一般为空不要用，
'''
class ImgInstance():
    def __init__(self,id,category,number,categoryName,categoryColor,ist_attr):
        # self.frameNum = frameNum  # frameNum用子物体的
        self.id = id
        self.category = category
        self.categoryName = categoryName
        self.number = number
        # self.categoryColor = categoryColor
        self.ist_attr = ist_attr
        self.obj_list = []

    def __repr__(self):
        return f"{self.id} {self.category} {self.number} {len(self.obj_list)}T"



class Img2Dobj():
    def __init__(self,instance:ImgInstance,
                 frameNum,id,number,category,
                 displayName, color,
                 shapeType,shape,order,img_attr,
                 isOCR=None,OCRText=""
                 ):
        self.instance = instance
        self.frameNum = frameNum
        self.id = id
        self.category = category
        self.displayName = displayName
        self.number = number
        self.color = color
        self.shapeType = shapeType
        self.shape = shape
        self.order = order
        self.img_attr = img_attr
        self.isOCR = isOCR
        self.OCRText = OCRText

    def __repr__(self):
        return f"F{self.frameNum} {self.id} {self.category} {self.number} {self.shapeType} Order:{self.order} <-[{self.instance.category}]"




# type points 点,polyline 线
# pointCount 最好根据数组长度重新算下
# 点云分割只有实例模式
'''
pointsLabels
[ 
    [
       12.747154235839844,
       5.126907825469971,
       -1.3931894302368164,
       86
    ],
    ...
]
'''

class LidarPointObj():
    def __init__(self,frameNum ,id,category,number,points,point_attr,pointsLabels,pointCount,type):
        self.frameNum = frameNum
        self.id = id
        self.category = category
        self.number = number
        self.points = points
        self.point_attr = point_attr
        self.pointsLabels = pointsLabels # 这个是点的 坐标和反射率信息的数组
        self.pointCount = pointCount
        self.type = type  # 平台工具多变形，笔刷，单点，都是point,折线是polyline

    def __repr__(self):
        return f"{self.id} {self.category} {self.number} {len(self.points)}P"

class LidarPointPolyline():
    def __init__(self, frameNum, imageNum, id, number, type, category, points,
                 img_attr=None):
        self.frameNum = frameNum
        self.imageNum = imageNum  # 图像的次序。从0开始
        self.id = id
        self.number = number
        self.type = type
        self.category = category
        self.points = points
        self.img_attr = img_attr  # 属性


    def to_dict(self):
        _data_dict = {
            "type": self.type,
            "id": self.id,
            "number": self.number,
            "category": self.category,
            "points": self.points,
            "labels": json.dumps(self.img_attr, ensure_ascii=False),
        }
        return _data_dict

    def __repr__(self):
        return f"{self.id} {self.category} {self.number} {self.imageNum}"


class CommonBaseMixIn():
    session = get_session(3)

    def get_raw_data(self,url):
        rs =  self.session.get(url).json()
        return rs


import math
def gen_format_progress_seq(total,split_part=10):
    ###初始化
    total = total # 总的数量
    split_part = split_part # 分片数量
    every_part_num = math.ceil(total/split_part) # 总打印的分片数量

    finish = 0  # 当前完成的数量
    finish_part = 0 # 分配开始的进度数量
    # 分片数量，假如 总量是102，分片是10
    def update(step=1):
        nonlocal finish,finish_part
        finish += step # 每调用一次 加1
        if finish//every_part_num >finish_part and finish//every_part_num <=split_part:
            finish_part+=1 # 分片数量加 1
            print( "[",("*"*finish_part).ljust(split_part,"_") ,"]" )
        # 根据完成数量update进度
    return update

import time
def deco_execution_time(func):
    def wrapper(*args, **kw):
        t_begin = time.time()
        res = func(*args, **kw)
        t_end = time.time()

        if t_end - t_begin < 60:
            print('%s executed in %s (s)' % (func.__name__, round(t_end - t_begin,2)) )
        elif t_end -t_begin <3600:
            print('%s executed in %s (min)' % (func.__name__, round((t_end - t_begin)/60, 2)))
        else:
            print('%s executed in %s (h)' % (func.__name__, round((t_end - t_begin) /3600, 2)))

        return res

    return wrapper

def remove_key_if_exists(info_dict: dict, rm_list: list):
    for rm_name in rm_list:
        if rm_name in info_dict:
            del info_dict[rm_name]

    return info_dict
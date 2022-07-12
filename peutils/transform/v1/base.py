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
from typing import Dict, List,Union


class DotDict(dict):
    def __init__(self,*args,**kwargs):
        super(DotDict, self).__init__(*args,**kwargs)

    def __getattr__(self, key):
        value = self[key]
        if isinstance(value,dict):
            value = DotDict(value)
        return value

# print(json.dumps(DotDict()))
# print(json.dumps(a))
# print(a["a"])
# a = DotDict()
# a["a"] = 1
#
# print(a)
# print(bool(DotDict()))

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


### 不兼容老的Plss模版，只兼容新的模版.
### 都存在的 id, msg, category(可选). number(可选). frameNum(可选，如果单帧就是0)
class ErrorUnit():
    def __init__(self,id,message,category=None,number=None,frameNum:Union[List[int],int,None]=None,block=True):
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
            err_str = f"帧:{[x+1 for x in self.frameList]} ID:{self.id} Message:{self.message} "
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

    def create_error(self,msg,obj=None,frameNum:Union[List[int],int,None]=None,block=True):
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
        return "\n".join([repr(e) for e in self.error_list])
        # 如果frame是0，不打印。

    def format_a9_error_str(self)->str:
        # 平台只接受id,message,frames,block四个属性。
        return json.dumps([{
            "id": e.id,
            "message": e.message,
            "frames": e.frameList,
            "blockSubmit": e.block
        } for e in self.error_list],ensure_ascii=False)




class Lidar3dObj():
    def __init__(self, frameNum, id, number, category, position, rotation, dimension,
                 lidar_attr=None, quaternion=None,pointCount=None):
        self.frameNum = frameNum
        self.id = id
        self.number = number
        self.category = category
        self.position = DotDict(position)
        self.rotation = DotDict(rotation)
        self.dimension = DotDict(dimension)

        self.lidar_attr = DotDict(lidar_attr) if lidar_attr else DotDict() # 属性
        self.quaternion = DotDict(quaternion) if quaternion else DotDict()
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
            "labels":"" if self.lidar_attr else json.dumps(self.lidar_attr,ensure_ascii=False),
        }
        return _data_dict



class Lidar3dImageRect():
    def __init__(self, frameNum, id, number,type, category, position, dimension,imageNum=None,
                 img_attr=None,points=None,rect1=None,rect2=None):
        '''
        VANISH_CUBE 灭点立体框才有points
        RECT_CUBE: 前后矩形框组成的立体框 只有这个才有rect1,rect2
        '''
        self.frameNum = frameNum
        self.imageNum = imageNum # 图像的次序。从0开始
        self.id = id
        self.number = number
        self.type = type
        self.category = category
        self.position = DotDict(position)
        self.dimension = DotDict(dimension)

        self.img_attr = DotDict(img_attr) if img_attr else DotDict()  # 属性

        self.points = points
        self.rect1 = rect1
        self.rect2 = rect2

        self.bbox =self.get_bbox()


    def get_bbox(self):
        # xmin ymin w h
        return [
            self.position["x"],self.position["y"],
            self.dimension["x"],self.dimension["y"]
        ]

    def get_dig_points(self):
        '''
        对角线点，左上角点和右下角点,2*2 数组
        '''
        if self.type !='rectangle':
            raise Exception("非矩形框请不要使用对角坐标")
        else:
            return [
                [self.position["x"], self.position["y"]],
                [self.position["x"] + self.dimension["width"], self.position["y"] + self.dimension["height"]]
            ]

    def to_dict(self):
        _data_dict = {
            "type":self.type,
            "id":self.id,
            "number":self.number,
            "category":self.category,
            "position":self.position,
            "dimension":self.dimension,
            "labels":"" if self.img_attr else json.dumps(self.img_attr,ensure_ascii=False),
        }
        if self.type =="VANISH_CUBE":
            if self.points is None:
                raise Exception("灭点必须提供points")
            _data_dict["points"] = self.points

        if self.type =="RECT_CUBE":
            if self.rect1 is None or self.rect2 is None:
                raise Exception("RECT_CUBE 必须提供rect1和rect2")
            _data_dict["rect1"] = self.rect1
            _data_dict["rect2"] = self.rect2

        return _data_dict

    def __repr__(self):
        return f"{self.id} {self.category} {self.number} {self.imageNum}"




'''
categoryColor一般为空不要用，
'''
class ImgInstance():
    def __init__(self,id,category,number,categoryName=None,ist_attr=None):
        # self.frameNum = frameNum  # frameNum用子物体的，因为一个实例会存在于连续真的多个数据中
        self.id = id
        self.category = category
        self.categoryName = categoryName
        self.number = number
        # self.categoryColor = categoryColor # 不用这个属性
        self.ist_attr = DotDict(ist_attr) if ist_attr else DotDict()
        self.obj_list = []

    def __repr__(self):
        return f"{self.id} {self.category} {self.number} {len(self.obj_list)}T"

    def to_pre_dict(self):
        _pre_data_dict = {
            "id":self.id,
            "category":self.category,
            "number": self.number,
            "attributes":self.ist_attr,
            "children":[
            ]
        }

        ## 计算child_dict
        child_dict = dict()
        for item in self.obj_list:
            child_id = item.id
            if child_id not in child_dict:
                child_dict[child_id] = {
                    "id": item.id,
                    "name": item.category,
                    "number": item.number,
                    "cameras": [{
                        "camera": "default",
                        "frames": []
                    }]
                }
            ## 添加这条数据到frames信息中
            child_dict[child_id]["cameras"][0]["frames"].append({
                "frameIndex": item.frameNum,
                "isKeyFrame": True,
                "shapeType": item.shapeType,
                "shape": item.shape,
                "order": item.order,
                "attributes": item.img_attr
            })
        for _,v in child_dict.items():
            _pre_data_dict["children"].append(v)
        return  _pre_data_dict




class Img2Dobj():
    def __init__(self,instance:ImgInstance,
                 frameNum,id,number,category,
                 shapeType,order=None,shape=None,img_attr=None,
                 displayName="", color="",
                 isOCR=None,OCRText=None
                 ):
        self.instance = instance
        self.frameNum = frameNum
        self.id = id
        self.category = category
        self.displayName = displayName
        self.number = number
        self.color = color
        self.shapeType = shapeType
        self.shape = DotDict(shape) if shape else DotDict()
        self.order = order
        self.img_attr = DotDict(img_attr) if img_attr else DotDict()
        self.isOCR = isOCR
        self.OCRText = OCRText


    def get_bbox(self):
        # xmin ymin w h

        if self.shapeType !='rectangle':
            raise Exception("非矩形框请不要使用bbox")
        else:
            return [
                self.shape["x"], self.shape["y"],
                self.shape["width"], self.shape["height"]
            ]

    def get_dig_points(self):
        '''
        对角线点，左上角点和右下角点,2*2 数组
        '''
        if self.shapeType !='rectangle':
            raise Exception("非矩形框请不要使用对角坐标")
        else:
            return [
                [self.shape["x"], self.shape["y"]],
                [self.shape["x"] + self.shape["width"], self.shape["y"] + self.shape["height"]]
            ]


    def __repr__(self):
        return f"F{self.frameNum} {self.id} {self.category} {self.number} {self.shapeType} Order:{self.order} <-[{self.instance.category}]"


class AudioCutObj():
    def __init__(self,frameNum,id,number,start,end,block_attr,line_contents,category=""):
        self.frameNum = frameNum
        self.id = id
        self.number = number
        self.category = category
        self.start = start
        self.end = end
        self.block_attr = DotDict(block_attr) if block_attr else DotDict()
        self.line_contents = line_contents # 对应content字段

    def __repr__(self):
        return f"{self.id} {self.category} {self.number} {self.start} {self.end}"


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
            "labels": "" if self.img_attr is None else json.dumps(self.img_attr, ensure_ascii=False),
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
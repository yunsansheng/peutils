#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: echai
Date: 2024-12-20
Short Description: 
Change History: 
"""
import sys
import os
import json
import time
import math
import re
import oss2
import inspect
from peutils.ossutil import OSS_STS_API
from peutils.textutil import gen_uuid
from peutils.transform.v1.base import OssSession, DotDict, get_session, dict_adapter, gen_format_progress_seq, deco_execution_time
from urllib.parse import unquote, urlparse
from typing import Union, List, Dict, Iterable
from abc import ABC, abstractmethod


def DotDictDeep(data):
    return json.loads(json.dumps(data, ensure_ascii=False), object_hook=lambda d: DotDict(**d))

def dict_to_list(items, keys: Iterable="xyz"):
    return [items[k] for k in keys] if isinstance(items, dict) else items

def list_to_dict(values, keys: Iterable="xyz"):
    return {k: values[k_idx] for k_idx, k in enumerate(keys)} if isinstance(values, list) else values

def list_adapter(lst: list, out_adapter=None):
    if out_adapter is None:
        return lst
    else:
        new_lst = list()
        for i in lst:
            if isinstance(i, list):
                new_lst.append(list_adapter(lst=i, out_adapter=out_adapter))
            else:
                new_lst.append(out_adapter(i))
        return new_lst

def timestamp_transform_unit(timestamp: Union[str, int, float], sep: int=10):
    """
    转换时间戳单位
    Args:
        timestamp: 时间戳
        sep: 整型部分位数，默认10位整数，单位位秒。其他单位e. 13=ms, 16=ns ···

    Returns: float

    """
    if "." in timestamp or isinstance(timestamp, float):
        return timestamp_transform_unit(timestamp=str(timestamp).replace(".", ""), sep=sep)
    return int(timestamp) / (10 ** len(str(timestamp)[sep:]))

def gen_vertexes_by_xywh(data, keys: Iterable=("x", "y", "width", "height")):
    x, y, w, h = dict_to_list(items=data, keys=keys)
    return [
        {"x": x, "y": y},
        {"x": x + w, "y": y},
        {"x": x + w, "y": y + h},
        {"x": x, "y": y + h}
    ]

# def dict_adapter_deep(d: dict, out_adapter=None):
#     """
#     参考 peutils.transform.v1.base.dict_adapter
#         可以深度处理d的v，但取消了key的rename方法
#     Args:
#         d: dict
#         out_adapter: 值的处理方法
#     Returns: new dict
#     """
#     d = {k: v for k, v in d.items()}
#     if out_adapter is not None:
#         if inspect.isfunction(out_adapter):
#             for k, v in d.items():
#                 if isinstance(v, dict):
#                     d[k] = dict_adapter_deep(d=v, out_adapter=out_adapter)
#                 else:
#                     d[k] = out_adapter(v)
#         elif isinstance(out_adapter, dict):
#             for k, v in d.items():
#                 if isinstance(v, dict):
#                     d[k] = dict_adapter_deep(d=v, out_adapter=out_adapter)
#                 else:
#                     for key, out_func in out_adapter.items():
#                         if key in d:
#                             d[key] = out_func(d[key])
#         else:
#             raise Exception("参数必须是函数或者字典. 如果是字典，那么就是对应的值是方法")
#
#     return d

class FramesGenCategorySeq():
    def __init__(self, start=0, default_dict=None):
        self.start = start

        self.track_seq = dict()  # {uuid: number}
        self.category_dict = dict() if default_dict is None else default_dict  # {frameId: {category: number}}

    def up_seq(self, frameId, category, uuid=None):
        if frameId in self.category_dict:
            if category in self.category_dict[frameId]:
                self.category_dict[frameId][category] = self.category_dict[frameId][category] + 1
            else:
                self.category_dict[frameId][category] = self.start + 1
        else:
            self.category_dict.setdefault(frameId, {})
            self.category_dict[frameId][category] = self.start + 1

        num = self.category_dict[frameId][category]
        if uuid is not None:
            self.track_seq[uuid] = num
            # if uuid in self.track_seq and self.track_seq[uuid] != num:
            #     print(f'uuid={uuid} 需要全局唯一', file=sys.stderr)
            # else:
            #     self.track_seq[uuid] = num
        return num


class GenUUIDSeq:
    """
    eg.
        gen_seq = GenUUIDSeq(start=0)
        get_uuid_seq = gen_seq.get_seq  # 等同于peutils.datautil.gen_uuid_seq
        for  i, k in enumerate("abcd", start=1):
            v = get_uuid_seq(k)
            print(v)
        print(gen_seq.uuid_dict)  # 不同于peutils.datautil.gen_uuid_seq
    """
    def __init__(self, start=0, default_dict=None):
        self.start = start
        self.uuid_dict = dict() if default_dict is None else default_dict

    def get_seq(self,uuid):
        if uuid not in self.uuid_dict:
            self.start += 1
            self.uuid_dict[uuid] = self.start
        return self.uuid_dict[uuid]


class CommonBaseMixIn():
    session = get_session(3)

    def parse_from_private_path(self, private_path, oss_prefix="appen://"):
        assert private_path.startswith(("appen://", "oss://"))
        private_path = private_path.replace(oss_prefix, "")
        route_list = private_path.split("/")
        bucket_name = route_list[0]
        private_real_path = '/'.join(route_list[1:])
        assert private_real_path != '', 'real_path为空'
        return bucket_name, private_real_path

    def get_raw_data(self, url, oss_prefix="appen://"):
        """
        可以获取 manifest pre_annotation annotation 的结果数据
        Args:
            url: http, https, oss_prefix 开头的数据
            oss_prefix: 当url为oss数据时，可以指定url前缀("appen://", "oss://")，用于切分bucket name和路径key。
        Returns:
        """
        if url.startswith(("http://", "https://")):
            rs = self.session.get(url).json()
            return rs

        bucket_name, private_real_path = self.parse_from_private_path(url, oss_prefix=oss_prefix)
        if bucket_name in ("appen-platform", "appen-platform-dev"):
            auth = oss2.Auth(os.getenv("MATRIXGO_RESULT_KEY"), os.getenv("MATRIXGO_RESULT_SECRET"))
            oss_session = OssSession()
            endpoint = "http://oss-cn-hangzhou.aliyuncs.com" if bucket_name == "appen-platform" else "http://oss-cn-zhangjiakou.aliyuncs.com"
            bucket = oss2.Bucket(auth, endpoint=endpoint, bucket_name=bucket_name, session=oss_session)
        else:
            bucket = OSS_STS_API(bucket_name=bucket_name)
        try:
            rs = json.loads(bucket.get_object(private_real_path).read())
        except Exception as e:
            raise Exception(f"请检查数据路径: {url}")
        return rs

    @staticmethod
    def get_expires_url_data(url):
        match = re.match(r"http.?://(.+)\.oss-cn-.+\.aliyuncs\.com/", url)
        if match is None:
            return None  # "不满足匹配条件"
        bucket_name = match.group(1)
        key = urlparse(unquote(url)).path.lstrip("/")
        api = OSS_STS_API(bucket_name=bucket_name)
        return api.bucket.get_object(key)

    def get_raw_data_by_oss_api(self, url,oss_client=None):
        url = unquote(url).split("?Expires=")[0]
        assert url.startswith("https://appen-data.oss-cn-shanghai.aliyuncs.com/"), "http bucket error"
        oss_key = url.replace("https://appen-data.oss-cn-shanghai.aliyuncs.com/", "")
        # oss_api = OSS_STS_API(bucket_name="appen-data")
        if not oss_client:
            oss_client=OSS_STS_API(bucket_name="appen-data")
        rs = json.loads(oss_client.bucket.get_object(oss_key).read())
        return rs

    def get_oss_data(self, url):
        auth = oss2.Auth(os.getenv("PE_OSS_AK"), os.getenv("PE_OSS_SK"))
        bucket = oss2.Bucket(auth, "http://oss-cn-hangzhou.aliyuncs.com", "tool-prod")
        if url.startswith("https://oss-prd.appen.com.cn:9001/tool-prod/"):
            oss_key = url.split("https://oss-prd.appen.com.cn:9001/tool-prod/")[1]
            rs = json.loads(bucket.get_object(oss_key).read())
            return rs
        elif url.startswith("https://tool-prod.oss-cn-hangzhou.aliyuncs.com/"):
            oss_key = url.split("https://tool-prod.oss-cn-hangzhou.aliyuncs.com/")[1]
            rs = json.loads(bucket.get_object(oss_key).read())
            return rs
        else:
            raise Exception("请检查annotation数据路径")

# 2.0模版实时检查
class ErrorUnit:
    def __init__(self, message, obj=None, id: Union[str, None]=None, frameNum: int=0):
        self.message = message
        self.obj = obj
        self.id = self.get_obj_id(id=id)
        self.category, self.number, self.name, self.frameId, self.is_component = self.parse_obj_get_info(frameNum=frameNum)

    def get_obj_id(self, id):
        # 高优：通过物体对象获取id，用于定位具体物体
        if self.obj is not None:
            try:
                return self.obj.id
            except AttributeError:
                pass
            except KeyError:
                pass
        elif id is not None:
            return id
        else:
            return "common-" + gen_uuid()

    def parse_obj_get_info(self, frameNum):
        category = ""  # 物体的名：实例对象就是实例名称，组件就是组件名称
        number = ""  # 物体编号：实例对象就是实例编号，组件就是组件编号
        name = ""  # 物体的具体名称：实例对象就是实例名称+编号，组件就是实例名称+编号 组件名称+编号
        is_component = False  # 是否是组件

        if self.obj is None:
            frameId = frameNum
        elif isinstance(self.obj, LidarInstance):
            category = self.obj.category
            number = self.obj.number
            name = f'{category}{number}'
            frameId = self.obj.frameId
        elif isinstance(self.obj, LidarComObj):
            category = self.obj.category
            number = self.obj.number
            name = f'{self.obj.instance.category}{self.obj.instance.number} {category}{number}'
            frameId = self.obj.frameId
            is_component = True
        elif isinstance(self.obj, DotDict):
            # 兼容自己构建的DotDict/dict, ErrorMsgLogV2.create_error会将dict转为DotDict
            category = self.obj.get("name", self.obj.get("category", ""))
            number = self.obj.get("number", "")
            if "instance" in self.obj:
                name = f'{self.obj.instance.category}{self.obj.instance.number} {category}{number}'
                is_component = True
            else:
                name = f'{category}{number}'
            frameId = self.obj.get("frameId", frameNum)
        else:
            frameId = frameNum
        return category, number, name, frameId, is_component

    def __repr__(self):
        if self.frameId is not None:
            err_str = f"ID: {self.id} 帧:{[self.frameId + 1]}"
        else:
            err_str = f"ID:{self.id}"

        if self.name != "":
            err_str = f'{err_str} 物体:{self.name} Message:{self.message}'
        else:
            err_str = f'{err_str} Message:{self.message}'

        return err_str

class ErrorMsgLogV2:
    def __init__(self):
        self.error_list = []

        self.error_listV1 = list()  # 暂时存放后处理格式的message，最后直接添加到self.error_list
        self.error_dict = dict()  # 暂时存放message用来处理成适合2.0的格式添加到self.error_list

        self.review_number = 0
        self.obj_type_dict = dict()
        self.obj_is_component = dict()

    def create_error(self, msg, obj=None, id: Union[str, None]=None, frameNum: int=0, block=True, a9_check: bool=True):
        """
        Args:
            msg:
            obj:
            id: obj为None, 可以传入id，给定默认值为common-uuid。主要针对全局属性、3D帧属性等
            frameNum: obj为None, 可以传入frameNum，给定默认值为0。主要针对全局属性、3D帧属性等
            block: 默认True阻止数据提交
            a9_check: 是否配置A9实时检查
        """
        if isinstance(obj, dict):
            obj = DotDictDeep(data=obj)

        ErrObj = ErrorUnit(message=msg, obj=obj, id=id, frameNum=frameNum)
        obj_id = ErrObj.id
        frame_id = ErrObj.frameId
        is_component = ErrObj.is_component
        self.obj_is_component[obj_id] = is_component

        self.error_listV1.append(ErrObj)  # 为后处理的message输出备份，self.fomart_error_str直接添加到self.error_list
        if a9_check is True:
            # A9实时检查暂存
            self.error_dict.setdefault(block, {}).setdefault(obj_id, {})
            if frame_id is not None and frame_id in self.error_dict[block][obj_id]:
                comment_len = len(self.error_dict[block][obj_id][frame_id]["data"]["comment"])
                if comment_len < 100:  # 同帧同框不同错误累计，设置长度限制
                    self.error_dict[block][obj_id][frame_id]["data"]["comment"] += f'; {msg}'
            else:
                try:
                    cam_fields = {"imageNum": obj.cameraIndex}
                    self.obj_type_dict.setdefault(obj_id, 0)  # 2d  reviewType = 0
                except:
                    cam_fields = dict()
                    self.obj_type_dict.setdefault(obj_id, 1)  # 3d  reviewType = 1
                self.error_dict[block][obj_id][frame_id] = {
                    "frame": frame_id,
                    **cam_fields,
                    "data": {
                        "result": "reject",
                        "type": ["标注错误"],
                        "comment": msg,
                    },
                }

    def fomart_error_str(self) -> str:
        self.error_list.extend(self.error_listV1)
        return "\n".join([repr(e) for e in self.error_list])

    def format_a9_error_str(self) -> str:
        for block, msg_errs in self.error_dict.items():
            for obj_id, items in msg_errs.items():
                self.review_number += 1
                self.error_list.append({
                    "id": obj_id,  # 物体id
                    "reviewType": self.obj_type_dict.get(obj_id, 1),  # 0=>2d, 1=>3d
                    "reviewNumber": self.review_number,
                    "isComponentReview": self.obj_is_component.get(obj_id, False),  # 是否是组件质检
                    # "message": message,
                    "frameInfoRecord": items,
                    "blockSubmit": block,
                    "updateTime": int(time.time() * 1000),
                })
        return json.dumps(self.error_list, ensure_ascii=False)

class LidarInstance():
    def __init__(self, frameId, id, category, number, attributes=None, createTime=None, updateTime=None):
        self.frameId = frameId
        self.id = id
        self.category = category
        self.number = number
        self.attributes = DotDictDeep(attributes) if attributes else DotDict()  # 动态属性
        self.createTime = createTime
        self.updateTime = updateTime

        self.shapes = list()

    def to_dict(self):
        _data_dict = {
            "frameId": self.frameId,
            "id": self.id,
            "category": self.category,
            "number": self.number,
            "attributes": self.attributes if self.attributes else None,
            "shapes": [shape.to_dict() for shape in self.shapes]
        }

        return _data_dict

    def __repr__(self):
        return f"{self.id} 物体: {self.category} {self.number} 组件数量: {len(self.shapes)}"

class LidarComObj(ABC):
    def __init__(
            # common params
            self, frameId, instance: LidarInstance, id, category, number, type, shapeData, attributes=None,
            projectMethod=None, interpolated=None, createTime=None, updateTime=None, createWorker=None, updateWorker=None,
    ):
        self.frameId = frameId
        self.instance = instance
        self.id = id
        self.category = category
        self.number = number
        self.type = type
        self.attributes = DotDictDeep(attributes) if attributes else DotDict()  # 动态属性

        if shapeData is not None:
            # 后处理中 ['CUBE', 'RECTANGLE3'] 不显示shapeData
            self.shapeData = DotDictDeep(shapeData)

        if projectMethod is not None:
            # 2d框会有
            self.projectMethod = projectMethod
        if interpolated is not None:
            self.interpolated = interpolated
        if createTime is not None:
            self.createTime = createTime
        if updateTime is not None:
            self.updateTime = updateTime
        if createWorker is not None:
            self.createWorker = createWorker
        if updateWorker is not None:
            self.updateWorker = updateWorker

    @abstractmethod
    def to_dict(self):
        ...

    def __repr__(self):
        return f"{self.id} 物体: {self.instance.category} {self.instance.number} 组件: {self.category} {self.number}"

class LidarCUBEObj(LidarComObj):
    # 'CUBE', 'RECTANGLE3'
    def __init__(
            self, position, dimension, quaternion, vertexes=None, pointCount=None, **kwargs
    ):
        super().__init__(**kwargs)
        self.position = DotDictDeep(position)
        self.dimension = DotDictDeep(dimension)
        self.quaternion = DotDictDeep(quaternion)
        self.vertexes = vertexes
        # pointCount = {'total': 3130, 'count': {'main': 1565, '3D': 1565}}
        self.pointCount = pointCount

    def to_dict(self):
        _data_dict = {
            "frameId": self.frameId,
            "id": self.id,
            "name": self.category,
            "number": self.number,
            "type": self.type,
            "shapeData": {
                "position": self.position,
                "dimension": self.dimension,
                "quaternion": self.quaternion,
            }
        }
        if self.attributes is not None:
            _data_dict["attributes"] = self.attributes
        if self.vertexes:
            _data_dict["shapeData"]["vertexes"] = self.vertexes
        if self.pointCount:
            _data_dict["pointCount"] = self.pointCount

        return _data_dict

class Lidar3dObj(LidarComObj):
    # "POLYLINE3", "POLYGON3", "CURVE3", "POINT3", 'POINTS'
    # todo 如果工具格式需要变动，重新创建类方法，独立出去
    # todo 独立的类若没有继承LidarComObj，需要在ErrorUnit中的parse_obj_get_info方法兼容
    def to_dict(self):
        _data_dict = {
            "frameId": self.frameId,
            "id": self.id,
            "name": self.category,
            "number": self.number,
            "type": self.type,
            "shapeData": self.shapeData,
        }
        if self.attributes is not None:
            _data_dict["attributes"] = self.attributes
        return _data_dict

class Lidar2dObj(LidarComObj):
    def __init__(self, cameraIndex, cameraName=None, parent=None, **kwargs):
        super().__init__(**kwargs)
        self.cameraIndex = cameraIndex
        self.cameraName = f'C{self.cameraIndex}' if cameraName is None else cameraName
        self.parent = parent

    def to_dict(self):
        _data_dict = {
            "frameId": self.frameId,
            "id": self.id,
            "name": self.category,
            "number": self.number,
            "type": self.type,
            "shapeData": self.shapeData,
            "cameraIndex": self.cameraIndex,
        }
        if self.parent is not None:
            _data_dict["parent"] = self.parent
        if self.attributes is not None:
            _data_dict["attributes"] = self.attributes
        return _data_dict

    def __repr__(self):
        return f"{self.id} {self.instance.category} {self.instance.number} {self.cameraName} {self.category} {self.number}"

class BitArray:
    """
    from peutils.transform.v2.base import BitArray
    将数字索引转为bigint字符串表现形式
    # eg. 涂色'POINTS'工具格式
        "shapeData": {  # f"{frame_idx}_{传感器名称}"，传感器名称默认P{index}
            f"{frame_idx}_P0": {
                "data": bigint_data,
                "size": bigint_size
            }
        }

    # eg. from peutils.transform.v2.base import gen_bit_pre_dict
    # 列表转换成bigint
    bit_array = BitArray()
    bit_array.set_all_bits(points_index_lst)
    bigint_data = bit_array.get_str_bits()
    bigint_size = bit_array.size
    >> {
        "data": bigint_data,
        "size": bigint_size
    }

    """

    def __init__(self):
        self.bits = {}  # 使用字典来存储块（每个块是一个整数）
        self.size = 0  # 跟踪被设置的位的数量（可选）

    @staticmethod
    def bits2list(bits):
        """
        获取点云索引
        bigint -> int：list
        :param bits:
        :return:
        """
        result = []
        for chunk_index_str, chunk_str in bits.items():
            chunk_index = int(chunk_index_str)  # 将字符串键转换为整数索引
            chunk = int(chunk_str)  # 将字符串表示的整数转换为Python整数
            for bit_index in range(64):  # 遍历64位
                # 检查第bit_index位是否为1
                if (chunk >> bit_index) & 1:
                    # 计算并添加全局索引到结果列表
                    # 注意：这里的索引是全局的，从0开始，每个块都是64位
                    index = chunk_index * 64 + bit_index
                    result.append(index)
        return result

    @staticmethod
    def get_chunk_index(index):
        return index // 64  # 整数除法来确定块索引

    @staticmethod
    def get_bit_index(index):
        return index % 64  # 求余来确定位索引

    def get_bit(self, index):
        if index < 0:
            raise ValueError('Index out of bounds.')
        chunk_index = self.get_chunk_index(index)
        bit_index = self.get_bit_index(index)
        chunk = self.bits.get(chunk_index, 0)  # 如果块不存在，默认为0
        return (chunk >> bit_index) & 1 != 0  # 使用位操作检查位是否为1

    def set_bit(self, index):
        if index < 0:
            raise ValueError('Index out of bounds.')
        if not self.get_bit(index):
            chunk_index = self.get_chunk_index(index)
            bit_index = self.get_bit_index(index)
            # 如果块不存在，在字典中创建一个新的块（默认为0）
            if chunk_index not in self.bits:
                self.bits[chunk_index] = 0
                # 设置指定位的值为1
            self.bits[chunk_index] |= (1 << bit_index)
            self.size += 1  # 更新被设置的位的数量

    def set_all_bits(self, index_list):
        for index in index_list:
            self.set_bit(index)

    def get_str_bits(self):
        return {str(k): str(v) for k, v in self.bits.items()}

def gen_bit_pre_dict(p_index_lst):
    bit_array = BitArray()
    bit_array.set_all_bits(p_index_lst)
    bigint_data = bit_array.get_str_bits()
    bigint_size = bit_array.size
    return {
        "data": bigint_data,
        "size": bigint_size
    }

if __name__ == "__main__":
    
    sys.exit()


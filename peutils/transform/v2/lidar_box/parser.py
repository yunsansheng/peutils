#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: echai
Date: 2024-12-20
Short Description:
Change History:
"""
from urllib.parse import unquote, urlparse
from peutils.transform.v2.lidar_manifest.parser import *
from peutils.transform.v2.base import *
from peutils.transform.v1.tools.lidar import get_abs_cube_points_list
import json
from io import BytesIO
from PIL import Image
from itertools import groupby
from types import SimpleNamespace
from collections import defaultdict
from peutils.datautil import gen_uuid_seq


class LidarBoxFrame(CommonBaseMixIn):
    def __init__(
            self, config, mfst_data, frameId, points, camera_idx2name, camera_meta, instances,
            frameInfo=None, frame_attr=None, relations=None):
        self.mfst_data = mfst_data

        self.frameId = frameId
        self.points = points
        self.frameInfo = DotDict() if frameInfo is None else frameInfo
        self.frame_attr = DotDict() if frame_attr is None else frame_attr
        self.relations = DotDict() if relations is None else relations

        self.log = ErrorMsgLogV2()
        self.config = config
        if self.config.parse_id_col == "fid":
            self.config.ist_seq_obj = GenUUIDSeq(start=self.config.seq_start)
            self.config.ist_seq_func = self.config.ist_seq_obj.get_seq
            self.config.lidar_seq_obj = GenUUIDSeq(start=self.config.seq_start)
            self.config.lidar_seq_func = self.config.lidar_seq_obj.get_seq
            self.config.img_seq_obj = GenUUIDSeq(start=self.config.seq_start)
            self.config.img_seq_func = self.config.img_seq_obj.get_seq

        # {cameraIndex: cameraName}
        self.camera_idx2name = DotDict(camera_idx2name)
        """
        camera_meta = {cameraName: {
            name: cameraName,  # manifest定义的镜头名
            a9_defined: name,  # a9模板自定义的镜头名
            index: index,
            url: cam_url,  # 可访问的https
            size: size,  # 宽高，平台不输出，默认None，当self.config.gen_img_size=True时为(width, height)
            attributes: cam_item.attributes,  # 2D帧属性
            items: {shape.id: Lidar2dObj}  # 当前帧该镜头所有的图像
        }}
        """
        self.camera_meta = DotDictDeep(data=camera_meta)  # item记录所有的2D框
        """
        instance_dict = {instance.id: LidarInstance}
            # 所有的实例对象
        lidar_dict = {shape.id: Lidar3dObj}
            # 所有点云物体，包含only_lidar_dict
        only_lidar_dict = {shape.id: Lidar3dObj}
            # 单独标注的点云物体
        projection_image_dict = {shape.parent: {cameraName: {shape.id: Lidar2dObj}}}
            # 由点云物体投影的图像，允许标注多个，所以parent下有多个Lidar2dObj
            # 使用shape.parent方便通过lidar_dict中的id配的对应的Lidar2dObj
        only_image_dict = {instance.id: {cameraName: {shape.id: Lidar2dObj}}}  
            # 单独标注的图像物体，允许标注多个，所以instance下有多个Lidar2dObj
            # instance.id方便区分Lidar2dObj属于哪个实例
        """
        self.instance_dict, self.lidar_dict, self.only_lidar_dict, self.projection_image_dict, self.only_image_dict = self.parse_by_instance(instances)
        lidar_dict = dict(sorted(self.lidar_dict.items(), key=lambda i: i[1].type))
        self.type_lidar_dict = DotDict({k: dict(v) for k, v in groupby(lidar_dict.items(), key=lambda i: i[1].type)})

    def gen_key_by_id(self, item, func_type):
        assert func_type in ["ist", "lidar", "img"], f'func_type not in ["ist", "lidar", "img"]'
        ### 注意：这里是 instance shape通用的生成key的方式，请注意item无法获取到值的情况
        if self.config.parse_id_col == "id":
            key = item.id
            if func_type == "img" and item.parent is not None:
                return [item.parent, key]
        # number不适用，废弃
        # elif self.config.parse_id_col == "number":
        #     key = item.number
        elif self.config.parse_id_col in ("gid", "fid"):
            if func_type == "ist":
                key = self.config.ist_seq_func(item.id)
            elif func_type == "lidar":
                key = self.config.lidar_seq_func(item.id)
            elif func_type == "img":
                try:
                    key = self.config.img_seq_func(item.id)
                    if item.parent is not None:
                        parent_key = self.config.lidar_seq_func(item.parent)
                        return [parent_key, key]
                except AttributeError:
                    key = self.config.img_seq_func(item.id)
                except KeyError:
                    key = self.config.img_seq_func(item.id)
            else:
                raise Exception(f'parse_id_col={self.config.parse_id_col}时，func_type设置["ist", "lidar", "img"]其中之一')
        else:
            raise Exception("parse_id_col解析模式错误")

        return key

    def parse_by_instance(self, instances):
        instance_dict = dict()

        # 情况太复杂，eg. 1. 多个3D多个2D框时，不能存在独立标注的2D框；2. 一个3D框时，2D可以独立标注；···等等
        lidar_dict = dict()  # 所有Lidar3dObj
        only_lidar_dict = dict()  # 独立标注的Lidar3dObj
        projection_image_dict = dict()  # Lidar3dObj投影的Lidar2dObj
        only_image_dict = dict()  # 独立标注的Lidar2dObj
        for instance in instances:
            ist_obj = LidarInstance(
                frameId=self.frameId,
                id=instance.id,
                category=instance.category,
                number=instance.number,
                attributes=instance.get("attributes", DotDict()),  # 动态属性
                createTime=instance.get("createTime"),
                updateTime=instance.get("updateTime"),
            )
            ist_key = self.gen_key_by_id(item=ist_obj, func_type="ist")

            # 2D 3D 混合在一起的，2D中的parent为3D框ID，表示由3D框投影生成
            for item in instance.shapes:
                item_type = item.type

                # 2D，同instance、同lidar、同镜头 都可以标注多个
                if "cameraIndex" in item:
                    cameraIndex = item["cameraIndex"]
                    camera_name = self.camera_idx2name[int(cameraIndex)]
                    keys, obj = self.parse_img_by_item(ist_obj=ist_obj, item=item)
                    # 3D的投影框
                    if "parent" in item:
                        parent_key, key = keys
                        projection_image_dict.setdefault(parent_key, {}).setdefault(camera_name, {}).update({key: obj})
                    # 单独标注的2D框
                    else:
                        key = keys
                        # 是否允许单独标注2D
                        if self.config.allow_only_2d is False:
                            self.log.create_error(msg="不允许独立标注2D", obj=obj)
                            continue
                        only_image_dict.setdefault(ist_key, {}).setdefault(camera_name, {}).update({key: obj})
                    self.camera_meta[camera_name]["items"].update({key: obj})
                # 3D，同instance可以标注多个。
                # 这里处理会拆成多个键值对。
                # 按instance分可以使用 itertools.groupby 对lidar_dict分组
                else:
                    if item_type in ["CUBE", "RECTANGLE3"]:
                        key, obj = self.parse_cube_by_item(ist_obj=ist_obj, item=item)
                    else:
                        key, obj = self.parse_lidar_by_item(ist_obj=ist_obj, item=item)
                    lidar_dict[key] = obj
                ist_obj.shapes.append(obj)  # LidarInstance添加Lidar2dObj, Lidar3dObj

            instance_dict[ist_key] = ist_obj

        for lidar_key, lidar_obj in lidar_dict.items():
            if lidar_key not in projection_image_dict:
                if self.config.allow_only_3d is False:
                    self.log.create_error(msg="不允许独立标注3D", obj=lidar_obj)
                    continue
                only_lidar_dict[lidar_key] = lidar_obj

        return instance_dict, lidar_dict, only_lidar_dict, projection_image_dict, only_image_dict

    def parse_cube_by_item(self, ist_obj, item):
        """
        立体框'CUBE'
                {
                    'position': {'x': 17.868800208232894, 'y': -3.205934701847561, 'z': 0.8},
                    'dimension': {'x': 4.6, 'y': 1.7, 'z': 1.6},
                    'quaternion': {'x': 0, 'y': 0, 'z': 0.9999976664686614, 'w': -0.0021603372958671}
                }
        矩形框'RECTANGLE3'
                {
                    'position': {'x': 13.623840253252638, 'y': -4.27206947092273, 'z': 0},
                    'dimension': {'x': 1.2619965389358034, 'y': 0.984357512780763, 'z': 0},
                    'quaternion': {'x': 0, 'y': 0, 'z': 0.7071067811865476, 'w': -0.7071067811865475},
                    'vertexes': [
                        [13.131661496862256, -4.9030677403906315, 0],
                        [14.116019009643018, -4.903067740390632, 0],
                        [14.11601900964302, -3.6410712014548285, 0],
                        [13.131661496862257, -3.6410712014548285, 0]
                    ]
                }
        """
        position = item.shapeData.position
        dimension = item.shapeData.dimension
        quaternion = item.shapeData.quaternion

        vertexes = None
        pointCount = item.get("pointCount", {})
        if item.type == "CUBE":
            # 计算顶点坐标
            if self.config.cube_vertexes is True:
                vertex_arr = get_abs_cube_points_list(quaternion=quaternion, position=position, dimension=dimension, axis="a9")
                vertexes = [list_adapter(lst=vertex, out_adapter=self.config.number_adapter_func) for vertex in vertex_arr.tolist()]

            ####业务检查
            if self.config.has_pointCount > 0:
                # 解析点云数量
                if pointCount.get("total"):
                    if pointCount.total < self.config.has_pointCount:
                        self.log.create_error(msg=f"点云数量{pointCount.total} < {self.config.has_pointCount}", obj=item)
                else:
                    self.log.create_error(msg=f"点云数量不能为空", obj=item)

            if self.config.yaw_only is True:
                # 仅水平旋转 不一定是x y为0，坐标系不同z不一定是yaw
                # 但一定只有一个值，其他两个位为0
                if len(set(dict_to_list(items=quaternion, keys="xyz")) - {0}) != 1:
                    self.log.create_error(msg="请确认数据是否为仅水平旋转", obj=item)

        else:
            vertexes = list_adapter(lst=item.shapeData.vertexes, out_adapter=self.config.number_adapter_func)

        lidar_obj = LidarCUBEObj(
            frameId=self.frameId,
            instance=ist_obj,
            id=item.id,
            category=item.name,
            number=item.number,
            type=item.type,
            shapeData=None,
            position=dict_adapter(position, out_adapter=self.config.number_adapter_func),
            dimension=dict_adapter(dimension, out_adapter=self.config.number_adapter_func),
            quaternion=dict_adapter(quaternion, out_adapter=self.config.number_adapter_func),
            vertexes=vertexes,
            attributes=DotDict(item.attributes) if item.get("attributes", None) else DotDict(),  # 动态属性
            interpolated=item.get("interpolated", None),
            createTime=item.get("createTime", None),
            updateTime=item.get("updateTime", None),
            createWorker=item.get("createWorker", None),
            updateWorker=item.get("updateWorker", None),
            pointCount=pointCount,
        )
        key = self.gen_key_by_id(item=lidar_obj, func_type="lidar")
        return key, lidar_obj

    def parse_lidar_by_item(self, ist_obj, item):
        """
        Args:
            ist_obj:
            item:
                type:
                    # 可以投影图形的工具
                    折线'POLYLINE3'
                            {
                                'vertexes': [
                                    {'position': [1, 1, 1], 'attributes': {'点属性': '1'}, 'pid': '23cf07c0'},
                                    {'position': [1, 1, 1], 'attributes': {'点属性': '1'}, 'pid': '23cf07c0'},
                                    {'position': [1, 1, 1], 'attributes': {'点属性': '1'}, 'pid': '23cf07c0'},
                                    ...
                                ]
                            }
                    多边形'POLYGON3'
                            {
                                'vertexes': [
                                    {'position': [1, 1, 1], 'attributes': {'点属性': '1'}},
                                    {'position': [1, 1, 1], 'attributes': {'点属性': '1'}},
                                    {'position': [1, 1, 1], 'attributes': {'点属性': '1'}},
                                    ...
                                ]
                            }
                    曲线'CURVE3'
                            {
                                'vertexes': [
                                    {'position': [1, 1, 1], 'attributes': {'点属性': '1'}, 'pid': '23cf07c0'},
                                    {'position': [1, 1, 1], 'attributes': {'点属性': '1'}, 'pid': '23cf07c0'},
                                    {'position': [1, 1, 1], 'attributes': {'点属性': '1'}, 'pid': '23cf07c0'},
                                    ...
                                ],
                                'bidirection': False
                            }
                    点'POINT3'
                            {
                                'vertexes': [{'position': [1, 1, 1]}],
                                'legacy': False
                            }
                    实例标签中心线 或 生成的动态中心线 'CENTER_LINE3'
                            {
                                'vertexes': [
                                    {'position': [1, 1, 1]},
                                    {'position': [1, 1, 1]},
                                    {'position': [1, 1, 1]},
                                    ...
                                ],
                                'source': {  # key应该是固定的, 2为左车道线 3为右车道线
                                    '2': '03d00645-a998-41bc-8340-4a4bc33cb77e',
                                    '3': '7dc508ae-ee08-4ff6-87e3-fe86070e5bf0'
                                },
                                'orders': {
                                    'pre': ['c8587933-7d70-430b-8bda-0de0b5841788'],  # 前驱
                                    'next': ['77817375-1d8a-44f5-9959-441dee3446fa'],  # 后继
                                    'left': '4e66afd5-648d-495b-aee5-9d0f7448251a',  # 左中心线
                                    'right': '7d75e07f-a33a-42d1-9002-ce07b45f3e9d'  # 右中心线
                                }
                            }
                    # 不可以投影图形的工具
                    涂色'POINTS'
                            {  # 帧id_传感器名称e. 0_main 0_P0
                                '0_P0': {
                                    "data": {
                                        0: 1995152341241,
                                        2: 1995152341341,
                                        3: 1995152341341,
                                    },
                                    "size": 3556,
                                    "min": [x, y, z],
                                    "max": [x, y, z]
                                }
                            }
                attributes: 未标注属性，该字段不会存在
        Returns:

        """
        ### 通用type的处理方式
        _type = item.type
        if _type in ["POLYLINE3", "POLYGON3", "CURVE3", "POINT3", "CENTER_LINE3"]:
            for vertex in item.shapeData.vertexes:
                vertex["position"] = list_adapter(lst=vertex.position, out_adapter=self.config.number_adapter_func)
        elif _type in ["POINTS"]:
            ### 涂色'POINTS' 不适用对值进行number_adapter_func
            pass
        else:
            raise TypeError(f"点云图形工具 {_type} 暂不支持")

        ####业务检查

        lidar_obj = Lidar3dObj(
            frameId=self.frameId,
            instance=ist_obj,
            id=item.id,
            category=item.name,
            number=item.number,
            type=_type,
            shapeData=item.shapeData,
            attributes=DotDict(item.attributes) if item.get("attributes", None) else DotDict(),  # 动态属性
            interpolated=item.get("interpolated", None),
            createTime=item.get("createTime", None),
            updateTime=item.get("updateTime", None),
            createWorker=item.get("createWorker", None),
            updateWorker=item.get("updateWorker", None),
        )
        key = self.gen_key_by_id(item=lidar_obj, func_type="lidar")
        return key, lidar_obj

    def parse_img_by_item(self, ist_obj, item):
        """
        Args:
            ist_obj:
            item:
                type:
                    自由立体框'free-cuboid' = {'points': [{'x': 0, 'y': 0}, {'x': 1, 'y': 1}, {'x': 2, 'y': 2}, {'x': 3, 'y': 3}, {'x': 4, 'y': 4}, {'x': 5, 'y': 5}, {'x': 6, 'y': 6}, {'x': 7, 'y': 7}]}
                    长方形'rectangle' = {'x': 551.760027, 'y': 191.513338, 'width': 84.919395, 'height': 66.145217}
                    前后矩形框'two-sides-cuboid' = {'front': {'x': 571.973963, 'y': 191.513338, 'width': 64.705459, 'height': 61.474902}, 'back': {'x': 552.598719, 'y': 211.824383, 'width': 48.109792, 'height': 45.834172}}
                    折线'line' = {'points': [{'x': 0, 'y': 0}, {'x': 1, 'y': 1}, ···]}
                    多边形'polygon' = {'points': [{'x': 0, 'y': 0}, {'x': 1, 'y': 1}, ···]}
                    点'dot' = {'x': 0, 'y': 0}
                attributes: 未标注属性，该字段不会存在
        Returns:

        """
        _type = item.type
        if item.type in ["rectangle"]:
            shapeData = dict_adapter(item.shapeData, out_adapter=self.config.number_adapter_func)
        elif item.type in ["two-sides-cuboid"]:
            shapeData = {k: dict_adapter(v, out_adapter=self.config.number_adapter_func) for k, v in item.shapeData.items()}
        elif item.type in ["free-cuboid", "line", "polygon"]:
            shapeData = {
                "points": [dict_adapter(v, out_adapter=self.config.number_adapter_func) for v in item.shapeData.points]
            }
        elif item.type in ["dot"]:
            shapeData = dict_adapter(item.shapeData, out_adapter=self.config.number_adapter_func)
        else:
            # 新增工具注意下方超出边界检查同步兼容
            raise TypeError(f"点云图形工具 {_type} 暂不支持")

        img_obj = Lidar2dObj(
            frameId=self.frameId,
            instance=ist_obj,
            id=item.id,
            category=item.name,
            number=item.number,
            type=_type,
            shapeData=DotDictDeep(data=shapeData),
            cameraIndex=item.cameraIndex,
            cameraName=self.camera_idx2name[item.cameraIndex],
            attributes=DotDict(item.attributes) if item.get("attributes", None) else DotDict(),  # 动态属性
            parent=item.get("parent", None),
            projectMethod=item.get("projectMethod", None),
            interpolated=item.get("interpolated", None),
            createTime=item.get("createTime", None),
            updateTime=item.get("updateTime", None),
            createWorker=item.get("createWorker", None),
            updateWorker=item.get("updateWorker", None),
        )
        if self.config.overflow is False:
            size = self.camera_meta[img_obj.cameraName]["size"]
            width, height = (None, None) if size is None else size
            if width is not None and height is not None:
                if item.type in ["rectangle"]:
                    xy_list = gen_vertexes_by_xywh(data=img_obj.shapeData)
                elif item.type in ["two-sides-cuboid"]:
                    xy_list = [
                        *gen_vertexes_by_xywh(data=img_obj.shapeData.front),
                        *gen_vertexes_by_xywh(data=img_obj.shapeData.back)
                    ]
                elif item.type in ["free-cuboid", "line", "polygon"]:
                    xy_list = img_obj.shapeData.points
                elif item.type in ["dot"]:
                    xy_list = [img_obj.shapeData]
                else:
                    raise TypeError(f"点云图形工具 {_type} 暂不支持超出边界检查")
                # xy_list = [{'x': 1, 'y': 1}, {'x': 1, 'y': 1}, ···]
                for xy in xy_list:
                    if xy["x"] < 0 or xy["y"] < 0 or xy["x"] > width or xy["y"] > height:
                        self.log.create_error(msg="图像超出边界", obj=img_obj)
                        break

        keys = self.gen_key_by_id(item=img_obj, func_type="img")
        return keys, img_obj

    def parse_orders_by_objs(self, pre_next_bothway=False):
        """
        解析orders，当前支持：
            - 前驱后继
        Args:
            pre_next_bothway: 默认False不检查前驱后继双向对应
        """
        # 物体左线2 右线3
        # source_2_dict = DotDict()
        # source_3_dict = DotDict()

        # 物体前驱pre 后继next  ### 参考 byd_private/byd-hnoa-4-after-lane-8548.py 方法parse_obj_gen_pre_next
        orders_pre_dict = DotDict()
        orders_next_dict = DotDict()
        # 物体左侧left 右侧right
        # orders_left_dict = DotDict()
        # orders_right_dict = DotDict()

        # 由于self.config.parse_id_col，obj_key不一定是uuid。要obj.id
        all_lidar_id = {obj.id: obj for obj in self.lidar_dict.values()}

        for obj_type, obj_items in self.type_lidar_dict.items():
            for obj_key, obj in obj_items.items():
                # 没有shapeData的对象、没有orders的对象都需要跳过
                try:
                    orders = obj.shapeData.orders
                except AttributeError:
                    continue
                except KeyError:
                    continue
                obj_uuid = obj.id
                # 前驱
                for pre_id in orders.get("pre", []):
                    if pre_id not in all_lidar_id:
                        self.log.create_error(msg=f"物体前驱{pre_id}不存在", obj=obj)
                        continue
                    # 构造前驱及其前驱id的后继
                    orders_pre_dict.setdefault(obj_uuid, set()).add(pre_id)
                    if pre_next_bothway is True:
                        # 当前A的前驱是B，则B的后继是A
                        orders_next_dict.setdefault(pre_id, set()).add(obj_uuid)

                # 后继
                for next_id in orders.get("next", []):
                    if next_id not in all_lidar_id:
                        self.log.create_error(msg=f"物体后继{next_id}不存在", obj=obj)
                        continue
                    # 构造后继及其后继id的前驱
                    orders_next_dict.setdefault(obj_uuid, set()).add(next_id)
                    if pre_next_bothway is True:
                        # 当前A的后继是B，则B的前驱是A
                        orders_pre_dict.setdefault(next_id, set()).add(obj_uuid)

        if pre_next_bothway is True:
            # 物体A有前驱B，那么B的后继应该有A
            for obj_id, pre_id_set in orders_pre_dict.items():
                obj = all_lidar_id[obj_id]
                for pre_id in pre_id_set:
                    if obj_id not in orders_next_dict.get(pre_id, set()):
                        # A = ErrorUnit(message="", obj=obj).__repr__().rsplit(" Message:", 1)[0]
                        B = ErrorUnit(message="", obj=all_lidar_id[pre_id]).__repr__().rsplit(" Message:", 1)[0]
                        self.log.create_error(msg=f'与 {B} 非双向前驱后继', obj=obj)

            # 物体B有后继A，那么A的前驱应该有B
            for obj_id, next_id_set in orders_next_dict.items():
                obj = all_lidar_id[obj_id]
                for next_id in next_id_set:
                    if obj_id not in orders_pre_dict.get(next_id, set()):
                        B = ErrorUnit(message="", obj=all_lidar_id[next_id]).__repr__().rsplit(" Message:", 1)[0]
                        self.log.create_error(msg=f'与 {B} 非双向前驱后继', obj=obj)

        return orders_pre_dict, orders_next_dict

    def parse_relations(self):
        staticCenterLineDict = dict()
        correlationDict = dict()
        coverDict = dict()

        for relation in self.relations:
            # 静态中心线的一些字段
            staticCenterLineKeys = {"sourceId", "targetId", "type", "lineVertices", "frame", "id", "number"}
            isStaticCenterLine = True if len(staticCenterLineKeys - relation.keys()) == 0 else False
            if isStaticCenterLine:
                """
                    {
                        "sourceId": "2ebe98f6-96d1-4d2b-ad28-b2ffc5cd4514",  # 线1.id
                        "targetId": "4a61da40-60aa-4617-b380-bd77d7e471b5",  # 线2.id
                        "type": 0,
                        "lineVertices": [   # 静态中心线顶点
                            [
                                4.851258993148804,
                                -1.4070330411195755,
                                -2.3196784257888794
                            ],
                            [
                                6.844011974248766,
                                -0.994390433340856,
                                -2.3312514058391076
                            ],
                            [
                                12.17837905883789,
                                -0.7067844867706299,
                                -2.3096799850463867
                            ]
                        ],
                        "frame": 0,  # 帧id
                        "id": "413c315f-c66d-48f4-9667-3f33452300ff",  # 由线1+线2生成的静态中心线.id
                        "positions": {},
                        "number": 1,  # 静态中心线序号
                        "attributes": {  # 中心线图形属性
                            "center_attr123": "a"
                        }
                    }
                """
                staticCenterLineDict[relation.id] = relation
                continue

            if relation.description == "从属":
                """
                    {
                        "description": "从属",
                        "sourceType": "SHAPE_ITEM",
                        "targetId": "ce6b0459-b4fd-4172-9623-9ff51b8e0491",
                        "targetType": "SHAPE_ITEM",
                        "sourceId": "6429ac81-f12a-46bb-9e23-731842c7676e",
                        "frame": 0,
                        "type": 1
                    }
                """
                correlationDict.setdefault(relation.sourceId, set()).add(relation.targetId)

            elif relation.description == "覆盖":
                """
                    {
                        "description": "覆盖",
                        "sourceType": "SHAPE_ITEM",
                        "targetId": "ce6b0459-b4fd-4172-9623-9ff51b8e0491",
                        "targetType": "SHAPE_ITEM",
                        "sourceId": "6429ac81-f12a-46bb-9e23-731842c7676e",
                        "frame": 0,
                        "type": 1
                    }
                """
                coverDict.setdefault(relation.sourceId, set()).add(relation.targetId)

        return staticCenterLineDict, correlationDict, coverDict

    def __repr__(self):
        return f'Frame {self.frameId}'

class LidarBoxParse(CommonBaseMixIn):

    ### 继承session属性 用来读取url
    def __init__(self, url, config):
        self.url = url
        self.config = config
        if self.config.parse_id_col == "gid":
            self.config.ist_seq_obj = GenUUIDSeq(start=self.config.seq_start)
            self.config.ist_seq_func = self.config.ist_seq_obj.get_seq
            self.config.lidar_seq_obj = GenUUIDSeq(start=self.config.seq_start)
            self.config.lidar_seq_func = self.config.lidar_seq_obj.get_seq
            self.config.img_seq_obj = GenUUIDSeq(start=self.config.seq_start)
            self.config.img_seq_func = self.config.img_seq_obj.get_seq

        self.raw_data = DotDictDeep(data=self.get_raw_data(url))  # 获取JSON字典数据数据
        self.mfst_data = LidarManifestParse(
            # 只有annotation.flowData.base_url存在manifest数据，并且数据格式为 文件路径被转换成可访问的url 的 json.dumps格式
            base_url=self.raw_data["flowData"][self.config.manifest_col_name], config=LidarManifestConfig()
        )
        # 静态属性：实例属性(self.staticAttrs.instance)+全局属性(self.staticAttrs.global)
        self.staticAttrs = self.raw_data.staticAttributes
        # self.instStaticAttrs = self.staticAttrs.get("instance", DotDict())
        # self.globalStaticAttrs = self.staticAttrs.get("global", DotDict())

        self.frames_lst, self.frame_length = self.parse_by_frame()

    def check_frames_error(self):
        all_errors = []
        for frame in self.frames_lst:
            all_errors.extend(frame.log.error_listV1)
        return all_errors

    def parse_by_frame(self):
        """返回解析后的frame列表，对应的数据"""
        frames_lst = []
        for idx, raw_frame in enumerate(self.raw_data["frames"]):
            frameId = raw_frame.frame  # 帧ID
            frame_attr = raw_frame.get("attributes", {})  # 3D帧属性

            # 2.0模版没有发现有效帧无效帧
            # if self.config.has_ignore_frame is True:
            #     isValid = raw_frame.get("isValid")
            # else:
            #     isValid = raw_frame["isValid"]

            if self.config.filter_frame and self.config.key_frames:
                raise Exception("filter_frame和key_frames不能同时配置")

            camera_idx2name = dict()
            camera_meta = dict()
            for cam_item in raw_frame.cameraInfoList:
                cam_idx = cam_item.index
                cam_name, cam_urls = self.mfst_data.cameras_list[cam_idx]
                cam_url = cam_urls[frameId]

                # 参数。只添加了sensor中的calib处理，对于manifest外参的参数，可以直接使用self.mfst_data.raw_data单独处理
                cam_calib = None
                if self.mfst_data.calib_dict.get(cam_name) is None:
                    pass
                elif isinstance(self.mfst_data.calib_dict.get(cam_name), dict):
                    cam_calib = self.mfst_data.calib_dict.get(cam_name)
                elif isinstance(self.mfst_data.calib_dict.get(cam_name), list):
                    cam_calib = self.mfst_data.calib_dict[cam_name][frameId]  # 连帧，每帧不同的情况

                # 图片尺寸
                size = None
                if self.config.gen_img_size is True or self.config.overflow is False:
                    # 当overflow=False需要校验2d是否超出边界时，也会获取图像尺寸
                    try:
                        img_data = self.session.get(cam_url)
                        size = Image.open(BytesIO(img_data.content)).size
                    except Exception as e:
                        api_data = self.get_expires_url_data(url=cam_url)
                        if api_data is not None:
                            size = Image.open(BytesIO(api_data.read())).size
                        if size is None:
                            raise Exception(f'图片 {cam_url} 获取size失败：{e}')
                camera_idx2name[cam_idx] = cam_name
                camera_meta[cam_name] = {
                    "name": cam_name,  # manifest定义的镜头名，manifest中相机传感器的名称key不是name时，平台输出会默认以 C0 的方式命名传感器
                    "index": cam_idx,
                    "url": cam_url,
                    "size": size,  # 宽高
                    "attributes": cam_item.get("attributes", DotDict()),  # 2D帧属性
                    "calibration": cam_calib,
                    "items": dict(),  # 该镜头所有的图像 {shape.id: Lidar2dObj}
                }

            mod2 = (frameId + 1) % 2
            if (self.config.filter_frame =='even' and mod2 == 1) or (self.config.filter_frame =='odd' and mod2 == 0) or (self.config.key_frames and frameId not in self.config.key_frames):
                # 偶数的时候忽略奇数帧 奇数的时候忽略偶数帧
                # 忽略非关键帧
                frame = LidarBoxFrame(
                    config=self.config,
                    mfst_data=self.mfst_data,
                    frameId=frameId,
                    points=raw_frame.points,
                    instances=[],
                    camera_idx2name=camera_idx2name,
                    camera_meta=camera_meta,
                )
            else:
                frame = LidarBoxFrame(
                    config=self.config,
                    mfst_data=self.mfst_data,
                    frameId=frameId,
                    points=raw_frame.points,
                    frameInfo=raw_frame.frameInfo,
                    frame_attr=frame_attr,
                    instances=raw_frame.instances,
                    camera_idx2name=camera_idx2name,
                    camera_meta=camera_meta,
                    relations=raw_frame.relations,
                )
            frames_lst.append(frame)

        return frames_lst, len(frames_lst)

class LidarBoxDataConfig():
    def __init__(
            self, manifest_col_name="base_url", yaw_only=True, has_pointCount: int=0, number_adapter_func=None, parse_id_col="id", seq_start=0,
            filter_frame=None, key_frames=None,
            allow_only_3d=False, allow_only_2d=False, gen_img_size=False, overflow=True, cube_vertexes=False,
    ):
        """
        Args:
            manifest_col_name: manifest列名，csv和FlowData一致
            yaw_only: 检查是否仅水平
            has_pointCount: 检查点云数量total是否 < has_pointCount
            number_adapter_func: 处理shapeData数值的方法,eg. lambda d: round(d, 3) if isinstance(d, int) else d
            parse_id_col: 对象键值对key的取值方式：id, gid（全局track, id生成int）, fid（帧内id生成int）
            seq_start: parse_id_col=fid时，序列编号起始值。seq_start=-1，则起始值为0，seq_start=0，则起始值为1，···
            # has_ignore_frame: 如果是True的时候，那么图片的宽高和和isvalid可以为空
            # cam_parse_mode:
            #     镜头名字解析模式，默认是取文件夹名字 可选值有manifest_parse
            #     新增kitti_manifest模式解析
            filter_frame: 默认None odd 奇数 even 偶数
            key_frames: 默认None 需要解析的关键帧
            # private_manifest:
            allow_only_3d: 默认不允许独立标注3d框
            allow_only_2d: 默认不允许独立标注2d框
            gen_img_size: 获取图片size=(width, height)
            overflow: 默认允许超出图像边界
            cube_vertexes: 默认不需要计算立体库CUBE的顶点坐标
        """
        self.manifest_col_name = manifest_col_name
        self.yaw_only = yaw_only
        self.has_pointCount = has_pointCount
        self.number_adapter_func = number_adapter_func
        self.parse_id_col = parse_id_col
        self.seq_start = seq_start
        self.filter_frame = filter_frame
        self.key_frames = key_frames
        self.allow_only_3d = allow_only_3d
        self.allow_only_2d = allow_only_2d
        self.gen_img_size = gen_img_size
        self.overflow = overflow
        if self.gen_img_size is True or self.overflow is False:
            print(f"谨慎选择！！！获取图片尺寸时间过长")
        self.cube_vertexes = cube_vertexes


if __name__ == "__main__":
    pass
    # from pprint import pprint
    # import pandas as pd
    #
    # lidar = LidarBoxParse(
    #     ### 对于长时间没有修改过的数据，数据url链接会失效，需要打回重新提交更新flowData.base_url
    #     url="appen://appen-platform/tool/aaaaaaaa-pppp-pppp-eeee-nnnnnnnnnnnn/766d8ab5-2802-4d29-a013-65fc18371688/4b1c9c52-5947-40a3-b786-c147463e673a/R.1735198368516.4b1c9c52-5947-40a3-b786-c147463e673a.CMvNtQUQAA3d3d_2024-12-26T065642Z.12988.result.json",
    #     # url=pd.read_csv("/Users/echai/Downloads/2025-01-06T08_22_34.477893Z-report.csv").to_dict(orient="records")[0]["annotation"],
    #     config=LidarBoxDataConfig(
    #         manifest_col_name="base_url",
    #         yaw_only=True,
    #         has_pointCount=30,
    #         number_adapter_func=None, # lambda i: round(i,3), # 默认None
    #         parse_id_col="id", # "gid",
    #         seq_start=0,
    #         filter_frame=None,
    #         key_frames=None,
    #         allow_only_3d=False,
    #         allow_only_2d=False,
    #         overflow=True,
    #         gen_img_size=False,
    #         cube_vertexes=True,
    #     ))
    # pprint(lidar.check_frames_error())
    # pprint(json.loads(lidar.frames_lst[0].log.format_a9_error_str()))
    # pprint(lidar.frames_lst[0].lidar_dict)
    # for k,v in lidar.frames_lst[0].lidar_dict.items():
    #     if v.type in ["CUBE", "RECTANGLE3"]:
    #         print(k,v.position,v.pointCount,v.attributes)
    #         try:
    #             print(dict_adapter(v.position, rename={"x": "k", "y": "x"}, out_adapter=None))
    #         except Exception as erx:
    #             print(erx)
    #             print(dict_adapter(v.position, rename={"x": "k", "y": "v"}, out_adapter=None))
    #     else:
    #         print(k,v.shapeData,v.attributes)
    # pprint(lidar.frames_lst[0].relations)
    # pprint(lidar.frames_lst[0].type_lidar_dict)
    # pprint(lidar.frames_lst[1].lidar_dict)
    # pprint(lidar.frames_lst[0].lidar_dict[1])
    # print(lidar.frames_lst[0].log.fomart_error_str())
    #
    # print(lidar.frames_lst[0].camera_idx2name)
    # print(lidar.frames_lst[0].camera_meta)
    # pprint(lidar.frames_lst[0].projection_image_dict)
    # print(lidar.frames_lst[0].only_image_dict)

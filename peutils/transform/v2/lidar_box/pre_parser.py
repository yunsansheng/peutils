#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: echai
Date: 2024-12-26
Short Description:

{
    "cameraInfoList": [
        {
            "name": "C0",
            "index": 0,
            "attributes": {
                "is_font": "1"
            }
        },
        {
            "name": "C1",
            "index": 1,
            "attributes": {
                "is_font": "0"
            }
        },
        {
            "name": "C2",
            "index": 2,
            "attributes": {
                "is_font": "0"
            }
        },
        {
            "name": "C3",
            "index": 3,
            "attributes": {
                "is_font": "0"
            }
        }
    ],
    "frameInfo": {
        "groundY": 0
    },
    "attributes": {
        "other_doubtful": "123\n"
    },
    "points": [
        {
            "url": "https://appen-data.oss-cn-shanghai.aliyuncs.com/appen%2Ftest_case%2F20231204_134514919518%2Fefan%2Fjust%2FAopeng-det-zdata-7_2-3565_pcd1016_img12192%2FZL00104_13028_zelos_sample_2024-07-18_19-52-00_000000000_1230478_bev%2FLIDAR_FUSED%2F0000_0_1721303521617628682.pcd?Expires=1735873200&OSSAccessKeyId=LTAI5tB2Etp2wUEVtkT7zckM&Signature=%2FVnwjIxvEywa9UU3hO5c0Jq%2BdLM%3D",
            "count": 350218
        },
        {
            "url": "https://appen-data.oss-cn-shanghai.aliyuncs.com/appen%2Ftest_case%2F20231204_134514919518%2Fefan%2Fjust%2FAopeng-det-zdata-7_2-3565_pcd1016_img12192%2FZL00104_13028_zelos_sample_2024-07-18_19-52-00_000000000_1230478_bev%2FLIDAR_FUSED%2F0000_0_1721303521617628682.pcd?Expires=1735873200&OSSAccessKeyId=LTAI5tB2Etp2wUEVtkT7zckM&Signature=%2FVnwjIxvEywa9UU3hO5c0Jq%2BdLM%3D",
            "count": 350218
        }
    ],
    "instances": [
        {
            "number": 1,
            "id": "7e48525f-0b2c-4cb2-80b6-6f33494e76de",
            "category": "car",
            "createTime": 1734846508527,
            "updateTime": 1734846508527,
            "attributes": {
                "ist_0": "0"
            },
            "shapes": [
                {
                    "id": "358d9f50-8ac1-4202-b760-ac40384a2f33",
                    "name": "2D-1",
                    "number": 1,
                    "type": "rectangle",
                    "createTime": 1735009287371,
                    "updateTime": 1735009287371,
                    "interpolated": false,
                    "shapeData": {},
                    "projectMethod": "PROJECT_BY_ADD",
                    "cameraIndex": 0,
                    "parent": "ce6b0459-b4fd-4172-9623-9ff51b8e0491",
                    "createWorker": "uuuuuuuu-uuuu-uuuu-uuuu-666666666666",
                    "updateWorker": "uuuuuuuu-uuuu-uuuu-uuuu-666666666666"
                },
                {
                    "id": "ce6b0459-b4fd-4172-9623-9ff51b8e0491",
                    "name": "3D",
                    "number": 1,
                    "type": "CUBE",
                    "createTime": 1734846508527,
                    "updateTime": 1735009984756,
                    "interpolated": false,
                    "shapeData": {},
                    "attributes": {
                        "Occlusion": "0"
                    },
                    "pointCount": {
                        "total": 12,
                        "count": {
                            "main": 6,
                            "3D": 6
                        }
                    },
                    "createWorker": "uuuuuuuu-uuuu-uuuu-uuuu-666666666666",
                    "updateWorker": "uuuuuuuu-uuuu-uuuu-uuuu-666666666666"
                }
            ]
        },
    ]
    "frame": 0,
    "relations": [
        {  # 静态中心线
            "sourceId": "b6d7bc84-a169-405d-9d19-9804eb66342e",
            "targetId": "3c644108-db53-4868-94ae-d28208a2168f",
            "type": 0,
            "lineVertices": [
                [
                    8.442609786987305,
                    -2.9527611136436462,
                    -2.1320650577545166
                ],
                [
                    11.6214756676249,
                    -2.519880842243446,
                    -1.1383077698260982
                ],
                [
                    16.794550882995424,
                    -2.747589639856153,
                    -1.191718056140014
                ],
                [
                    17.67825499062313,
                    -2.626004557438868,
                    -0.8317324128264391
                ],
                [
                    19.785904909434908,
                    -2.527884025129546,
                    -1.144618034362793
                ]
            ],
            "frame": 0,
            "id": "50ad2824-4de4-456c-a7f7-f8d751d7d41f",
            "positions": {},
            "number": 2,
            "attributes": {  # 中心线图像属性
                "statis_center_attr": "a"
            }
        },
        {
            "description": "从属",
            "sourceType": "SHAPE_ITEM",
            "targetId": "ce6b0459-b4fd-4172-9623-9ff51b8e0491",
            "targetType": "SHAPE_ITEM",
            "sourceId": "6429ac81-f12a-46bb-9e23-731842c7676e",
            "frame": 0,
            "type": 1
        },
        {
            "description": "从属",
            "sourceType": "SHAPE_ITEM",
            "targetId": "6429ac81-f12a-46bb-9e23-731842c7676e",
            "targetType": "SHAPE_ITEM",
            "sourceId": "ce6b0459-b4fd-4172-9623-9ff51b8e0491",
            "frame": 0,
            "type": 1
        },
        {
            "description": "覆盖",
            "sourceType": "SHAPE_ITEM",
            "targetId": "ce6b0459-b4fd-4172-9623-9ff51b8e0491",
            "targetType": "SHAPE_ITEM",
            "sourceId": "6429ac81-f12a-46bb-9e23-731842c7676e",
            "frame": 0,
            "type": 1
        }
    ]
}
Change History: 
"""
import sys
import json
from peutils.datautil import GenCategorySeq
from peutils.transform.v2.base import LidarInstance, Lidar2dObj, Lidar3dObj, LidarCUBEObj, BitArray, gen_uuid
from peutils.transform.v2.lidar_manifest.parser import LidarManifestParse
from typing import Union,Dict


class LidarBoxPre():
    def __init__(self, camera_name_list: Union[list, None]=None, frame_length: Union[int, None]=None, manifest_data: Union[LidarManifestParse, None]=None):
        if manifest_data is None:
            assert camera_name_list is not None and frame_length is not None, f"camera_name_list and frame_length are required when manifest_data is None."
            self.frame_length = frame_length
            self.camera_name_list = camera_name_list
        else:
            self.frame_length = manifest_data.frame_length
            self.camera_name_list = list(manifest_data.cameras_dict.keys())

        self.instance_seq = GenCategorySeq()
        self.lidar_seq = GenCategorySeq()
        self.img_seq = GenCategorySeq()

        # 记录关键信息
        self.instance_obj_dict = dict()  # {frameId: {id: xxx}}
        self.instance_track = dict()  # {id: number}  # tracking
        self.lidar_track = dict()  # {id: number}  # tracking
        self.img_track = dict()  # {id: number}  # tracking

    def add_instance_obj(
            self, frameId, category, istId: Union[str, None]=None,
            dynamicAttrs: Union[dict, None]=None,
    ):
        istId = f"IST_{gen_uuid()}" if istId is None else f"IST_{istId}"

        # 获取track number
        if istId in self.instance_track:
            number = self.instance_track[istId]
        else:
            number = self.instance_seq.up_seq(category)
            self.instance_track[istId] = number

        # id 每帧都是唯一的，frameId+uuid全局唯一
        self.instance_obj_dict.setdefault(frameId, {})
        if istId not in self.instance_obj_dict[frameId]:
            instanceObj = LidarInstance(
                frameId=frameId, id=istId, category=category, number=number,
                attributes=dynamicAttrs if dynamicAttrs else {}  # 动态属性
            )
            self.instance_obj_dict[frameId][istId] = instanceObj

        return self.instance_obj_dict[frameId][istId]

    def add_img_obj(
            self, instance, category, shapeType, shapeData, cameraIndex: int,
            shapeId: Union[str, None]=None, parent: Union[str, None]=None, dynamicAttrs: Union[dict, None]=None,
    ):
        frameId = instance.frameId
        istId = instance.id
        shapeId = f"IMG_{gen_uuid()}" if shapeId is None else f"IMG_{shapeId}"

        seq_by = f'{istId}_{cameraIndex}_{category}'
        # 获取track number
        if shapeId in self.img_track:
            number = self.img_track[shapeId]
        else:
            number = self.img_seq.up_seq(seq_by)
            self.img_track[shapeId] = number

        obj = Lidar2dObj(
            frameId=frameId, instance=instance,
            id=shapeId, category=category, number=number,
            cameraIndex=cameraIndex, type=shapeType, shapeData=shapeData, attributes=dynamicAttrs, parent=parent,
        )
        self.instance_obj_dict[frameId][istId].shapes.append(obj)

        return obj

    def add_lidar_obj(
            self, instance, category, shapeType, shapeData,
            shapeId: Union[str, None]=None, dynamicAttrs: Union[dict, None]=None,
    ):
        # shapeType = ("POLYLINE3", "POLYGON3", "CURVE3", "POINT3", 'POINTS', 'CUBE'(没有pointCount时也适用), 'RECTANGLE3')
        frameId = instance.frameId
        istId = instance.id
        shapeId = f"LIDAR_{gen_uuid()}" if shapeId is None else f"LIDAR_{shapeId}"

        seq_by = f'{istId}_{category}'
        # 获取track number
        if shapeId in self.lidar_track:
            number = self.lidar_track[shapeId]
        else:
            number = self.lidar_seq.up_seq(seq_by)
            self.lidar_track[shapeId] = number

        obj = Lidar3dObj(
            frameId=frameId, instance=instance,
            id=shapeId, category=category, number=number,
            type=shapeType, shapeData=shapeData, attributes=dynamicAttrs,
        )
        self.instance_obj_dict[frameId][istId].shapes.append(obj)

        return obj

    def add_CUBE_obj(
            self, instance, category, shapeType, position, dimension, quaternion, vertexes=None, pointCount=None,
            shapeId: Union[str, None]=None, dynamicAttrs: Union[dict, None]=None,
    ):
        # shapeType = ('CUBE', 'RECTANGLE3')
        if shapeType == "RECTANGLE3":
            assert vertexes is not None, "Of type RECTANGLE3, vertexes is required."
        frameId = instance.frameId
        istId = instance.id
        shapeId = f"LIDAR_{gen_uuid()}" if shapeId is None else f"LIDAR_{shapeId}"

        seq_by = f'{istId}_{category}'
        # 获取track number
        if shapeId in self.lidar_track:
            number = self.lidar_track[shapeId]
        else:
            number = self.lidar_seq.up_seq(seq_by)
            self.lidar_track[shapeId] = number

        obj = LidarCUBEObj(
            frameId=frameId, instance=instance,
            id=shapeId, category=category, number=number, type=shapeType, shapeData=None,
            position=position, dimension=dimension, quaternion=quaternion, vertexes=vertexes, pointCount=pointCount,
            attributes=dynamicAttrs,
        )
        self.instance_obj_dict[frameId][istId].shapes.append(obj)

        return obj

    def dumps_data(
            self, globalAttrs: Union[Dict, None]=None, instanceStaticAttrs: Union[dict, None]=None,
            frames_attrs_3d: Union[dict, None]=None, frames_attrs_2d: Union[dict, None]=None,
            relations: Union[dict, None]=None,
    ):
        """
        Args:
            globalAttrs: 全局属性。{全局属性key: 全局属性value}
            instanceStaticAttrs: 实例的静态属性。 {instance.id: {静态属性key: 静态属性value}}
            frames_attrs_3d: 3d帧属性。 {frameId: {属性key: 属性value}}
            frames_attrs_2d: 2d帧属性。 {frameId: {camera: {属性key: 属性value}}} or {camera: {frameId: {属性key: 属性value}}}
            relations: {frameId: [{覆盖、从属、静态中心线等键值对}, {}, {}, ···]}
        Returns:

        """
        staticAttributes = dict()
        if globalAttrs is not None:
            staticAttributes["global"] = globalAttrs
        if instanceStaticAttrs:
            staticAttributes["instance"] = instanceStaticAttrs

        if relations is None:
            relations = dict()

        frames_list = list()
        for frameId in range(self.frame_length):
            optional_keys = dict()
            if frames_attrs_3d:
                # 3D帧属性
                optional_keys["attributes"] = frames_attrs_3d.get(frameId, {})
            if frames_attrs_2d:
                # 2D帧属性
                frame_cameraInfoList = list()
                for cam_idx, cam_name in enumerate(self.camera_name_list):
                    if isinstance(list(frames_attrs_2d.keys())[0], int):
                        frame_cameraInfoList.append({
                            "name": cam_name,
                            "index": cam_idx,
                            "attributes": frames_attrs_2d.get(frameId, {}).get(cam_name, {})
                        })
                    else:
                        frame_cameraInfoList.append({
                            "name": cam_name,
                            "index": cam_idx,
                            "attributes": frames_attrs_2d.get(cam_name, {}).get(frameId, {})
                        })

            frames_list.append({
                **optional_keys,
                "instances": [ist_obj.to_dict() for ist_id, ist_obj in self.instance_obj_dict.get(frameId, {}).items()],
                "frame": frameId,
                "relations": relations.get(frameId, [])
            })

        out_dict = {
            "frames": frames_list,
            "staticAttributes": staticAttributes,
        }
        return json.dumps(out_dict, ensure_ascii=False)

if __name__ == "__main__":
    pass
    # ### lidar_pre类的两种创建方式
    # # from peutils.transform.v2.lidar_manifest.parser import LidarManifestParse, LidarManifestConfig
    # # lidar_pre = LidarBoxPre(manifest_data=LidarManifestParse(base_url="url or manifest dict", config=LidarManifestConfig()))
    # lidar_pre = LidarBoxPre(frame_length=3, camera_name_list=["C1", "C2"])
    #
    # ### 所有id必须保证同帧唯一，否则预标框会被覆盖，加载框少于实际预标框。最好在脚本里统计框数做校验。
    #
    # ist_obj = lidar_pre.add_instance_obj(frameId=0, category=f'car', istId="a1")
    # ### 不带pointCount的CUBE有两种方式add_lidar_obj、add_CUBE_obj。带pointCount的CUBE只能使用add_CUBE_obj
    # lidar_obj = lidar_pre.add_lidar_obj(
    #     instance=ist_obj, category="3D", shapeId="lidar1", shapeType="CUBE",
    #     shapeData={
    #         "position": {"x": 1, "y": 1, "z": 1},
    #         "dimension": {"x": 1, "y": 1, "z": 1},
    #         "quaternion": {"x": 0, "y": 0, "z": 1, "w": 1},
    #     },
    # )
    # lidar_pre.add_CUBE_obj(
    #     instance=ist_obj, category="3D", shapeId="lidar2", shapeType="CUBE",
    #     position={"x": 1, "y": 1, "z": 1},
    #     dimension={"x": 1, "y": 1, "z": 1},
    #     quaternion={"x": 0, "y": 0, "z": 1, "w": 1},
    #     pointCount={'total': 3130, 'count': {'main': 1565, '3D': 1565}}
    # )
    # ### 图像框
    # lidar_pre.add_img_obj(
    #     instance=ist_obj,category="2D",shapeType="rect", shapeData={"x": 1, "y": 1, "width": 10, "height": 10},
    #     cameraIndex=0, shapeId="img1", parent=lidar_obj.id,
    #     dynamicAttrs={"only2d": "false"}
    # )
    # pre_data = json.loads(lidar_pre.dumps_data())


# -*- coding: UTF-8 -*-

'''
Author: Henry Wang
Date: 2022-05-30 13:08
Short Description:

Change History:

'''

from peutils.transform.v1.base import *
import json
from types import SimpleNamespace
from collections import defaultdict



class LidarBoxFrame():
    def __init__(self,frameId,frameUrl,isValid,frameUrlInternal,frameUrlExternal,
                 frame_attr,items,images,
                 config):
        self.frameId = frameId
        self.frameUrl = frameUrl
        self.isValid = isValid
        self.frameUrlInternal = frameUrlInternal
        self.frameUrlExternal = frameUrlExternal

        self.log = ErrorMsgLogV1()

        self.config = config

        self.frame_attr = frame_attr
        self.lidar_dict = self.get_lidar_dict(items)
        self.camera_list,self.camera_meta,self.images_dict= self.get_images_dict(images)
        self._img_idset = self.get_img_idset(self.images_dict)
        self.only_lidar_idset= self.lidar_dict.keys() - self._img_idset # 只有3D 没有出现在2D的ID
        self.only_image_idset = self._img_idset -  self.lidar_dict.keys() # 只出现在2D没有出现在3D中的ID
        self.has_23d_idset = self.lidar_dict.keys() & self._img_idset # 2D和3D都出现


    @staticmethod
    def get_img_idset(images_dict):
        img_idset = set()
        for _,v in images_dict.items():
            img_idset = img_idset | v.keys()
        return img_idset

    def get_img_obj_list(self,id,keep_nan=False):
        lst = []
        for cam in self.camera_list:
            obj = self.images_dict[cam].get(id)
            if keep_nan == True:
                lst.append(obj)
            else:
                if obj:
                    lst.append(obj)
        return lst


    def parse_lidar_by_item(self,item):
        frameNum = item["frameNum"]
        id = item["id"]
        number= item["number"]
        category = item["category"]
        # print(self.config)
        rotation =  dict_adapter(item["rotation"],out_adapter=self.config.number_adpter_func)
        position = dict_adapter(item["position"],out_adapter=self.config.number_adpter_func)
        dimension = dict_adapter(item["dimension"],out_adapter=self.config.number_adpter_func)
        ## 四元数
        quaternion =dict_adapter(item["quaternion"],out_adapter=self.config.number_adpter_func)

        ### 解析属性
        if item.get("labels") is None:
            lidar_attr = dict()
        else:
            lidar_attr = json.loads(item["labels"])

        ### 解析点云数量
        if item.get("pointCount") and item.get("pointCount").get("lidar"):
            pointCount = item["pointCount"]["lidar"]
        else:
            pointCount = None


        '''
        检查逻辑
        1.如果yaw_only True,检查 rotation x 和 y都是0
        2.如果has_pointCount是True,检查pointCount 不是None
        '''
        lidar_obj = Lidar3dObj(
            frameNum= frameNum,
            id = id,
            number=number,
            category=category,
            position= position,
            rotation= rotation,
            dimension = dimension,
            quaternion = quaternion,
            lidar_attr = lidar_attr,
            pointCount = pointCount
        )

        if self.config.parse_id_col =="id":
            key = id
        elif self.config.parse_id_col =="number":
            key = number
        else:
            raise Exception("parse_id_col解析模式只能是id或者number")

        ####业务检查
        if self.config.has_pointCount == True and lidar_obj.pointCount is None:
            self.log.create_error(msg="点云数量不能为空",obj=lidar_obj)

        if self.config.yaw_only ==True:
            if lidar_obj.rotation["x"] !=0 or lidar_obj.rotation["y"] !=0:
                self.log.create_error(msg="仅水平旋转x y应该为0",obj=lidar_obj)

        return key,lidar_obj

    def parse_img_by_item(self,item,width,height):
        frameNum = item["frameNum"]
        imageNum = item["imageNum"]
        id = item["id"]
        number = item["number"]
        rect_type = item["type"]
        category = item["category"]

        position = dict_adapter(item["position"], out_adapter=self.config.number_adpter_func)
        dimension = dict_adapter(item["dimension"], out_adapter=self.config.number_adpter_func)

        ### 解析属性
        if item.get("labels") is None:
            img_attr = dict()
        else:
            img_attr = json.loads(item["labels"])

        '''
        检查逻辑
        1.图像是否超出边界外

        '''
        if rect_type =="RECT":
            img_obj = Lidar3dImageRect(
                frameNum=frameNum,
                imageNum=imageNum,
                id=id,
                number=number,
                type=rect_type,
                category=category,
                position=position,
                dimension=dimension,
                img_attr=img_attr,
            )
        else:
            # 暂时不会遇到
            img_obj =None

        if self.config.parse_id_col == "id":
            key = id
        elif self.config.parse_id_col == "number":
            key = number
        else:
            raise Exception("parse_id_col解析模式只能是id或者number")

        if self.config.overflow ==False:
            if img_obj.position["x"] <0 or img_obj.position["y"]<0 \
                    or (img_obj.position["x"] + img_obj.dimension["x"]) > width \
                    or (img_obj.position["y"] + img_obj.dimension["y"]) >height:
                self.log.create_error(msg="图像超出边界",obj=img_obj)

        return key, img_obj


    def get_lidar_dict(self,items):
        lidar_dict = dict()

        for item in items:
            key,lidar_obj =self.parse_lidar_by_item(item=item)
            lidar_dict[key] = lidar_obj

        if len(items) != len(lidar_dict):
            raise Exception(f"{self.config.parse_id_col} 解析模式下数量不等，请检查使用参数")
        return lidar_dict

    def get_single_image_dict(self,items,width,height):
        single_image_dict = dict()

        for item in items:
            if item["type"] =="RECT":
                key,img_obj = self.parse_img_by_item(item,width,height)
                single_image_dict[key] = img_obj
            else:
                raise Exception("目前图像物体仅支持RECT,其他类型还在开发中")

        if len(items) != len(single_image_dict):
            raise Exception(f"{self.config.parse_id_col} 解析模式下数量不等，请检查使用参数")
        return single_image_dict

    def get_images_dict(self,images):
        ### 先解析出镜头数量
        images_dict = dict()
        camera_list = []
        camera_meta = dict()
        for img in images:
            image_path = img["image"]
            camera_name = image_path.split("/")[-2]
            camera_list.append(camera_name)

            camera_meta[camera_name]= {
                "image_path":image_path,
                "imageUrlInternal":img["imageUrlInternal"],
                "imageUrlExternal":img["imageUrlExternal"],
                "width": img["width"],
                "height": img["height"],
            }
            images_dict[camera_name] = self.get_single_image_dict(img["items"],width=img["width"],height = img["height"])

        ## check
        if len(camera_list) != len(images):
            raise Exception("找到的镜头数量和原始不一致")

        return camera_list,camera_meta,images_dict


    def __repr__(self):
        return f'Frame {self.frameId}'




class LidarBoxParse(CommonBaseMixIn):

    ### 继承session属性 用来读取url
    def __init__(self,url,config):
        self.url = url
        self.config = config
        self.raw_data = self.get_raw_data(url) # 获取JSON字典数据数据

        self.frames_lst = self.parse_by_frame()


    def parse_by_frame(self):
        '''
        返回解析后的frame列表，对应的数据
        '''
        #
        frames_lst = []
        for raw_frame in self.raw_data["frames"]:

            ### 属性
            attribute = raw_frame.get("attribute")
            if attribute:
                frame_attr = json.loads(attribute)
            else:
                frame_attr = dict()

            frame = LidarBoxFrame(
                frameId=raw_frame["frameId"],
                frameUrl=raw_frame["frameUrl"],
                isValid=raw_frame["isValid"],
                frameUrlInternal=raw_frame["frameUrlInternal"],
                frameUrlExternal=raw_frame["frameUrlExternal"],
                frame_attr = frame_attr,
                items = raw_frame["items"],
                images = raw_frame["images"],
                config= self.config
            )
            frames_lst.append(frame)
        return frames_lst



class LidarBoxDataConfig():
    def __init__(self,yaw_only=True,has_pointCount=True,number_adpter_func=None,
                 parse_id_col="id",overflow=False):
        self.yaw_only = yaw_only
        self.has_pointCount = has_pointCount
        self.number_adpter_func = number_adpter_func
        self.parse_id_col = parse_id_col # id或number
        self.overflow = overflow # 默认不允许超出图像边界

from pprint import pprint

if __name__ =="__main__":
    ## 单帧
    from pprint import pprint
    lidar = LidarBoxParse(url="http://oss.prd.appen.com.cn:9000/appen-lidar-prod/15a7d17dd9ff2d831e0523421b1798e3/R.1647329777003.7628df30-4735-40fe-a641-b8210e11e00e.CLnhugEQJA3d3d_2022-03-15T073140Z.16644.QA_RW.f5079a20-5bef-478f-b9c5-a19f84227acd.27d74dc726f51f05e31f2206fda11714.review.json",
                         config =LidarBoxDataConfig(
                             yaw_only = True,
                             has_pointCount= True,
                             number_adpter_func=None, #lambda i: round(i,3), # 默认None
                             parse_id_col = "id",
                             overflow= False
                         ))
    pprint(lidar.frames_lst[0].lidar_dict["06e41560-32ac-436d-a0c0-3e4aae7d4858"].rotation)
    print(lidar.frames_lst[0].log.error_list)
    # p = lidar.frames_lst[0].lidar_dict["06e41560-32ac-436d-a0c0-3e4aae7d4858"].position
    # print(dict_adapter(p,rename={"x":"k","y":"x"},out_adapter=None))
    # {'x': 18.690793403437375, 'y': -56.18997617593776, 'z': -1.380000000000006}

    # print(lidar.frames_lst[0].camera_list)
    # print(lidar.frames_lst[0].camera_meta)
    # pprint(lidar.frames_lst[0].images_dict)
    # print(lidar.frames_lst[0].only_image_idset)
    # print(lidar.frames_lst[0].get_img_obj_list(id="f661d8a6-ad24-4f95-b034-67983b17709f"))
    # print(lidar.frames_lst[0].get_img_obj_list(id="f661d8a6-ad24-4f95-b034-67983b17709f",keep_nan=True))





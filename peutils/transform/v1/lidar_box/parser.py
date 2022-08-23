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
from peutils.datautil import gen_uuid_seq



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
        if self.config.parse_id_col =="fid":
            self.config.seq_func = gen_uuid_seq(start=self.config.seq_start)

        self.frame_attr = frame_attr
        self.lidar_dict = self.get_lidar_dict(items)
        self.camera_list,self.camera_meta,self.images_dict,self.images_list= self.get_images_dict(images)
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

        rotation =  dict_adapter(item["rotation"],out_adapter=self.config.number_adpter_func)
        position = dict_adapter(item["position"],out_adapter=self.config.number_adpter_func)
        dimension = dict_adapter(item["dimension"],out_adapter=self.config.number_adpter_func)
        ## 四元数
        quaternion =dict_adapter(item["quaternion"],out_adapter=self.config.number_adpter_func)

        ### 解析点云数量
        if item.get("pointCount") and item.get("pointCount").get("lidar") is not None:
            pointCount = item["pointCount"]["lidar"]
        else:
            pointCount = None


        '''
        检查逻辑
        1.如果yaw_only True,检查 rotation x 和 y都是0
        2.如果has_pointCount是True,检查pointCount 不是None
        '''
        lidar_obj = Lidar3dObj(
            frameNum= self.frameId, #item["frameNum"],
            id = item["id"],
            number= item["number"],
            category=item["category"],
            position= position,
            rotation= rotation,
            dimension = dimension,
            quaternion = quaternion,
            lidar_attr = json.loads(item["labels"]) if item.get("labels") else dict(),
            pointCount = pointCount
        )

        if self.config.parse_id_col =="id":
            key = item["id"]
        elif self.config.parse_id_col =="number":
            key = item["number"]
        elif self.config.parse_id_col in ("gid","fid"):
            key = self.config.seq_func(item["id"])
        else:
            raise Exception("parse_id_col解析模式错误")

        ####业务检查
        if self.config.has_pointCount == True and lidar_obj.pointCount is None:
            self.log.create_error(msg="点云数量不能为空",obj=lidar_obj)

        if self.config.yaw_only ==True:
            if lidar_obj.rotation["x"] !=0 or lidar_obj.rotation["y"] !=0:
                self.log.create_error(msg="仅水平旋转x y应该为0",obj=lidar_obj)


        return key,lidar_obj

    def parse_img_by_item(self,item,width,height):

        position = dict_adapter(item["position"], out_adapter=self.config.number_adpter_func)
        dimension = dict_adapter(item["dimension"], out_adapter=self.config.number_adpter_func)

        '''
        检查逻辑
        1.图像是否超出边界外

        '''
        if item["type"] in {"RECT","VANISH_CUBE","RECT_CUBE"}:
            points = None
            rect1 = None
            rect2 = None

            if item["type"] =="VANISH_CUBE":
                points = item["points"]

            if item["type"] =="RECT_CUBE":
                rect1 = item["rect1"]
                rect2 = item["rect2"]


            img_obj = Lidar3dImageRect(
                frameNum= self.frameId, #item["frameNum"],
                imageNum=item["imageNum"],
                id=item["id"],
                number=item["number"],
                type=item["type"],
                category=item["category"],
                position=position,
                dimension=dimension,
                img_attr=json.loads(item["labels"]) if item.get("labels") else dict(),
                points = points,
                rect1 = rect1,
                rect2 = rect2
            )

        else:
            # 暂时不会遇到
            img_obj =None

        if self.config.parse_id_col == "id":
            key = item["id"]
        elif self.config.parse_id_col == "number":
            key = item["number"]
        elif self.config.parse_id_col in ("gid","fid"):
            key = self.config.seq_func(item["id"])
        else:
            raise Exception("parse_id_col解析模式错误")

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
            if item["type"] in {"RECT","VANISH_CUBE","RECT_CUBE"}:
                key,img_obj = self.parse_img_by_item(item,width,height)
                single_image_dict[key] = img_obj
            else:
                raise Exception("目前图像物体仅支持RECT VANISH_CUBE RECT_CUBE,其他类型还在开发中")

        if len(items) != len(single_image_dict):
            raise Exception(f"{self.config.parse_id_col} 解析模式下数量不等，请检查使用参数")
        return single_image_dict

    def get_images_dict(self,images):
        ### 先解析出镜头数量
        images_dict = dict() #{cam:dict1,cam2:dict2,...}
        images_list = [] #[dict1,dict2,..]
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
            sg_img_dict = self.get_single_image_dict(img["items"],width=img["width"],height = img["height"])
            images_dict[camera_name] = sg_img_dict
            images_list.append(sg_img_dict)

        ## check
        if len(camera_list) != len(images):
            raise Exception("找到的镜头数量和原始不一致")

        return camera_list,camera_meta,images_dict,images_list


    def __repr__(self):
        return f'Frame {self.frameId}'




class LidarBoxParse(CommonBaseMixIn):

    ### 继承session属性 用来读取url
    def __init__(self,url,config):
        self.url = url
        self.config = config
        if self.config.parse_id_col == "gid":
            self.config.seq_func = gen_uuid_seq(start=self.config.seq_start)

        self.raw_data = self.get_raw_data(url) # 获取JSON字典数据数据
        self.frames_lst, self.frame_length = self.parse_by_frame()


    def check_frames_error(self):
        all_errors = []
        for frame in self.frames_lst:
            all_errors.extend(frame.log.error_list)
        return all_errors


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
                if isinstance(attribute,dict):
                    frame_attr = DotDict(attribute)
                else:
                    frame_attr = DotDict(json.loads(attribute))
            else:
                frame_attr = DotDict()

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
        return frames_lst,len(frames_lst)



class LidarBoxDataConfig():
    def __init__(self,yaw_only=True,has_pointCount=True,number_adpter_func=None,
                 parse_id_col="id",seq_start=0,overflow=False):
        self.yaw_only = yaw_only
        self.has_pointCount = has_pointCount
        self.number_adpter_func = number_adpter_func
        self.parse_id_col = parse_id_col # id或number ,gid, fid
        self.seq_start = seq_start
        self.overflow = overflow # 默认不允许超出图像边界

from pprint import pprint

if __name__ =="__main__":
    ## 单帧
    from pprint import pprint
    lidar = LidarBoxParse(url="https://oss-prd.appen.com.cn:9001/tool-prod/6e3149fd2e517f8ead3102ef2b23a55d/R.1654671141185.762645cb-d524-42b8-b5c2-217c002b2066.CLuksAIQAA3d3d_2022-06-08T065143Z.18179.QA_RW.4a1fb325-19b0-4dc4-92d4-c4a95eb29831.38888b56a8a16cda2f27473749a89622.review.json",
                         config =LidarBoxDataConfig(
                             yaw_only = True,
                             has_pointCount= True,
                             number_adpter_func=None, #lambda i: round(i,3), # 默认None
                             parse_id_col = "gid",
                             seq_start = 0, # 如果是 gid,fid,或者frame_id 需要提供seq_start， 如果是0就是从1开始编号，如果是-1就是从0开始编号
                             overflow= False
                         ))
    # pprint(lidar.check_frames_error())
    # pprint(lidar.frames_lst[0].lidar_dict)
    # for k,v in lidar.frames_lst[0].lidar_dict.items():
    #     print(k,v.position,v.pointCount,v.lidar_attr)
    # pprint(lidar.frames_lst[1].lidar_dict)
    # pprint(lidar.frames_lst[0].lidar_dict["06e41560-32ac-436d-a0c0-3e4aae7d4858"].rotation)
    # print(lidar.check_frames_error())
    # print(lidar.frames_lst[7].log.fomart_error_str())
    # print(lidar.check_frames_error())
    # print(json.dumps(lidar()))
    # p = lidar.frames_lst[0].lidar_dict["06e41560-32ac-436d-a0c0-3e4aae7d4858"].position
    # print(dict_adapter(p,rename={"x":"k","y":"x"},out_adapter=None))
    # {'x': 18.690793403437375, 'y': -56.18997617593776, 'z': -1.380000000000006}

    # print(lidar.frames_lst[0].camera_list)
    # print(lidar.frames_lst[0].camera_meta)
    # pprint(lidar.frames_lst[0].images_dict)
    # pprint(lidar.frames_lst[0].images_list)
    # print(lidar.frames_lst[0].only_image_idset)
    # print(lidar.frames_lst[0].get_img_obj_list(id="f661d8a6-ad24-4f95-b034-67983b17709f"))
    # print(lidar.frames_lst[0].get_img_obj_list(id="f661d8a6-ad24-4f95-b034-67983b17709f",keep_nan=True))





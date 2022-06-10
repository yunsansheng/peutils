# -*- coding: UTF-8 -*-

'''
Author: Henry Wang
Date: 2022-06-09 14:51
Short Description:

Change History:

'''
from peutils.transform.v1.base import *
import json
from peutils.datautil import gen_uuid_seq


class ImgComFrame():
    def __init__(self,frameId,frameUrl,isValid,imageWidth,imageHeight,
                 rotation,
                 frame_attr,
                 config):
        self.frameId = frameId
        self.frameUrl = frameUrl
        self.isValid = isValid
        self.imageWidth = imageWidth
        self.imageHeight = imageHeight
        self.rotation =rotation

        self.log = ErrorMsgLogV1()
        self.config = config
        self.frame_attr = frame_attr
        self.frame_obj_list = []


    def add_frame_obj(self,obj:Img2Dobj):
        if obj.order is None:
            self.log.create_error("order检查模式下不能缺失",obj=obj)
        self.frame_obj_list.append(obj)


    def __repr__(self):
        return f'Frame {self.frameId} {len(self.frame_obj_list)}T'


class ImgComParse(CommonBaseMixIn):

    ### 继承session属性 用来读取url
    def __init__(self,url,config):
        self.url = url
        self.config = config
        self.raw_data = self.get_raw_data(url) # 获取JSON字典数据数据
        self.instance_lst,self.object_lst = self.parse_by_instance()
        self.frames_lst = self.parse_by_frame()


    def check_frames_error(self):
        all_errors = []
        for frame in self.frames_lst:
            all_errors.extend(frame.log.error_list)
        return all_errors

    def parse_by_frame(self):
        frames_lst = []
        for raw_frame in self.raw_data["frames"][0]["frames"]: # 先解析default cam
            frame = ImgComFrame(
                frameId= raw_frame["frameIndex"],
                frameUrl= raw_frame["imageUrl"],
                imageWidth = raw_frame["imageWidth"],
                imageHeight = raw_frame["imageHeight"],
                isValid= raw_frame["valid"],
                rotation = raw_frame["rotation"],
                frame_attr= raw_frame.get("attributes") if raw_frame.get("attributes") else dict(),
                config=self.config
            )
            frames_lst.append(frame)

        for obj in self.object_lst:
            frames_lst[obj.frameNum].add_frame_obj(obj)

        ### 对order进行检查并且排序数据,缺失的数据排在最前面.
        for f in frames_lst:
            f.frame_obj_list.sort(key=lambda i: -1 if i.order is None else i.order)

        return frames_lst

    def parse_by_instance(self):

        instance_lst = []
        all_obj_lst = []
        for instance in self.raw_data["instances"]:
            ist = ImgInstance(
                id=instance["id"],
                category = instance["category"],
                categoryName = instance["categoryName"],
                categoryColor = instance["categoryColor"],
                number = instance["number"],
                ist_attr = instance.get("attributes") if instance.get("attributes") else dict()
            )
            obj_list = []
            for ch in instance["children"]:
                for obj in ch["cameras"][0]["frames"]: # 默认先只处理default cam
                    imgobj = Img2Dobj(
                        instance = ist,
                        frameNum= obj["frameIndex"],
                        id = ch["id"],
                        number = ch["number"],
                        category = ch["name"],
                        displayName = ch["displayName"],
                        color = ch["displayColor"],
                        shapeType = obj["shapeType"],
                        shape = obj["shape"],
                        order = obj.get("order"),# 测试None if ch["id"] =="faeb43ff-546b-4f80-b99b-8e4eeb62f112" else obj.get("order"),
                        img_attr = obj.get("attributes") if instance.get("attributes") else dict(),
                        isOCR= obj.get("isOCR",False),
                        OCRText= obj.get("OCRText","")
                    )
                    obj_list.append(imgobj)
            # 加到ist实例中
            all_obj_lst.extend(obj_list)
            ist.obj_list.extend(obj_list)
            instance_lst.append(ist)

        return instance_lst,all_obj_lst



class ImgComDataConfig():
    def __init__(self,parse_id_col="id",number_adpter_func=None,seq_start=0,check_order=True,overflow=False):
        self.number_adpter_func = number_adpter_func
        self.parse_id_col = parse_id_col, # 默认id ## 暂时不引入fid,gid
        self.check_order = check_order # 检查order 是否都存在
        self.seq_start = seq_start  # 暂时用不到
        self.overflow = overflow # 默认不允许超出图像边界



if __name__ =="__main__":
    ## 单帧
    from pprint import pprint
    img = ImgComParse(url="https://oss-prd.appen.com.cn:9001/tool-prod/a2a3ef0c-55c4-4d15-8cc2-ff6aeb7878dd/R.1650783983510.a2a3ef0c-55c4-4d15-8cc2-ff6aeb7878dd.CODU4AEQEg3d3d_2022-04-24T070156Z.18107.result.json",
                         config =ImgComDataConfig(
                         ))

    # pprint(img.instance_lst)
    # pprint(img.object_lst)
    # pprint(img.frames_lst)
    # pprint(img.frames_lst[0].)
    # img.frames_lst[9].frame_obj_list.sort(key=lambda i: i.order)
    pprint(img.frames_lst[9].frame_obj_list)
    pprint(img.frames_lst[9].log.error_list)
    # pprint(img)
    # pprint(img.object_lst)

    # for frame in img.frames_lst:
    #     # print(frame.imageWidth)
    #     # print(frame.frame_obj_list)
    #     # print(frame.log.error_list)
    #     pprint(frame)
    # pprint(lidar.frames_lst[49].lidar_dict)
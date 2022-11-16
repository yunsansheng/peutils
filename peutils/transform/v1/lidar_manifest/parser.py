# -*- coding: UTF-8 -*-

'''
Author: Henry Wang
Date: 2022-06-01 16:19
Short Description:

Change History:

'''

from peutils.transform.v1.base import *
import os

class LidarManifestConfig():
    def __init__(self):
        pass


class LidarManifestParse(CommonBaseMixIn):

    ### 继承session属性 用来读取url
    def __init__(self,base_url,config):
        # self.raw_data = self.get_raw_data(os.path.join(base_url,"manifest.json"))
        self.raw_data = self.get_raw_data(base_url + "/manifest.json")
        self.config = config
        self.frame_length = self.get_frame_length()
        self.camera_list = self.get_camera_list()

    def get_frame_length(self):

        if self.raw_data["frames"].get("urls") is not None:
            f_num = len(self.raw_data["frames"].get("urls"))
        elif self.raw_data["frames"].get("data") is not None:
            f_num = len(self.raw_data["frames"].get("data"))
        else:
            raise Exception("MAINIFEST 未找到对应的帧数量")
        return f_num

    def get_camera_list(self):
        img_len = len(self.raw_data["images"])
        camera_list = [x["camera"] for x in self.raw_data["images"] ]
        # print(img_len,camera_list)
        if img_len != len(set(camera_list)):
            raise Exception(f"MAINIFEST 镜头数据解析错误 {camera_list}")

        return camera_list


# print(os.path.join("https://projecteng.oss-cn-shanghai.aliyuncs.com/3d_json/manifest/3615d49983984e7484ccd10dc8fc8f81/61d972a8910d7200e762ec55_9999_9999","manifest.json"))
if __name__ =="__main__":
    ## 单帧
    from pprint import pprint
    # mfst = LidarManifestParse(base_url="https://projecteng.oss-cn-shanghai.aliyuncs.com/3d_json/manifest/3615d49983984e7484ccd10dc8fc8f81/61d972a8910d7200e762ec55_9999_9999",
    #                      config =LidarManifestConfig())
    #
    # print(mfst.camera_list,mfst.frame_length)
    mfst = LidarManifestParse(
        base_url="https://projecteng.oss-cn-shanghai.aliyuncs.com/3d_json/manifest/23efe93357dd47a2877184a250bec73e/619c8ea93842dacdbf91b66e_351_400",
        config=LidarManifestConfig())

    print(mfst.camera_list, mfst.frame_length)

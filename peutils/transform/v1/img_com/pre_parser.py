# -*- coding: UTF-8 -*-

'''
Author: Henry Wang
Date: 2022-06-14 09:16
Short Description:

Change History:

预处理必须的数据结构
{
  "instances": [
    {
      "id": "xxx", // 唯一编号勿重复
      "category": "CAR", // 请对应模板配置
      "number": 1, // 同一category下勿重复
      "children": [
        {
          "id": "yyy", // 唯一编号勿重复
          "name": "车身", // 请对应模板配置
          "number": 1, // 同一instance，同一name下勿重复
          "cameras": [
            {
              "camera": "default", // 请对应模板数据（若为单相机，则默认为default）
              "frames": [
                {
                  "frameIndex": 0,
                  "isKeyFrame": true, // 预标数据默认为关键帧true
                  "shapeType": "polygon",
                  "shape": {} // 图形数据（不同图形的数据结构不同，详情参考下方图形数据结构说明）
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}



'''
import json
from peutils.transform.v1.base import *


class ImgComPre():
    ### 提供ImgComFrame实例对象frame_list，或者提供frame_length构造一个空的
    def __init__(self,frame_length,frames_lst=None):

        self.frame_length = frame_length

        if frames_lst is not None:
            self.frames_lst = [ f.to_pre_dict() for f in frames_lst]
        else:
            ### 构造空的
            self.frames_lst = [{
                "frameId": i,
                "frame_attr": dict(),
                "frame_items": [],
            } for i in range(self.frame_length)]






if __name__ =="__main__":
    from pprint import pprint
    from peutils.transform.v1.img_com.parser import ImgComParse,ImgComDataConfig
    img = ImgComParse(
        url="https://oss-prd.appen.com.cn:9001/tool-prod/a2a3ef0c-55c4-4d15-8cc2-ff6aeb7878dd/R.1650783983510.a2a3ef0c-55c4-4d15-8cc2-ff6aeb7878dd.CODU4AEQEg3d3d_2022-04-24T070156Z.18107.result.json",
        config=ImgComDataConfig(
        ))
    # print(img.frame_length)
    # print(img.frames_lst)

    imgpre = ImgComPre(frame_length=img.frame_length,frames_lst=img.frames_lst)
    pprint(imgpre.frames_lst)


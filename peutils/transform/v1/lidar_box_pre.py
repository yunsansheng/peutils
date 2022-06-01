# -*- coding: UTF-8 -*-

'''
Author: Henry Wang
Date: 2022-06-01 15:33
Short Description:

Change History:


主要用于预处理的数据转成平台的格式,平台最少的数据格式
{

	"frames": [{
		"frameId": 0,
		"items": [{
			"id": "669b1f5a-8eeb-40fe-8945-2dd8cec688a1",
			"number": 1,
			"position": {
				"x": -2.9164659842583536,
				"y": -51.38931599127634,
				"z": -1.8388888888888877
			},
			"rotation": {
				"x": 0,
				"y": 0,
				"z": -1.6618072479377624
			},
			"dimension": {
				"x": 4.2,
				"y": 1.8,
				"z": 1.6
			},
			"category": "轿车",
			"labels": "...json字符串..."
		}],
		"images": [
			[{
				"items": [{
					"type": "RECT",
					"id": "669b1f5a-8eeb-40fe-8945-2dd8cec688a1",
					"number": 1,
					"category": "轿车",
					"position": {
						"x": 944.9714187283353,
						"y": 712.9711061567027
					},
					"dimension": {
						"x": 71.2262093020197,
						"y": 58.792783067844766
					},
					"labels": "...json字符串..."

				}]
			}]
		]

	}]

}

'''
from peutils.transform.v1.base import *
import json




class LidarBoxPre():
    ### 输入连续帧数量
    ### 镜头顺序，可根据新数据的manifest读取

    def __init__(self,frame_length,camera_list):
        self.frame_length = frame_length
        self.camera_list = camera_list  # 镜头顺序，可以从新的数据中取到。如果变换了之后可能会影响到数据的
        self.frame_list = [{
                                "frameId":i,
                                "items":[],
                                "images":[
                                    {
                                        "items":[]
                                    }
                                          for j in range(len(self.camera_list))]
                            } for i in range(self.frame_length)]  # 写完后的完整数据

    def add_lidar_obj(self,frameNum,lidar_obj):
        self.frame_list[frameNum]["items"].append(
            lidar_obj.to_dict()
        )

    def add_img_obj(self,frameNum,camera,img_obj):
        cam_idx = self.camera_list.index(camera)
        self.frame_list[frameNum]["images"][cam_idx]["items"].append(
            img_obj.to_dict()
        )

    def dumps_data(self):
        out_dict = {
            "frames":self.frame_list
        }
        return json.dumps(out_dict,ensure_ascii=False)



if __name__ =="__main__":
    ldboxpre = LidarBoxPre(frame_length = 50,camera_list=['front_middle_camera', 'lf_wide_camera', 'lr_wide_camera', 'rear_middle_camera', 'rf_wide_camera', 'rr_wide_camera'])
    print(ldboxpre.dumps_data())

    # self.frames = {}



# -*- coding: UTF-8 -*-

'''
Author: Henry Wang
Date: 2022-06-03 06:38
Short Description:

Change History:

'''
from peutils.transform.v1.lidar_box.parser import LidarBoxParse,LidarBoxDataConfig
from peutils.transform.v1.task.executor import AbstractTask,CommonTaskV1

import logging
# logging.basicConfig(level=logging.DEBUG)
import time
import random

class AfterParse(AbstractTask):

    def __init__(self,parse_cls,config,row,users_param=None):
        super().__init__(parse_cls,config,row,users_param)


    def check_row_on_a9(self) ->None:

        self.log.create_error("发现错误")

    def check_row_addtional(self) ->None:
        pass

    def parse_row_func(self) ->None:
        # logging.debug("haha")
        # time.sleep(random.randint(1,10))
        logging.info("_______ok_________ ")
        print(self.parse_obj.frames_lst)
        # print("_______ok_________")


af = AfterParse(LidarBoxParse,
                config =LidarBoxDataConfig(
                             yaw_only = True,
                             has_pointCount= True,
                             number_adpter_func=None, #lambda i: round(i,3), # 默认None
                             parse_id_col = "id",
                             overflow= False
                         ),
                row={
    "annotation":"http://oss.prd.appen.com.cn:9000/appen-lidar-prod/15a7d17dd9ff2d831e0523421b1798e3/R.1647329777003.7628df30-4735-40fe-a641-b8210e11e00e.CLnhugEQJA3d3d_2022-03-15T073140Z.16644.QA_RW.f5079a20-5bef-478f-b9c5-a19f84227acd.27d74dc726f51f05e31f2206fda11714.review.json"
})
af.parse_row_func()

### 并发执行
# ct = CommonTaskV1(AfterParse)
# ct.process_func("/Users/hwang2/Downloads/Result_2022-05-31T09_06_35.239647Z_1.csv",k1="v1",k2="v2")




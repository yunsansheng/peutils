#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: echai
Date: 2024-12-20
Short Description:
Change History:
"""
import sys
import json
from peutils.transform.v2.base import CommonBaseMixIn


class LidarManifestConfig():
    def __init__(self, sensor3d_name="name", sensor2d_name="name", oss_prefix="appen://"):
        """
        Args:
            sensor3d_name: 点云传感器名称的key，默认name也是平台读取的固定key。若key不是name时，平台输出默认没有设置，会以 P0 的方式命名传感器
            sensor2d_name: 相机传感器名称的key，默认name也是平台读取的固定key。若key不是name时，平台输出默认没有设置，会以 C0 的方式命名传感器
            oss_prefix: oss形式的标注结果链接，链接前缀(bucket前的部分)
        """
        self.sensor3d_name = sensor3d_name
        self.sensor2d_name = sensor2d_name
        self.oss_prefix = oss_prefix


class LidarManifestParse(CommonBaseMixIn):

    ### 继承session属性 用来读取url
    def __init__(self,base_url,config):
        self.config = config
        # 可以直接传入manifest值
        if isinstance(base_url, dict):
            self.raw_data = base_url
        else:
            if base_url.startswith('{'):
                self.raw_data = json.loads(base_url)
            else:
                self.raw_data = self.get_raw_data(base_url, oss_prefix=self.config.oss_prefix)
        self.frame_length, self.frame_list, self.cameras_list, self.calib_dict = self.parse_sensors()
        self.frame_dict = dict(self.frame_list)
        self.cameras_dict = dict(self.cameras_list)

    def parse_sensors(self):
        # 后处理分配各路sensor需要用到索引的方式，所以这里定义list((name, urls))的方式
        frame_list = list()  # 会有多路lidar sensor，所以使用dict，其key为sensor name
        cameras_list = list() # 多路镜头  # 如果不加载图片的话，不会有camera sensor
        calib_dict = dict()  # 镜头参数
        for sensor in self.raw_data["sensors"]:
            sensor_type = sensor["type"]  # points or camera
            urls = sensor["urls"]
            if sensor_type == "points":
                name = sensor.get(self.config.sensor3d_name, f'P{len(frame_list)}')
                frame_list.append((name, urls))

            elif sensor_type == "camera":
                # manifest中相机传感器的名称key不是name时，平台输出会默认以 C0 的方式命名传感器
                name = sensor.get(self.config.sensor2d_name, f'C{len(cameras_list)}')
                cameras_list.append((name, urls))
                # 映射
                calib_dict[name] = sensor.get("calibrations", None)

        # 判断manifest为3D or 4D
        manifest_frames = self.raw_data.get("frames", [])
        if len(manifest_frames) > 0:
            # 4D：用pose点数作为帧数
            frame_count = [len(frame["pose"]) for lidar_sensor_idx, frame in enumerate(self.raw_data["frames"])]
        else:
            # 3D：用sensor文件数量作为帧数
            frame_count = [len(urls) for (name, urls) in frame_list]

        sensors_frame_count = [*frame_count, *[len(urls) for (name, urls) in cameras_list]]
        if len(set(sensors_frame_count)) != 1:
            print(f"注意各sensors帧数之间不相等：{sensors_frame_count}", file=sys.stderr)
        return max(sensors_frame_count), frame_list, cameras_list, calib_dict


if __name__ =="__main__":
    pass
    # mfst = LidarManifestParse(
    #     base_url="http://appen-config.oss-cn-shanghai.aliyuncs.com/echai/a9_v2/3d_test/20241221/manifest.json",
    #     config=LidarManifestConfig())
    #
    # print(mfst.frame_length, mfst.frame_dict, mfst.cameras_dict)

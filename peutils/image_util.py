# -*- coding: UTF-8 -*-

'''
Author: Henry Wang
Date: 2021-03-17 11:18
Short Description:

Change History:

'''
import numpy as np
import cv2
import re
import shutil
import base64
import os




class DrawMaskCls:
    def __init__(self, image_path,width,heigth, objects_data, result_path, colorMapping=None):
        '''

        :param image_path: local image path
        :param objects_data:
        :param result_path:
        :param colorMapping:
        输入颜色格式:
        {
            "行人":"#68bc00",
            "sse-eraser":"#ffffff"
            ...
        }
        '''
        self.image_path = image_path
        self.width = width
        self.height = heigth
        self.objects_data = objects_data
        self.result_path = result_path
        self.colorMapping = colorMapping


    def get_image_meta(self, image_path):
        img_data = cv2.imread(image_path)
        # img_data = cv2.imdecode(np.fromfile(image_path,dtype=np.uint8), -1)
        # 2021-2-7-21:38 xtu changed:
        # 增加win10旋转，目前尝试PIL以及PyPlot,numpy读取文件不会对其进行处理，需要旋转，cv2为已翻转信息，不能使用翻转！！
        # 旋转度信息为0112,仅针对exif信息，有可能图片不存在exif信息,png图片不存在该bug

        # https://blog.csdn.net/m1m2m3mmm/article/details/78401523
        h, w = img_data.shape[0], img_data.shape[1]
        return h, w


    def gen_mask_layer(self):
        # print(self.objects_data)
        # 生成空图
        mask_layer = np.zeros((self.height, self.width, 3), np.uint8)

        '根据mask顺序生成数据'

        for object in self.objects_data:
            # 获取坐标,二维数组。 [[x,y],[x,y]]
            points_np = np.array([self.getObjPoints(object)], dtype=np.int32)

            # 获取名称lassName
            objectClassName= object["className"]
            objectColorCode = object['classColor']  #"#009ce0"

            # 获取颜色rgb_list [0,0,0] # 范围是0-256
            if self.colorMapping is None:
                if objectClassName == 'sse-eraser':
                    rgb_list = [0, 0, 0]
                else:
                    rgb_list = self.transfer_color_code(objectColorCode)
            else:
                rgb_list = self.transfer_color_code(self.colorMapping[objectClassName])

            # 填充信息形状和颜色信息
            cv2.fillPoly(mask_layer, points_np, rgb_list)

        # 预览
        # cv2.imshow('URL2Image', black_backgroud)
        # cv2.waitKey()
        return mask_layer

    @staticmethod
    def transfer_color_code(color_str:str)->list:
        '''
        #ffffff 格式转成list [255,255,255]
        :param color_str:
        :return:
        '''
        return [int(color_str[5:7], 16), int(color_str[3:5], 16), int(color_str[1:3], 16)]


    @staticmethod
    def getObjPoints(obj):
        # 一纬数组
        return [[point['x'], point['y']] for point in obj['polygon']]


    def combine_mask_and_origin(self, maskOpacity=0.5, orginOpacity=0.8):
        mask_layer = self.gen_mask_layer()
        orgin_layer = cv2.imread(self.image_path)
        # orgin_layer = cv2.imdecode(np.fromfile(self.image_path,dtype=np.uint8),-1)
        # # imdecode读取的是rgb，如果后续需要opencv处理的话，需要转换成bgr，转换后图片颜色会变化
        # orgin_layer = cv2.cvtColor(orgin_layer, cv2.COLOR_RGB2BGR)
        combine_layer = cv2.addWeighted(orgin_layer, orginOpacity, mask_layer, maskOpacity, 1)
        return combine_layer


    def main_result(self, mask=True, combine=True, origin=True, jsondata=True):
        image_name = os.path.basename(self.image_path)
        image_name_without_suffix = '.'.join(os.path.basename(self.image_path).split(".")[:-1])

        if mask:
            mask_layer = self.gen_mask_layer()
            out_path = os.path.join(self.result_path,"mask")
            os.makedirs(out_path,exist_ok=True)
            cv2.imencode('.png', mask_layer)[1].tofile(os.path.join(out_path, image_name_without_suffix+'.png'))

        if combine:
            combine_layer = self.combine_mask_and_origin()  # 使用默认配置
            out_path = os.path.join(self.result_path, "mask_on_origin")
            os.makedirs(out_path,exist_ok=True)
            cv2.imencode('.png', combine_layer)[1].tofile(os.path.join(out_path, image_name_without_suffix + '.png'))


        if origin:
            out_path = os.path.join(self.result_path, "origin")
            os.makedirs(out_path,exist_ok=True)
            shutil.copyfile(self.image_path, os.path.join(out_path, image_name))




class RLEUtils:
    """
    RLE (Run-Length Encoding) 编解码工具类
    用于二值掩码的压缩和解压缩
    """
    
    @staticmethod
    def binary_mask_to_rle(binary_mask):
        """
        将二值掩码转换为 RLE 格式
        
        :param binary_mask: numpy数组，二值掩码 (0和1)
        :return: dict, {"counts": [...], "size": [height, width]}
        """
        rle = {"counts": [], "size": list(binary_mask.shape)}
        counts = rle.get("counts")
        for i, (value, elements) in enumerate(groupby(binary_mask.ravel(order="F"))):
            if i == 0 and value == 1:
                counts.append(0)
            counts.append(len(list(elements)))
        return rle
    
    @staticmethod
    def rle_decode(rle, img_height, img_width):
        """
        将 RLE 格式解码为二值掩码
        
        :param rle: dict, {"counts": [...], "size": [height, width]}
        :param img_height: 图像高度
        :param img_width: 图像宽度
        :return: numpy数组，二值掩码 (0和1)
        """
        counts = rle["counts"]
        flat = []
        val = 0
        for c in counts:
            flat.extend([val] * c)
            val = 1 - val
        mask = np.array(flat[: img_height * img_width], dtype=np.uint8).reshape(
            (img_height, img_width), order="F"
        )
        return mask
    
    @staticmethod
    def rle_encode(mask):
        """
        将二值掩码编码为 RLE 格式（便捷方法）
        
        :param mask: numpy数组，二值掩码 (0和1)
        :return: dict, {"counts": [...], "size": [height, width]}
        """
        fortran_ground_truth_binary_mask = np.asfortranarray(mask)
        rle = RLEUtils.binary_mask_to_rle(fortran_ground_truth_binary_mask)
        return rle
    
    @staticmethod
    def decode(rle):
        """
        从 RLE 解码（自动从 size 获取尺寸）
        
        :param rle: dict, {"counts": [...], "size": [height, width]}
        :return: numpy数组，二值掩码 (0和1)
        """
        img_height, img_width = rle["size"]
        return RLEUtils.rle_decode(rle, img_height, img_width)
    
    @staticmethod
    def encode(mask):
        """
        编码为 RLE（便捷方法，同 rle_encode）
        
        :param mask: numpy数组，二值掩码 (0和1)
        :return: dict, {"counts": [...], "size": [height, width]}
        """
        return RLEUtils.rle_encode(mask)
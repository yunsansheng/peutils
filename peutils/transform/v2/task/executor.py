# -*- coding: UTF-8 -*-

'''
Author: Henry Wang
Date: 2022-06-02 22:12
Short Description:

Change History:

'''


from abc import ABC,abstractmethod
# import uuid
import os,sys
import json
import traceback
from peutils.transform.v2.base import ErrorMsgLogV2,gen_format_progress_seq,deco_execution_time
import pandas as pd
from concurrent import futures
from peutils.textutil import gen_uuid



## 单条数据的处理基类，可能是连续帧
class AbstractTask(ABC):

    def __init__(self,row,users_param=None):
        self.row= row # 原始csv这一行的数据
        self.users_param = users_param if users_param is not None else {} # 前端用户的参数
        self.log = ErrorMsgLogV2()  # 这行的所有错误

    @property
    def row_flag(self):
        if len(self.log.error_list)>0:
            return 0
        else:
            return 1

    @abstractmethod
    def check_row_on_a9(self)->None:
        """a9只能通过annotation进行检查 将内容输出到log"""

    @abstractmethod
    def check_row_addtional(self)->None:
        """额外的内容检查 将内容输出到log """

    def check_row_func(self,check_mode="all"): #check分a9的
        if self.log is None or isinstance(self.log,ErrorMsgLogV2) ==False:
            raise Exception("请定义log 并且使用ErrorMsgLog的实例")
        else:
            ### 将自带错误的解析方法放过去这个错误的方法
            # self.log.error_list.extend(self.parse_obj.check_frames_error())

            if check_mode=="a9_check":
                self.check_row_on_a9()
                return self.log.error_list  ##直接返回对象
            elif check_mode == "all":
                self.check_row_on_a9()
                self.check_row_addtional()
                return self.log.error_list ##做格式化
            else:
                raise Exception("未定义的check mode")


    @abstractmethod
    def parse_row_func(self)->None:
        """实现自定义的 parse_row_func方法  相当于单条数据的main函数"""


class CommonTaskV2:
    def __init__(self,row_cls:type,max_worker=16):
        self.RowTask = row_cls
        # self.parse_cls = parse_cls
        # self.config = config
        self.max_worker = max_worker
        self.format_progress = lambda: None


    def process_unit(self,row,users_param):
        row_task = self.RowTask(row=row,users_param=users_param)
        ## 执行检查逻辑,将错误输出到log

        ###执行方法,捕捉未知错误
        try:
            row_task.check_row_func()
            row_task.parse_row_func()
        except Exception as e:
            row_task.log.create_error(msg=repr(e))

        ### 这行所有错误的集合
        errors = row_task.log.fomart_error_str()

        return row_task.row_flag, row, errors

    ### 单个文件的处理
    @deco_execution_time
    def process_file(self,file, nrows, user_kw):
        task_df = pd.read_csv(file,encoding='utf-8-sig', nrows=nrows)
        task_count = len(task_df)
        self.format_progress = gen_format_progress_seq(total=task_count, split_part=min(10, task_count))

        rows_error = list()

        with futures.ThreadPoolExecutor(min(self.max_worker, task_count)) as executor:

            tasks = [executor.submit(self.process_unit, row=row, users_param=user_kw) for _, row in task_df.iterrows()]

            for future in futures.as_completed(tasks):
                row_flag, row, errors, = future.result()  # flag 1代表是成功，0代表失败，失败后所有的数据，写入csv
                self.format_progress()
                if row_flag == 0:
                    rows_error.append({"errors":errors,**row,})

            if len(rows_error)>0:
                print(f"{file} 发现异常{len(rows_error)}，请检查输出文件中的异常明细", file=sys.stderr)
                df_error = pd.DataFrame(rows_error)
                if "Record ID" in df_error:
                    df_error.sort_values(by="Record ID", inplace=True)
                df_error.to_csv(f"error_{gen_uuid()}_{'.'.join(os.path.basename(file).split('.')[:-1])}.csv",index=False,encoding="utf-8-sig")

    ## process 方法的入口
    @deco_execution_time
    def process_func(self,files, nrows=None, **user_kw):

        if isinstance(files,list) == True:
            for file in files:
                self.process_file(file, nrows, user_kw)
        else:
            self.process_file(files, nrows, user_kw)



# class AfterParse(AbstractTask):
#     def __init__(self, row, users_param=None):
#         super().__init__(row, users_param)
#         self.test = 1
#
#     def check_row_on_a9(self) -> None:
#         for frame in [1, 2]:
#             self.log.create_error(msg=f'属性丢失', frameNum=frame)
#
#     def check_row_addtional(self) -> None:
#         pass
#
#     def parse_row_func(self) -> None:
#         pass
#
# CommonTaskV2(AfterParse, max_worker=10).process_func(
#     files="/Users/echai/Downloads/2025-01-14T07_57_38.523066Z-report.csv", nrows=1
# )
#


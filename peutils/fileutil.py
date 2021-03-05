# -*- coding: UTF-8 -*-

'''
Author: Henry Wang
Date: 2021-03-05 13:23
Short Description:

Change History:

'''

from pathlib import Path

def list_current_file(path='.', type='all', suffix='', not_prefix=(('~', '.'))):
    '''
    列出当前目录下的文件或者文件夹
    :param path: 默认当前目录
    :param type: 可选 file,folder,all 默认all
    :param suffix: 对文件夹和文件后缀过滤
    :param not_prefix: 对文件夹和文件前缀过滤，默认不要隐藏文件和临时文件
    :return:文件或文件夹的集合
    '''
    p = Path(path)

    if type == 'all':
        return [x.resolve().as_posix() for x in p.iterdir()
                if x.name.endswith(suffix) and not x.name.startswith(not_prefix)]
    elif type == "file":
        return [x.resolve().as_posix() for x in p.iterdir() if x.is_file()
                if x.name.endswith(suffix) and not x.name.startswith(not_prefix)]
    elif type == "folder":
        return [x.resolve().as_posix() for x in p.iterdir() if x.is_dir()
                if x.name.endswith(suffix) and not x.name.startswith(not_prefix)]
    else:
        raise Exception(f"type: {type} not defined.")
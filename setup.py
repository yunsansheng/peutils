# -*- coding: UTF-8 -*-

'''
Author: Henry Wang
Date: 2021-03-05 13:20
Short Description:

Change History:

'''

from setuptools import setup, find_packages




setup(
    name = "peutils",
    version = '0.0.50',
    keywords = ("pip3", "peutils",'henry'),
    description = "utils for text,audio,video,excel,file and so on.",
    long_description = "utils for text,audio,video,excel,file and so on,more details please visit gitlab.",
    license = "MIT Licence",
    url = "https://github.com/yunsansheng/peutils",
    author = "henry.wang",
    author_email = "shanandone@qq.com",
    packages = find_packages(),
    include_package_data = True,
    platforms = "any",
    install_requires = []
)


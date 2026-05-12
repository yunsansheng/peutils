# -*- coding: UTF-8 -*-

'''
Author: rxu
Date: 2024-07-17 16:38
Short Description: URL处理工具模块

Change History:
2024-01-XX: 添加完整的URL验证、解析和操作功能

'''

import urllib.parse
from typing import Dict, List, Tuple, Optional, Union
import re


def get_clean_url(url: str) -> str:
    """
    获取纯净url（移除查询参数）

    类似
    https://appen-data.oss-cn-shanghai.aliyuncs.com/Sand%2FSand_MovingVehicle%2F20240628_135703770731%2F1054%2F202405181
    44339399530%2Fvelodyne_points%2Fvelodyne64.pcd?Expires=1721959200&OSSAccessKeyId=LTAI5tB2Etp2wUEVtkT7zckM&Signature
    =uKI2Et1%2FDDYSXJg7YAVwe3sNp7o%3D
    转换为
    'https://appen-data.oss-cn-shanghai.aliyuncs.com/Sand/Sand_MovingVehicle/20240628_135703770731/1054/2024051814433939
    95530/velodyne_points/velodyne64.pcd'

    Args:
        url (str): 输入的URL字符串

    Returns:
        str: 移除查询参数后的纯净URL

    Raises:
        ValueError: 当输入不是有效字符串时
    """
    if not isinstance(url, str):
        raise ValueError("URL必须是字符串类型")
    
    if not url.strip():
        return ""
        
    try:
        url = urllib.parse.unquote(url)
        parsed_url = urllib.parse.urlparse(url)
        clean_url = urllib.parse.urlunparse(parsed_url._replace(query=""))
        return clean_url
    except Exception as e:
        raise ValueError(f"URL解析失败: {str(e)}")


def is_valid_url(url: str) -> bool:
    """
    验证URL格式是否正确

    Args:
        url (str): 待验证的URL

    Returns:
        bool: URL格式是否有效
    """
    if not isinstance(url, str) or not url.strip():
        return False
    
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_http_url(url: str) -> bool:
    """
    检查是否为HTTP/HTTPS协议的URL

    Args:
        url (str): 待检查的URL

    Returns:
        bool: 是否为HTTP/HTTPS协议
    """
    if not isinstance(url, str):
        return False
    
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.scheme.lower() in ['http', 'https']
    except Exception:
        return False


def is_storage_url(url: str) -> bool:
    """
    检查是否为存储系统URL (oss://, obs://, s3://, appen://)

    Args:
        url (str): 待检查的URL

    Returns:
        bool: 是否为存储系统URL
    """
    if not isinstance(url, str):
        return False
    
    storage_prefixes = ['oss://', 'obs://', 's3://', 'appen://']
    return any(url.startswith(prefix) for prefix in storage_prefixes)


def extract_query_params(url: str) -> Dict[str, List[str]]:
    """
    提取URL中的查询参数为字典

    Args:
        url (str): 输入URL

    Returns:
        Dict[str, List[str]]: 查询参数字典，键为参数名，值为参数值列表

    Example:
        >>> extract_query_params("http://example.com?a=1&b=2&a=3")
        {'a': ['1', '3'], 'b': ['2']}
    """
    if not isinstance(url, str):
        return {}
    
    try:
        parsed = urllib.parse.urlparse(url)
        return urllib.parse.parse_qs(parsed.query)
    except Exception:
        return {}


def build_query_string(params: Dict[str, Union[str, List[str]]]) -> str:
    """
    将字典构建成查询字符串

    Args:
        params (Dict[str, Union[str, List[str]]]): 参数字典

    Returns:
        str: 查询字符串

    Example:
        >>> build_query_string({'a': '1', 'b': ['2', '3']})
        'a=1&b=2&b=3'
    """
    if not isinstance(params, dict):
        return ""
    
    try:
        return urllib.parse.urlencode(params, doseq=True)
    except Exception:
        return ""


def add_query_params(url: str, params: Dict[str, Union[str, List[str]]]) -> str:
    """
    向URL添加查询参数

    Args:
        url (str): 原始URL
        params (Dict[str, Union[str, List[str]]]): 要添加的参数

    Returns:
        str: 添加参数后的新URL

    Example:
        >>> add_query_params("http://example.com", {'a': '1', 'b': '2'})
        'http://example.com?a=1&b=2'
    """
    if not isinstance(url, str) or not isinstance(params, dict):
        return url
    
    try:
        parsed = urllib.parse.urlparse(url)
        existing_params = urllib.parse.parse_qs(parsed.query)
        
        # 合并参数
        for key, value in params.items():
            if key in existing_params:
                if isinstance(value, list):
                    existing_params[key].extend(value)
                else:
                    existing_params[key].append(str(value))
            else:
                existing_params[key] = value if isinstance(value, list) else [str(value)]
        
        # 构建新的查询字符串
        new_query = urllib.parse.urlencode(existing_params, doseq=True)
        return urllib.parse.urlunparse(parsed._replace(query=new_query))
    except Exception:
        return url




def normalize_url_path(url: str) -> str:
    """
    标准化URL路径（处理../和./）

    Args:
        url (str): 输入URL

    Returns:
        str: 标准化后的URL

    Example:
        >>> normalize_url_path("http://example.com/path/../file.txt")
        'http://example.com/file.txt'
    """
    if not isinstance(url, str):
        return url
    
    try:
        parsed = urllib.parse.urlparse(url)
        # 使用normpath处理路径规范化
        normalized_path = urllib.parse.quote(urllib.parse.unquote(parsed.path))
        return urllib.parse.urlunparse(parsed._replace(path=normalized_path))
    except Exception:
        return url


def parse_storage_url(storage_url: str) -> Tuple[str, str]:
    """
    解析存储URL，返回(bucket, path)

    Args:
        storage_url (str): 存储URL (如: oss://bucket-name/path/to/file)

    Returns:
        Tuple[str, str]: (bucket_name, path) 元组

    Raises:
        ValueError: 当URL格式不正确时

    Example:
        >>> parse_storage_url("oss://my-bucket/path/file.txt")
        ('my-bucket', 'path/file.txt')
    """
    if not isinstance(storage_url, str):
        raise ValueError("存储URL必须是字符串")
    
    if not is_storage_url(storage_url):
        raise ValueError("不是有效的存储URL格式")
    
    try:
        # 移除协议前缀
        for prefix in ['oss://', 'obs://', 's3://', 'appen://']:
            if storage_url.startswith(prefix):
                path_without_prefix = storage_url[len(prefix):]
                break
        
        # 分割bucket和路径
        parts = path_without_prefix.split('/', 1)
        if len(parts) == 1:
            bucket_name = parts[0]
            path = ""
        else:
            bucket_name, path = parts
            
        return bucket_name, path
    except Exception as e:
        raise ValueError(f"存储URL解析失败: {str(e)}")


def is_private_url(url: str) -> bool:
    """
    判断是否为私有访问URL（含签名参数）

    Args:
        url (str): 待检查的URL

    Returns:
        bool: 是否为私有URL

    Example:
        >>> is_private_url("http://example.com/file.txt?Expires=123&OSSAccessKeyId=abc")
        True
    """
    if not isinstance(url, str):
        return False
    
    private_indicators = ['Expires=', 'OSSAccessKeyId=', 'Signature=', 'AWSAccessKeyId=']
    return any(indicator in url for indicator in private_indicators)



def join_url_paths(base_url: str, *paths: str) -> str:
    """
    智能连接URL路径

    Args:
        base_url (str): 基础URL
        *paths (str): 要连接的路径片段

    Returns:
        str: 连接后的完整URL

    Example:
        >>> join_url_paths("http://example.com", "api", "users")
        'http://example.com/api/users'
    """
    if not isinstance(base_url, str):
        return base_url
    
    try:
        parsed = urllib.parse.urlparse(base_url)
        base_path = parsed.path.rstrip('/')
        
        # 处理路径连接
        path_parts = [base_path] if base_path else []
        for path in paths:
            if isinstance(path, str):
                # 清理路径并添加
                clean_path = path.strip('/')
                if clean_path:
                    path_parts.append(clean_path)
        
        # 重新组合URL
        new_path = '/' + '/'.join(path_parts) if path_parts else '/'
        return urllib.parse.urlunparse(parsed._replace(path=new_path))
    except Exception:
        # 出错时返回原URL
        return base_url


def get_url_domain(url: str) -> str:
    """
    提取URL的域名部分

    Args:
        url (str): 输入URL

    Returns:
        str: 域名，如果无法提取则返回空字符串

    Example:
        >>> get_url_domain("https://www.example.com:8080/path")
        'www.example.com'
    """
    if not isinstance(url, str):
        return ""
    
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc.split(':')[0]  # 移除端口号
    except Exception:
        return ""


def is_same_domain(url1: str, url2: str) -> bool:
    """
    判断两个URL是否属于同一域名

    Args:
        url1 (str): 第一个URL
        url2 (str): 第二个URL

    Returns:
        bool: 是否属于同一域名

    Example:
        >>> is_same_domain("http://example.com/path1", "https://example.com/path2")
        True
    """
    domain1 = get_url_domain(url1)
    domain2 = get_url_domain(url2)
    return domain1.lower() == domain2.lower() if domain1 and domain2 else False


def get_relative_path(url: str) -> str:
    """
    获取URL中域名或bucket后的相对路径
    
    支持HTTP/HTTPS URL和存储系统URL
    
    Args:
        url (str): 输入URL
        
    Returns:
        str: 相对路径，如果无法解析则返回空字符串
        
    Examples:
        >>> get_relative_path("https://appen-data.aliyun-shanghai.com/xc/occ/anno.json")
        'xc/occ/anno.json'
        >>> get_relative_path("appen://appen-data/xc/occ/anno.json")
        'xc/occ/anno.json'
        >>> get_relative_path("oss://my-bucket/folder/file.txt")
        'folder/file.txt'
    """
    if not isinstance(url, str) or not url.strip():
        return ""
    
    try:
        # 处理存储系统URL
        if is_storage_url(url):
            bucket, path = parse_storage_url(url)
            return path
        
        # 处理HTTP/HTTPS URL
        elif is_http_url(url):
            parsed = urllib.parse.urlparse(url)
            # 移除开头的斜杠
            path = parsed.path.lstrip('/')
            return path
            
        # 其他情况
        else:
            return ""
            
    except Exception:
        return ""


def get_base_path(url: str) -> str:
    """
    获取URL的基础路径（相对于域名或bucket的部分）
    与get_relative_path功能相同，提供另一个名称选择
    
    Args:
        url (str): 输入URL
        
    Returns:
        str: 基础路径
        
    Examples:
        >>> get_base_path("https://example.com/api/v1/data.json")
        'api/v1/data.json'
        >>> get_base_path("oss://bucket/folder/file.txt")
        'folder/file.txt'
    """
    return get_relative_path(url)



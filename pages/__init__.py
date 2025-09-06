# -*- coding: utf-8 -*-
"""
用户行为分析页面模块

包含以下分析页面：
- user_profile: 用户画像分析
- geo_analysis: 地理行为分析
- time_analysis: 时间行为分析
- content_analysis: 内容行为分析
- social_network: 社交网络分析
"""

__version__ = "1.0.0"
__author__ = "User Behavior Analysis Team"

# 导入所有页面模块
try:
    from . import user_profile
    from . import geo_analysis
    from . import time_analysis
    from . import content_analysis
    from . import social_network
except ImportError as e:
    print(f"Warning: Failed to import some page modules: {e}")

# 页面模块列表
PAGE_MODULES = [
    'user_profile',
    'geo_analysis', 
    'time_analysis',
    'content_analysis',
    'social_network'
]

# 页面信息
PAGE_INFO = {
    'user_profile': {
        'name': '用户画像分析',
        'icon': '👤',
        'description': '分析用户基础属性、活跃度、影响力等特征'
    },
    'geo_analysis': {
        'name': '地理行为分析',
        'icon': '🌍',
        'description': '分析用户地理分布、区域行为差异、热力图等'
    },
    'time_analysis': {
        'name': '时间行为分析',
        'icon': '⏰',
        'description': '分析发布时间模式、用户活跃时段等时间特征'
    },
    'content_analysis': {
        'name': '内容行为分析',
        'icon': '📝',
        'description': '分析文本内容、话题挖掘、情感分析等'
    },
    'social_network': {
        'name': '社交网络分析',
        'icon': '🕸️',
        'description': '分析用户互动、网络结构、影响力传播等'
    }
}

def get_page_list():
    """获取页面列表"""
    return [(info['icon'] + ' ' + info['name'], module) for module, info in PAGE_INFO.items()]

def get_page_info(module_name):
    """获取页面信息"""
    return PAGE_INFO.get(module_name, {})
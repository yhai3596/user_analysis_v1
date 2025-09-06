# 应用配置文件

# 数据处理配置
DATA_CONFIG = {
    'chunk_size': 10000,  # 分块读取大小
    'sample_size': 1000,  # 样本数据大小
    'max_memory_usage': 2048,  # 最大内存使用(MB)
    'cache_ttl': 3600,  # 缓存过期时间(秒)
}

# 可视化配置
VIZ_CONFIG = {
    'color_palette': [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ],
    'map_style': 'OpenStreetMap',
    'figure_width': 800,
    'figure_height': 600,
    'font_size': 12,
    'title_font_size': 16,
}

# 文本分析配置
TEXT_CONFIG = {
    'max_words': 100,  # 词云最大词数
    'min_word_length': 2,  # 最小词长
    'stopwords_file': None,  # 停用词文件路径
    'font_path': None,  # 中文字体路径
}

# 地理分析配置
GEO_CONFIG = {
    'default_zoom': 10,
    'heatmap_radius': 15,
    'cluster_threshold': 100,
    'map_height': 500,
}

# 缓存配置
CACHE_CONFIG = {
    'cache_dir': 'cache',
    'streamlit_cache_dir': 'streamlit_cache',
    'enable_disk_cache': True,
    'enable_session_cache': True,
    'auto_clear_cache': False,
}

# 性能配置
PERFORMANCE_CONFIG = {
    'enable_multiprocessing': True,
    'max_workers': 4,
    'memory_limit_mb': 4096,
    'gc_threshold': 1000,  # 垃圾回收阈值
}

# 导出配置
EXPORT_CONFIG = {
    'report_formats': ['pdf', 'html', 'excel'],
    'image_formats': ['png', 'svg', 'pdf'],
    'default_dpi': 300,
    'export_dir': 'exports',
}

# 数据库配置（可选）
DB_CONFIG = {
    'enable_db': False,
    'db_type': 'sqlite',  # sqlite, postgresql, mysql
    'db_path': 'data/analysis.db',
    'connection_pool_size': 5,
}

# 安全配置
SECURITY_CONFIG = {
    'max_file_size_mb': 500,
    'allowed_file_types': ['.xlsx', '.xls', '.csv'],
    'enable_file_validation': True,
    'max_upload_files': 5,
}

# 日志配置
LOGGING_CONFIG = {
    'log_level': 'INFO',
    'log_file': 'logs/app.log',
    'max_log_size_mb': 10,
    'backup_count': 5,
    'enable_console_log': True,
}

# 应用元信息
APP_INFO = {
    'name': '用户行为分析系统',
    'version': '1.0.0',
    'description': '基于Streamlit的用户行为分析工具',
    'author': 'AI Assistant',
    'contact': 'support@example.com',
    'github': 'https://github.com/example/user-behavior-analysis',
}

# 页面配置
PAGE_CONFIG = {
    'page_title': APP_INFO['name'],
    'page_icon': '📊',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded',
    'menu_items': {
        'Get Help': 'https://github.com/example/user-behavior-analysis/wiki',
        'Report a bug': 'https://github.com/example/user-behavior-analysis/issues',
        'About': f"{APP_INFO['name']} v{APP_INFO['version']}\n\n{APP_INFO['description']}"
    }
}

# 分析模块配置
ANALYSIS_MODULES = {
    'user_profile': {
        'name': '用户画像分析',
        'icon': '👥',
        'description': '分析用户基础属性、活跃度和影响力',
        'enabled': True,
    },
    'geo_analysis': {
        'name': '地理行为分析',
        'icon': '🗺️',
        'description': '分析用户地理分布和位置行为',
        'enabled': True,
    },
    'time_analysis': {
        'name': '时间行为分析',
        'icon': '⏰',
        'description': '分析用户时间活跃模式',
        'enabled': True,
    },
    'content_analysis': {
        'name': '内容行为分析',
        'icon': '📝',
        'description': '分析用户内容和文本行为',
        'enabled': True,
    },
    'social_network': {
        'name': '社交网络分析',
        'icon': '🔗',
        'description': '分析用户社交互动和网络关系',
        'enabled': True,
    },
}

# 默认数据字段映射
FIELD_MAPPING = {
    'user_id': '用户ID',
    'gender': '性别',
    'nickname': '昵称',
    'province': '注册省份',
    'city': '注册城市',
    'weibo_count': '微博数',
    'following_count': '关注数',
    'followers_count': '粉丝数',
    'bio': '个人简介',
    'location_id': '地点ID',
    'location_name': '地点名称',
    'location_type': '地点类型',
    'address': '详细地址',
    'latitude': '纬度',
    'longitude': '经度',
    'weibo_id': '微博ID',
    'publish_time': '发布时间',
    'source': '发布来源',
    'content': '微博文本',
    'repost_count': '转发数',
    'comment_count': '评论数',
    'like_count': '点赞数',
}

# 数据验证规则
VALIDATION_RULES = {
    'required_fields': ['用户ID'],
    'numeric_fields': ['微博数', '关注数', '粉丝数', '转发数', '评论数', '点赞数'],
    'categorical_fields': ['性别', '注册省份', '地点类型'],
    'datetime_fields': ['发布时间'],
    'coordinate_fields': ['纬度', '经度'],
    'text_fields': ['昵称', '个人简介', '微博文本'],
}

# 获取配置的便捷函数
def get_config(config_name: str, default=None):
    """获取配置值"""
    config_map = {
        'data': DATA_CONFIG,
        'viz': VIZ_CONFIG,
        'text': TEXT_CONFIG,
        'geo': GEO_CONFIG,
        'cache': CACHE_CONFIG,
        'performance': PERFORMANCE_CONFIG,
        'export': EXPORT_CONFIG,
        'db': DB_CONFIG,
        'security': SECURITY_CONFIG,
        'logging': LOGGING_CONFIG,
        'app': APP_INFO,
        'page': PAGE_CONFIG,
        'modules': ANALYSIS_MODULES,
        'fields': FIELD_MAPPING,
        'validation': VALIDATION_RULES,
    }
    return config_map.get(config_name, default)

# 环境变量覆盖（可选）
import os

# 允许通过环境变量覆盖某些配置
if os.getenv('CHUNK_SIZE'):
    DATA_CONFIG['chunk_size'] = int(os.getenv('CHUNK_SIZE'))

if os.getenv('CACHE_TTL'):
    DATA_CONFIG['cache_ttl'] = int(os.getenv('CACHE_TTL'))

if os.getenv('MAX_MEMORY_USAGE'):
    DATA_CONFIG['max_memory_usage'] = int(os.getenv('MAX_MEMORY_USAGE'))

if os.getenv('LOG_LEVEL'):
    LOGGING_CONFIG['log_level'] = os.getenv('LOG_LEVEL')
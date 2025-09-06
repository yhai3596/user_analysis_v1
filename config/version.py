# -*- coding: utf-8 -*-
"""
版本信息配置文件
用于集中管理应用版本信息和更新日志
"""

from datetime import datetime

# 当前版本信息
CURRENT_VERSION = "1.2"
RELEASE_DATE = "2024-01-15"
APP_NAME = "用户行为分析系统"

# 版本历史和更新日志
VERSION_HISTORY = [
    {
        "version": "1.2",
        "date": "2024-01-15",
        "status": "current",
        "changes": [
            "✅ 修复词云生成字体问题",
            "✅ 添加textstat和networkx依赖",
            "✅ 优化异常处理机制",
            "✅ 提升跨平台兼容性",
            "🔧 改进错误提示信息"
        ],
        "type": "bugfix"
    },
    {
        "version": "1.1",
        "date": "2024-01-10",
        "status": "released",
        "changes": [
            "✅ 修复变量作用域问题",
            "✅ 优化Streamlit Cloud部署",
            "✅ 改进错误提示信息",
            "🚀 提升部署稳定性"
        ],
        "type": "bugfix"
    },
    {
        "version": "1.0",
        "date": "2024-01-01",
        "status": "released",
        "changes": [
            "🎉 首次发布",
            "📊 完整的用户行为分析功能",
            "🚀 大数据处理支持",
            "💾 智能缓存机制",
            "📈 丰富的可视化图表",
            "🔍 多维度数据分析"
        ],
        "type": "major"
    }
]

# 计划中的版本
PLANNED_VERSIONS = [
    {
        "version": "1.3",
        "planned_date": "2024-02-01",
        "status": "planned",
        "features": [
            "🔍 高级搜索过滤功能",
            "📈 更多可视化图表类型",
            "🤖 AI智能分析建议",
            "📊 自定义仪表板",
            "🔗 API接口支持",
            "📤 增强的数据导出功能"
        ],
        "type": "feature"
    },
    {
        "version": "1.4",
        "planned_date": "2024-03-01",
        "status": "planned",
        "features": [
            "🌐 多语言支持",
            "📱 移动端适配",
            "🔐 用户权限管理",
            "📤 批量数据导出",
            "🔄 实时数据同步",
            "📊 高级统计分析"
        ],
        "type": "major"
    },
    {
        "version": "2.0",
        "planned_date": "2024-06-01",
        "status": "roadmap",
        "features": [
            "🏗️ 全新架构重构",
            "⚡ 性能大幅提升",
            "🎨 全新UI设计",
            "🔌 插件系统支持",
            "☁️ 云端部署支持",
            "🤖 机器学习集成"
        ],
        "type": "major"
    }
]

def get_version_info():
    """获取当前版本信息"""
    return {
        "version": CURRENT_VERSION,
        "release_date": RELEASE_DATE,
        "app_name": APP_NAME
    }

def get_changelog():
    """获取更新日志"""
    return VERSION_HISTORY

def get_roadmap():
    """获取版本路线图"""
    return PLANNED_VERSIONS

def format_version_display():
    """格式化版本显示信息"""
    changelog_text = ""
    
    # 当前版本和历史版本
    for version_info in VERSION_HISTORY:
        version = version_info["version"]
        date = version_info["date"]
        changes = version_info["changes"]
        
        changelog_text += f"**v{version} ({date})**\n"
        for change in changes:
            changelog_text += f"• {change}\n"
        changelog_text += "\n"
    
    return changelog_text

def format_roadmap_display():
    """格式化路线图显示信息"""
    roadmap_text = ""
    
    for version_info in PLANNED_VERSIONS:
        version = version_info["version"]
        planned_date = version_info.get("planned_date", "待定")
        features = version_info["features"]
        
        roadmap_text += f"**v{version} (计划: {planned_date})**\n"
        for feature in features:
            roadmap_text += f"• {feature}\n"
        roadmap_text += "\n"
    
    return roadmap_text

def get_latest_updates(limit=3):
    """获取最新的更新信息"""
    return VERSION_HISTORY[:limit]

def is_latest_version(version):
    """检查是否为最新版本"""
    return version == CURRENT_VERSION
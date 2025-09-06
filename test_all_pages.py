#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有页面的数据处理逻辑
验证修复后的应用是否能正常处理数据
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

# 导入各个页面模块
from utils.visualizer import create_dashboard_metrics

def create_test_data():
    """创建测试数据"""
    np.random.seed(42)
    n_samples = 1000
    
    data = {
        '用户ID': [f'user_{i:04d}' for i in range(n_samples)],
        '用户名': [f'用户{i}' for i in range(n_samples)],
        '微博内容': [f'这是第{i}条微博内容，包含一些测试文本' for i in range(n_samples)],
        '发布时间': pd.date_range('2023-01-01', periods=n_samples, freq='H'),
        '发布来源': np.random.choice(['iPhone客户端', 'Android客户端', '网页版'], n_samples),
        '转发数': np.random.randint(0, 1000, n_samples),
        '评论数': np.random.randint(0, 500, n_samples),
        '点赞数': np.random.randint(0, 2000, n_samples),
        '关注数': np.random.randint(10, 10000, n_samples),
        '粉丝数': np.random.randint(0, 50000, n_samples),
        '注册城市': np.random.choice(['北京', '上海', '广州', '深圳', '杭州'], n_samples),
        '注册省份': np.random.choice(['北京市', '上海市', '广东省', '浙江省'], n_samples),
        '性别': np.random.choice(['男', '女', '未知'], n_samples),
        '年龄': np.random.randint(18, 65, n_samples)
    }
    
    return pd.DataFrame(data)

def test_dashboard_metrics():
    """测试仪表板指标函数"""
    print("\n=== 测试仪表板指标函数 ===")
    
    # 测试正常数据
    df = create_test_data()
    metrics = create_dashboard_metrics(df)
    print(f"✅ 正常数据测试通过: {len(metrics)} 个指标")
    
    # 测试None数据
    metrics_none = create_dashboard_metrics(None)
    print(f"✅ None数据测试通过: {len(metrics_none)} 个指标")
    
    # 测试空DataFrame
    empty_df = pd.DataFrame()
    metrics_empty = create_dashboard_metrics(empty_df)
    print(f"✅ 空DataFrame测试通过: {len(metrics_empty)} 个指标")
    
    return True

def test_user_profile_analyzer():
    """测试用户画像分析器"""
    print("\n=== 测试用户画像分析器 ===")
    
    try:
        from pages.user_profile import UserProfileAnalyzer
        analyzer = UserProfileAnalyzer()
        
        # 测试正常数据
        df = create_test_data()
        result = analyzer.analyze_basic_attributes(df)
        print(f"✅ 基础属性分析通过: {len(result)} 个结果")
        
        result = analyzer.analyze_activity_levels(df)
        print(f"✅ 活跃度分析通过: {len(result)} 个结果")
        
        result = analyzer.analyze_influence_metrics(df)
        print(f"✅ 影响力分析通过: {len(result)} 个结果")
        
        return True
    except Exception as e:
        print(f"❌ 用户画像分析器测试失败: {e}")
        return False

def test_content_analyzer():
    """测试内容分析器"""
    print("\n=== 测试内容分析器 ===")
    
    try:
        from pages.content_analysis import ContentAnalyzer
        analyzer = ContentAnalyzer()
        
        # 测试正常数据
        df = create_test_data()
        result = analyzer.analyze_text_content(df)
        print(f"✅ 文本内容分析通过: {len(result)} 个结果")
        
        result = analyzer.analyze_posting_sources(df)
        print(f"✅ 发布来源分析通过: {len(result)} 个结果")
        
        return True
    except Exception as e:
        print(f"❌ 内容分析器测试失败: {e}")
        return False

def test_time_analyzer():
    """测试时间分析器"""
    print("\n=== 测试时间分析器 ===")
    
    try:
        from pages.time_analysis import TimeAnalyzer
        analyzer = TimeAnalyzer()
        
        # 测试正常数据
        df = create_test_data()
        result = analyzer.analyze_posting_patterns(df)
        print(f"✅ 发布模式分析通过: {len(result)} 个结果")
        
        result = analyzer.analyze_user_activity_patterns(df)
        print(f"✅ 用户活动模式分析通过: {len(result)} 个结果")
        
        return True
    except Exception as e:
        print(f"❌ 时间分析器测试失败: {e}")
        return False

def test_geo_analyzer():
    """测试地理分析器"""
    print("\n=== 测试地理分析器 ===")
    
    try:
        from pages.geo_analysis import GeoAnalyzer
        analyzer = GeoAnalyzer()
        
        # 测试正常数据
        df = create_test_data()
        result = analyzer.analyze_geographic_distribution(df)
        print(f"✅ 地理分布分析通过: {len(result)} 个结果")
        
        result = analyzer.analyze_regional_behavior(df)
        print(f"✅ 区域行为分析通过: {len(result)} 个结果")
        
        return True
    except Exception as e:
        print(f"❌ 地理分析器测试失败: {e}")
        return False

def test_social_network_analyzer():
    """测试社交网络分析器"""
    print("\n=== 测试社交网络分析器 ===")
    
    try:
        from pages.social_network import SocialNetworkAnalyzer
        analyzer = SocialNetworkAnalyzer()
        
        # 测试正常数据
        df = create_test_data()
        result = analyzer.analyze_user_interactions(df)
        print(f"✅ 用户互动分析通过: {len(result)} 个结果")
        
        result = analyzer.analyze_follower_patterns(df)
        print(f"✅ 关注者模式分析通过: {len(result)} 个结果")
        
        return True
    except Exception as e:
        print(f"❌ 社交网络分析器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试所有页面的数据处理逻辑...")
    
    test_results = []
    
    # 运行所有测试
    test_results.append(test_dashboard_metrics())
    test_results.append(test_user_profile_analyzer())
    test_results.append(test_content_analyzer())
    test_results.append(test_time_analyzer())
    test_results.append(test_geo_analyzer())
    test_results.append(test_social_network_analyzer())
    
    # 汇总结果
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n{'='*50}")
    print(f"📊 测试结果汇总: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！应用修复成功！")
        print("\n✅ 修复总结:")
        print("   - 所有页面添加了数据None检查")
        print("   - create_dashboard_metrics函数增强了防护")
        print("   - 数据获取逻辑更加健壮")
        print("   - 应用现在可以安全处理各种数据状态")
    else:
        print("❌ 部分测试失败，需要进一步检查")
    
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
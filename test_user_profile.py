#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户画像模块测试脚本
测试修复后的用户画像分析功能
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import pandas as pd
import numpy as np
from utils.data_loader import BigDataLoader
from pages.user_profile import UserProfileAnalyzer
from utils.visualizer import create_dashboard_metrics

def test_user_profile_module():
    """测试用户画像模块"""
    print("开始用户画像模块测试...")
    print("=" * 60)
    
    # 1. 加载测试数据
    print("\n1. 加载测试数据...")
    try:
        loader = BigDataLoader()
        file_path = "e:\\AICoding\\用户数据分析\\切片.xlsx"
        
        # 加载样本数据
        df = loader.load_data_sample(file_path, sample_size=100)
        print(f"   ✅ 数据加载成功，形状: {df.shape}")
        print(f"   数据列: {list(df.columns)}")
        
    except Exception as e:
        print(f"   ❌ 数据加载失败: {e}")
        return False
    
    # 2. 测试数据不为None的情况
    print("\n2. 测试数据有效性...")
    if df is None:
        print("   ❌ 数据为None，这是之前的问题")
        return False
    else:
        print("   ✅ 数据不为None，问题已修复")
    
    # 3. 测试create_dashboard_metrics函数
    print("\n3. 测试仪表板指标创建...")
    try:
        metrics = create_dashboard_metrics(df)
        print("   ✅ 仪表板指标创建成功")
        print(f"   指标数量: {len(metrics)}")
        for key, value in list(metrics.items())[:5]:  # 显示前5个指标
            print(f"   • {key}: {value}")
    except Exception as e:
        print(f"   ❌ 仪表板指标创建失败: {e}")
        return False
    
    # 4. 测试UserProfileAnalyzer
    print("\n4. 测试用户画像分析器...")
    try:
        analyzer = UserProfileAnalyzer()
        print("   ✅ 用户画像分析器初始化成功")
        
        # 测试基础属性分析
        basic_analysis = analyzer.analyze_basic_attributes(df)
        print(f"   ✅ 基础属性分析成功，结果数量: {len(basic_analysis)}")
        
        # 测试活跃度分析
        activity_analysis = analyzer.analyze_activity_levels(df)
        print(f"   ✅ 活跃度分析成功，结果数量: {len(activity_analysis)}")
        
        # 测试影响力分析
        influence_analysis = analyzer.analyze_influence_metrics(df)
        print(f"   ✅ 影响力分析成功，结果数量: {len(influence_analysis)}")
        
    except Exception as e:
        print(f"   ❌ 用户画像分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 测试数据列访问
    print("\n5. 测试数据列访问...")
    try:
        # 检查关键列是否存在
        key_columns = ['用户ID', '性别', '注册省份', '微博数', '粉丝数']
        existing_columns = [col for col in key_columns if col in df.columns]
        missing_columns = [col for col in key_columns if col not in df.columns]
        
        print(f"   存在的关键列: {existing_columns}")
        if missing_columns:
            print(f"   缺失的关键列: {missing_columns}")
        
        # 测试列访问不会引发AttributeError
        if '用户ID' in df.columns:
            unique_users = df['用户ID'].nunique()
            print(f"   ✅ 用户ID列访问成功，唯一用户数: {unique_users}")
        
        print("   ✅ 数据列访问测试通过")
        
    except AttributeError as e:
        print(f"   ❌ 数据列访问出现AttributeError: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 数据列访问出现其他错误: {e}")
        return False
    
    print("\n=" * 60)
    print("🎉 所有用户画像模块测试通过！")
    print("\n修复总结:")
    print("• 添加了数据None检查，避免AttributeError")
    print("• 在数据加载后初始化filtered_data")
    print("• 确保所有分析函数都能正常处理数据")
    
    return True

def test_edge_cases():
    """测试边界情况"""
    print("\n\n边界情况测试...")
    print("=" * 60)
    
    # 测试空DataFrame
    print("\n1. 测试空DataFrame...")
    try:
        empty_df = pd.DataFrame()
        metrics = create_dashboard_metrics(empty_df)
        print("   ✅ 空DataFrame处理成功")
    except Exception as e:
        print(f"   ❌ 空DataFrame处理失败: {e}")
    
    # 测试只有部分列的DataFrame
    print("\n2. 测试部分列DataFrame...")
    try:
        partial_df = pd.DataFrame({
            '用户ID': [1, 2, 3],
            '性别': ['男', '女', '男']
        })
        metrics = create_dashboard_metrics(partial_df)
        print("   ✅ 部分列DataFrame处理成功")
    except Exception as e:
        print(f"   ❌ 部分列DataFrame处理失败: {e}")
    
    print("\n✅ 边界情况测试完成")

if __name__ == "__main__":
    # 运行主要测试
    success = test_user_profile_module()
    
    # 运行边界情况测试
    test_edge_cases()
    
    if success:
        print("\n🎉 用户画像模块修复验证成功！")
    else:
        print("\n❌ 用户画像模块仍存在问题")
        sys.exit(1)
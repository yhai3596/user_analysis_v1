#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据加载功能测试脚本
测试BigDataLoader和DataProcessor的各项功能
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from utils.data_loader import BigDataLoader, DataProcessor

def test_data_loading():
    """测试数据加载功能"""
    print("=" * 60)
    print("数据加载功能测试")
    print("=" * 60)
    
    # 初始化加载器
    loader = BigDataLoader()
    
    # 测试文件路径
    test_file = "e:\\AICoding\\用户数据分析\\切片.xlsx"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return False
    
    print(f"✅ 测试文件存在: {test_file}")
    
    try:
        # 1. 测试文件信息获取
        print("\n1. 测试文件信息获取...")
        info = loader.get_data_info(test_file)
        print(f"   文件大小: {info['file_size_mb']:.2f} MB")
        print(f"   预估内存: {info['estimated_memory_mb']:.2f} MB")
        print(f"   数据形状: {info['sample_shape']}")
        print(f"   列数量: {len(info['columns'])}")
        
        # 2. 测试样本数据加载
        print("\n2. 测试样本数据加载...")
        sample_df = loader.load_data_sample(test_file, sample_size=100)
        print(f"   样本数据形状: {sample_df.shape}")
        print(f"   内存使用: {sample_df.memory_usage(deep=True).sum() / 1024:.2f} KB")
        
        # 检查数据质量
        print(f"   缺失值数量: {sample_df.isnull().sum().sum()}")
        print(f"   重复行数量: {sample_df.duplicated().sum()}")
        
        # 3. 测试数据预处理
        print("\n3. 测试数据预处理...")
        processed_df = DataProcessor.preprocess_data(sample_df.copy())
        print(f"   预处理后形状: {processed_df.shape}")
        print(f"   预处理后缺失值: {processed_df.isnull().sum().sum()}")
        
        # 检查是否有无穷大值
        numeric_cols = processed_df.select_dtypes(include=[np.number]).columns
        inf_count = 0
        for col in numeric_cols:
            inf_count += np.isinf(processed_df[col]).sum()
        print(f"   无穷大值数量: {inf_count}")
        
        # 4. 测试分块加载（小规模测试）
        print("\n4. 测试分块加载...")
        chunk_count = 0
        total_rows = 0
        for chunk in loader.load_data_chunked(test_file, chunk_size=50):
            chunk_count += 1
            total_rows += len(chunk)
            if chunk_count >= 3:  # 只测试前3个块
                break
        print(f"   测试了 {chunk_count} 个数据块")
        print(f"   总行数: {total_rows}")
        
        # 5. 测试用户聚合功能
        print("\n5. 测试用户聚合功能...")
        if '用户ID' in sample_df.columns:
            user_agg = DataProcessor.aggregate_by_user(sample_df)
            print(f"   聚合后用户数: {len(user_agg)}")
            print(f"   聚合后列数: {user_agg.shape[1]}")
        else:
            print("   跳过用户聚合测试（无用户ID列）")
        
        # 6. 测试时间特征提取
        print("\n6. 测试时间特征提取...")
        if '发布时间' in sample_df.columns:
            time_features = DataProcessor.extract_time_features(sample_df)
            print(f"   时间特征提取后列数: {time_features.shape[1]}")
            new_cols = set(time_features.columns) - set(sample_df.columns)
            print(f"   新增时间特征: {list(new_cols)}")
        else:
            print("   跳过时间特征测试（无发布时间列）")
        
        # 7. 测试活跃度评分
        print("\n7. 测试活跃度评分...")
        activity_df = DataProcessor.calculate_user_activity_score(sample_df)
        if 'activity_score' in activity_df.columns:
            print(f"   活跃度评分范围: {activity_df['activity_score'].min():.2f} - {activity_df['activity_score'].max():.2f}")
            print(f"   平均活跃度: {activity_df['activity_score'].mean():.2f}")
        else:
            print("   活跃度评分计算失败")
        
        print("\n✅ 所有数据加载功能测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("错误处理测试")
    print("=" * 60)
    
    loader = BigDataLoader()
    
    # 测试不存在的文件
    print("\n1. 测试不存在的文件...")
    try:
        loader.load_data_sample("不存在的文件.xlsx")
        print("   ❌ 应该抛出异常但没有")
        return False
    except Exception as e:
        print(f"   ✅ 正确处理了文件不存在错误: {type(e).__name__}")
    
    # 测试空数据处理
    print("\n2. 测试空数据处理...")
    try:
        empty_df = pd.DataFrame()
        processed = DataProcessor.preprocess_data(empty_df)
        print(f"   ✅ 空数据处理成功，结果形状: {processed.shape}")
    except Exception as e:
        print(f"   ❌ 空数据处理失败: {str(e)}")
        return False
    
    # 测试包含异常值的数据
    print("\n3. 测试异常值处理...")
    try:
        # 创建包含异常值的测试数据
        test_data = pd.DataFrame({
            '用户ID': [1, 2, 3, 4, 5],
            '粉丝数': [100, 200, np.inf, 300, -np.inf],
            '关注数': [50, np.nan, 75, 100, 125],
            '性别': ['男', '女', None, '男', '女']
        })
        
        processed = DataProcessor.preprocess_data(test_data)
        
        # 检查无穷大值是否被处理
        inf_count = np.isinf(processed.select_dtypes(include=[np.number])).sum().sum()
        print(f"   ✅ 异常值处理成功，剩余无穷大值: {inf_count}")
        
        # 检查缺失值是否被处理
        null_count = processed.isnull().sum().sum()
        print(f"   ✅ 缺失值处理成功，剩余缺失值: {null_count}")
        
    except Exception as e:
        print(f"   ❌ 异常值处理失败: {str(e)}")
        return False
    
    print("\n✅ 所有错误处理测试通过！")
    return True

if __name__ == "__main__":
    print("开始数据加载功能测试...\n")
    
    # 运行测试
    test1_passed = test_data_loading()
    test2_passed = test_error_handling()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if test1_passed and test2_passed:
        print("🎉 所有测试通过！数据加载功能正常工作。")
    else:
        print("⚠️ 部分测试失败，请检查相关功能。")
        if not test1_passed:
            print("   - 数据加载功能测试失败")
        if not test2_passed:
            print("   - 错误处理测试失败")
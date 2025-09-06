#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据加载功能修复
验证load_data函数是否能正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from utils.data_loader import BigDataLoader
import pandas as pd

def test_data_loader_directly():
    """直接测试BigDataLoader类"""
    print("=== 测试BigDataLoader类 ===")
    
    try:
        loader = BigDataLoader()
        file_path = "e:\\AICoding\\用户数据分析\\切片.xlsx"
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"❌ 数据文件不存在: {file_path}")
            return False
        
        print(f"✅ 数据文件存在: {file_path}")
        
        # 测试获取数据信息
        print("\n--- 测试获取数据信息 ---")
        info = loader.get_data_info(file_path)
        print(f"✅ 数据信息获取成功:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        # 测试样本数据加载
        print("\n--- 测试样本数据加载 ---")
        sample_df = loader.load_data_sample(file_path, sample_size=100)
        print(f"✅ 样本数据加载成功: {sample_df.shape}")
        print(f"  列名: {list(sample_df.columns)}")
        print(f"  数据类型: {sample_df.dtypes.to_dict()}")
        
        return True
        
    except Exception as e:
        print(f"❌ BigDataLoader测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_load_data_function():
    """测试app.py中的load_data函数"""
    print("\n=== 测试load_data函数 ===")
    
    try:
        # 模拟streamlit session state
        class MockSessionState:
            def __init__(self):
                self.current_data = None
                self.data_loaded = False
                self.data_info = None
                self.filtered_data = None
        
        # 创建模拟的streamlit模块
        class MockStreamlit:
            def __init__(self):
                self.session_state = MockSessionState()
            
            def spinner(self, text):
                class SpinnerContext:
                    def __enter__(self):
                        print(f"🔄 {text}")
                        return self
                    def __exit__(self, *args):
                        pass
                return SpinnerContext()
            
            def success(self, text):
                print(f"✅ {text}")
            
            def error(self, text):
                print(f"❌ {text}")
        
        # 替换streamlit模块
        import sys
        mock_st = MockStreamlit()
        sys.modules['streamlit'] = mock_st
        
        # 导入并测试load_data函数
        from app import load_data
        
        file_path = "e:\\AICoding\\用户数据分析\\切片.xlsx"
        
        # 测试样本模式
        print("\n--- 测试样本模式 ---")
        load_data(file_path, 'sample')
        
        if mock_st.session_state.data_loaded:
            print(f"✅ 样本数据加载成功: {mock_st.session_state.current_data.shape}")
            print(f"  数据信息: {mock_st.session_state.data_info}")
        else:
            print("❌ 样本数据加载失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ load_data函数测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试数据加载功能修复...\n")
    
    # 测试1: 直接测试BigDataLoader
    test1_result = test_data_loader_directly()
    
    # 测试2: 测试load_data函数
    test2_result = test_load_data_function()
    
    # 总结
    print("\n=== 测试结果总结 ===")
    print(f"BigDataLoader测试: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"load_data函数测试: {'✅ 通过' if test2_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！数据加载功能已修复。")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要进一步检查。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
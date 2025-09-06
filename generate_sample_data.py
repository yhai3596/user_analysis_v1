#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成示例数据文件
用于替换原始数据文件，避免在git仓库中包含敏感数据
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_sample_data(num_records=5000):
    """
    生成示例用户行为数据
    """
    # 设置随机种子以确保可重现性
    np.random.seed(42)
    random.seed(42)
    
    # 生成用户ID
    user_ids = [f"user_{i:06d}" for i in range(1, num_records // 10 + 1)]
    
    # 生成数据
    data = []
    
    for i in range(num_records):
        # 随机选择用户
        user_id = random.choice(user_ids)
        
        # 生成时间戳（最近30天内）
        base_time = datetime.now() - timedelta(days=30)
        random_days = random.randint(0, 30)
        random_hours = random.randint(0, 23)
        random_minutes = random.randint(0, 59)
        publish_time = base_time + timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
        
        # 生成地理位置
        cities = ['北京', '上海', '广州', '深圳', '杭州', '南京', '成都', '武汉', '西安', '重庆']
        city = random.choice(cities)
        
        # 生成经纬度（中国范围内）
        longitude = round(random.uniform(73.66, 135.05), 6)
        latitude = round(random.uniform(3.86, 53.55), 6)
        
        # 生成内容相关数据
        content_types = ['文本', '图片', '视频', '链接']
        content_type = random.choice(content_types)
        
        # 生成互动数据
        likes = random.randint(0, 1000)
        comments = random.randint(0, 200)
        shares = random.randint(0, 100)
        
        # 生成用户属性
        age_groups = ['18-25', '26-35', '36-45', '46-55', '55+']
        age_group = random.choice(age_groups)
        
        genders = ['男', '女']
        gender = random.choice(genders)
        
        # 生成设备信息
        devices = ['iOS', 'Android', 'Web']
        device = random.choice(devices)
        
        # 生成话题标签
        topics = ['科技', '娱乐', '体育', '新闻', '生活', '美食', '旅游', '教育', '健康', '时尚']
        topic = random.choice(topics)
        
        record = {
            '用户ID': user_id,
            '发布时间': publish_time.strftime('%Y-%m-%d %H:%M:%S'),
            '城市': city,
            '经度': longitude,
            '纬度': latitude,
            '内容类型': content_type,
            '点赞数': likes,
            '评论数': comments,
            '分享数': shares,
            '年龄段': age_group,
            '性别': gender,
            '设备类型': device,
            '话题标签': topic,
            '内容长度': random.randint(10, 500),
            '活跃度得分': round(random.uniform(0, 100), 2)
        }
        
        data.append(record)
    
    return pd.DataFrame(data)

def main():
    """
    主函数：生成示例数据并保存
    """
    print("正在生成示例数据...")
    
    # 生成数据
    df = generate_sample_data(5000)
    
    # 保存为Excel文件
    output_file = "切片.xlsx"
    df.to_excel(output_file, index=False, engine='openpyxl')
    
    print(f"示例数据已生成并保存到: {output_file}")
    print(f"数据形状: {df.shape}")
    print(f"列名: {list(df.columns)}")
    
    # 显示前几行数据
    print("\n前5行数据预览:")
    print(df.head())
    
    # 显示数据统计信息
    print("\n数据统计信息:")
    print(f"用户数量: {df['用户ID'].nunique()}")
    print(f"时间范围: {df['发布时间'].min()} 到 {df['发布时间'].max()}")
    print(f"城市数量: {df['城市'].nunique()}")
    print(f"内容类型: {df['内容类型'].unique()}")

if __name__ == "__main__":
    main()
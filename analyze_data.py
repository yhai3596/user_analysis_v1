import pandas as pd
import numpy as np

# 读取Excel文件
df = pd.read_excel('切片.xlsx')

print('='*60)
print('数据集基本信息')
print('='*60)
print(f'总行数: {len(df)}')
print(f'总列数: {len(df.columns)}')

print('\n' + '='*60)
print('完整列名列表')
print('='*60)
for i, col in enumerate(df.columns, 1):
    print(f'{i:2d}. {col}')

print('\n' + '='*60)
print('数据类型')
print('='*60)
for col in df.columns:
    print(f'{col}: {df[col].dtype}')

print('\n' + '='*60)
print('缺失值统计')
print('='*60)
missing = df.isnull().sum()
missing_cols = missing[missing > 0]
if len(missing_cols) > 0:
    for col, count in missing_cols.items():
        print(f'{col}: {count}个缺失值 ({count/len(df)*100:.1f}%)')
else:
    print('没有缺失值')

print('\n' + '='*60)
print('各列唯一值数量')
print('='*60)
for col in df.columns:
    unique_count = df[col].nunique()
    print(f'{col}: {unique_count}个唯一值')

print('\n' + '='*60)
print('前3行完整数据展示')
print('='*60)
for i in range(min(3, len(df))):
    print(f'\n第{i+1}行数据:')
    print('-' * 40)
    for col in df.columns:
        value = df.iloc[i][col]
        if pd.isna(value):
            value = 'NaN'
        print(f'{col}: {value}')

print('\n' + '='*60)
print('数值型字段统计信息')
print('='*60)
numeric_cols = df.select_dtypes(include=[np.number]).columns
if len(numeric_cols) > 0:
    print(df[numeric_cols].describe())
else:
    print('没有数值型字段')

print('\n' + '='*60)
print('文本型字段示例')
print('='*60)
text_cols = df.select_dtypes(include=['object']).columns
for col in text_cols[:5]:  # 只显示前5个文本字段
    print(f'\n{col}字段示例值:')
    unique_vals = df[col].dropna().unique()[:3]
    for val in unique_vals:
        print(f'  - {val}')
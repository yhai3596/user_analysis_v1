import pandas as pd
import re

# 读取数据文件
df = pd.read_excel('切片.xlsx')

print('微博文本内容示例:')
for i, content in enumerate(df['微博文本'].dropna().head(20), 1):
    print(f'{i}. {repr(content)}')
    
print('\n检查异常内容:')
for i, content in enumerate(df['微博文本'].dropna(), 1):
    content_str = str(content)
    # 检查是否包含大量数字或英文字符
    if re.search(r'[0-9]{5,}', content_str) or re.search(r'[A-Za-z]{10,}', content_str):
        print(f'可能异常内容 {i}: {repr(content_str)}')
        if i > 50:  # 只检查前50条
            break
            
print('\n内容统计:')
print('总条数:', len(df))
print('非空微博文本数:', df['微博文本'].notna().sum())
print('空值数:', df['微博文本'].isna().sum())

# 分析内容特征
valid_contents = df['微博文本'].dropna()
print('\n内容特征分析:')
print('平均长度:', valid_contents.str.len().mean())
print('最大长度:', valid_contents.str.len().max())
print('最小长度:', valid_contents.str.len().min())

# 检查是否有重复内容
print('\n重复内容分析:')
duplicated = valid_contents.duplicated().sum()
print('重复内容数量:', duplicated)
if duplicated > 0:
    print('重复内容示例:')
    dup_contents = valid_contents[valid_contents.duplicated(keep=False)].unique()
    for i, content in enumerate(dup_contents[:5], 1):
        print(f'{i}. {repr(content)}')
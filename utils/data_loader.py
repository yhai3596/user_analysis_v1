import pandas as pd
import numpy as np
import os
import pickle
from typing import Iterator, Optional, Dict, Any, List
import gc
from functools import wraps
import hashlib
import json

class BigDataLoader:
    """
    大数据加载器，支持分块读取、内存优化和缓存机制
    """
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # 数据类型优化映射
        self.dtype_optimization = {
            '用户ID': 'int64',
            '性别': 'category',
            '转发数': 'int16',
            '评论数': 'int16', 
            '点赞数': 'int16',
            '微博数': 'int32',
            '关注数': 'int32',
            '粉丝数': 'int32',
            '地点ID': 'int64',
            '微博ID': 'int64'
        }
    
    def _get_cache_key(self, file_path: str, **kwargs) -> str:
        """生成缓存键"""
        cache_data = {
            'file_path': file_path,
            'file_mtime': os.path.getmtime(file_path),
            'kwargs': kwargs
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _save_cache(self, key: str, data: Any) -> None:
        """保存缓存"""
        cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
    
    def _load_cache(self, key: str) -> Optional[Any]:
        """加载缓存"""
        cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                # 缓存文件损坏，删除它
                os.remove(cache_file)
        return None
    
    def optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """优化数据类型以减少内存使用"""
        for col, dtype in self.dtype_optimization.items():
            if col in df.columns:
                if dtype == 'category':
                    df[col] = df[col].astype('category')
                else:
                    # 转换为数值类型并处理异常值
                    numeric_series = pd.to_numeric(df[col], errors='coerce')
                    
                    # 处理无穷大值
                    numeric_series = numeric_series.replace([np.inf, -np.inf], np.nan)
                    
                    # 对于整数类型，填充NaN为0或中位数
                    if 'int' in dtype:
                        if numeric_series.isna().all():
                            # 如果全是NaN，填充为0
                            numeric_series = numeric_series.fillna(0)
                        else:
                            # 使用中位数填充NaN
                            median_val = numeric_series.median()
                            if pd.isna(median_val):
                                median_val = 0
                            numeric_series = numeric_series.fillna(median_val)
                    
                    # 确保数值在合理范围内
                    if dtype == 'int16':
                        numeric_series = numeric_series.clip(-32768, 32767)
                    elif dtype == 'int32':
                        numeric_series = numeric_series.clip(-2147483648, 2147483647)
                    
                    df[col] = numeric_series.astype(dtype)
        
        # 优化字符串列
        for col in df.select_dtypes(include=['object']).columns:
            if col not in self.dtype_optimization:
                # 尝试转换为category如果唯一值较少
                if len(df) > 0 and df[col].nunique() / len(df) < 0.5:
                    df[col] = df[col].astype('category')
        
        return df
    
    def load_data_chunked(self, file_path: str, chunk_size: int = 10000, 
                         usecols: Optional[List[str]] = None,
                         use_cache: bool = True) -> Iterator[pd.DataFrame]:
        """分块读取数据"""
        cache_key = self._get_cache_key(file_path, chunk_size=chunk_size, usecols=usecols)
        
        if use_cache:
            cached_data = self._load_cache(cache_key)
            if cached_data is not None:
                for chunk in cached_data:
                    yield chunk
                return
        
        chunks = []
        try:
            # 根据文件扩展名选择读取方法
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                # Excel文件不支持chunksize，需要先读取全部数据再分块
                full_data = pd.read_excel(file_path, usecols=usecols)
                
                # 手动分块
                for start in range(0, len(full_data), chunk_size):
                    end = min(start + chunk_size, len(full_data))
                    chunk = full_data.iloc[start:end].copy()
                    
                    # 优化数据类型
                    chunk = self.optimize_dtypes(chunk)
                    chunks.append(chunk)
                    yield chunk
                    
                    # 强制垃圾回收
                    gc.collect()
                    
                # 清理完整数据以释放内存
                del full_data
                gc.collect()
                
            elif file_path.endswith('.csv'):
                reader = pd.read_csv(file_path, chunksize=chunk_size, usecols=usecols)
                for chunk in reader:
                    # 优化数据类型
                    chunk = self.optimize_dtypes(chunk)
                    chunks.append(chunk)
                    yield chunk
                    
                    # 强制垃圾回收
                    gc.collect()
            else:
                raise ValueError(f"不支持的文件格式: {file_path}")
            
            # 保存到缓存
            if use_cache:
                self._save_cache(cache_key, chunks)
                
        except Exception as e:
            print(f"读取文件时出错: {e}")
            raise
    
    def load_data_sample(self, file_path: str, sample_size: int = 1000,
                        usecols: Optional[List[str]] = None,
                        use_cache: bool = True) -> pd.DataFrame:
        """加载数据样本用于快速分析"""
        cache_key = self._get_cache_key(file_path, sample_size=sample_size, usecols=usecols)
        
        if use_cache:
            cached_data = self._load_cache(cache_key)
            if cached_data is not None:
                return cached_data
        
        try:
            # 读取前N行作为样本
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                # 对于Excel文件，先尝试读取原始数据
                df = pd.read_excel(file_path, nrows=sample_size, usecols=usecols)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path, nrows=sample_size, usecols=usecols)
            else:
                raise ValueError(f"不支持的文件格式: {file_path}")
            
            # 数据清洗：处理异常值
            for col in df.columns:
                if df[col].dtype in ['object', 'string']:
                    continue
                    
                # 替换无穷大值为NaN
                df[col] = df[col].replace([np.inf, -np.inf], np.nan)
                
                # 对于数值列，检查是否有异常大的值
                if pd.api.types.is_numeric_dtype(df[col]):
                    # 使用IQR方法检测异常值
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    
                    # 设置合理的上下界
                    lower_bound = Q1 - 3 * IQR
                    upper_bound = Q3 + 3 * IQR
                    
                    # 将异常值替换为边界值
                    df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
            
            # 优化数据类型
            df = self.optimize_dtypes(df)
            
            if use_cache:
                self._save_cache(cache_key, df)
            
            return df
            
        except Exception as e:
            print(f"读取样本数据时出错: {e}")
            raise
    
    def get_data_info(self, file_path: str) -> Dict[str, Any]:
        """获取数据文件基本信息"""
        cache_key = self._get_cache_key(file_path, info_only=True)
        
        cached_info = self._load_cache(cache_key)
        if cached_info is not None:
            return cached_info
        
        try:
            # 读取少量数据获取结构信息
            sample_df = self.load_data_sample(file_path, sample_size=100, use_cache=False)
            
            info = {
                'columns': list(sample_df.columns),
                'dtypes': sample_df.dtypes.to_dict(),
                'sample_shape': sample_df.shape,
                'file_size_mb': os.path.getsize(file_path) / (1024 * 1024),
                'estimated_memory_mb': sample_df.memory_usage(deep=True).sum() / (1024 * 1024)
            }
            
            self._save_cache(cache_key, info)
            return info
            
        except Exception as e:
            print(f"获取数据信息时出错: {e}")
            raise
    
    def clear_cache(self) -> None:
        """清空缓存"""
        for file in os.listdir(self.cache_dir):
            if file.endswith('.pkl'):
                os.remove(os.path.join(self.cache_dir, file))
        print("缓存已清空")


def memory_efficient(func):
    """内存优化装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 执行前垃圾回收
        gc.collect()
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # 执行后垃圾回收
            gc.collect()
    
    return wrapper


class DataProcessor:
    """数据处理工具类"""
    
    @staticmethod
    @memory_efficient
    def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
        """数据预处理"""
        df = df.copy()
        
        # 处理缺失值
        for col in df.columns:
            if df[col].dtype == 'object':
                # 字符串列用'未知'填充
                df[col] = df[col].fillna('未知')
            elif df[col].dtype.name == 'category':
                # 分类列需要先添加'未知'到类别中
                if '未知' not in df[col].cat.categories:
                    df[col] = df[col].cat.add_categories(['未知'])
                df[col] = df[col].fillna('未知')
            elif pd.api.types.is_numeric_dtype(df[col]):
                # 数值列用中位数填充
                if df[col].notna().any():
                    try:
                        median_val = df[col].median()
                        df[col] = df[col].fillna(median_val)
                    except (TypeError, ValueError):
                        # 如果median计算失败，使用0填充
                        df[col] = df[col].fillna(0)
                else:
                    df[col] = df[col].fillna(0)
            else:
                # 其他类型用'未知'填充
                df[col] = df[col].fillna('未知')
        
        # 处理异常值 - 只处理纯数值列
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            # 跳过分类数据类型
            if df[col].dtype.name == 'category':
                continue
                
            # 替换无穷大值
            df[col] = df[col].replace([np.inf, -np.inf], np.nan)
            
            # 使用IQR方法处理异常值
            try:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                if IQR > 0 and not pd.isna(Q1) and not pd.isna(Q3):
                    lower_bound = Q1 - 3 * IQR
                    upper_bound = Q3 + 3 * IQR
                    df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
                
                # 再次填充可能产生的NaN
                if df[col].isna().any():
                    median_val = df[col].median()
                    if pd.isna(median_val):
                        median_val = 0
                    df[col] = df[col].fillna(median_val)
            except (TypeError, ValueError):
                # 如果统计计算失败，只填充NaN为0
                df[col] = df[col].fillna(0)
        
        return df
    
    @staticmethod
    @memory_efficient
    def aggregate_by_user(df: pd.DataFrame) -> pd.DataFrame:
        """按用户聚合数据"""
        user_agg = df.groupby('用户ID').agg({
            '性别': 'first',
            '昵称': 'first', 
            '注册省份': 'first',
            '注册城市': 'first',
            '微博数': 'first',
            '关注数': 'first',
            '粉丝数': 'first',
            '个人简介': 'first',
            '转发数': ['sum', 'mean', 'max'],
            '评论数': ['sum', 'mean', 'max'],
            '点赞数': ['sum', 'mean', 'max'],
            '发布时间': ['count', 'min', 'max']
        }).reset_index()
        
        # 扁平化列名
        user_agg.columns = ['_'.join(col).strip() if col[1] else col[0] 
                           for col in user_agg.columns.values]
        
        return user_agg
    
    @staticmethod
    @memory_efficient
    def extract_time_features(df: pd.DataFrame, time_col: str = '发布时间') -> pd.DataFrame:
        """提取时间特征"""
        df = df.copy()
        df[time_col] = pd.to_datetime(df[time_col])
        
        df['hour'] = df[time_col].dt.hour
        df['day_of_week'] = df[time_col].dt.dayofweek
        df['month'] = df[time_col].dt.month
        df['is_weekend'] = df['day_of_week'].isin([5, 6])
        
        return df
    
    @staticmethod
    @memory_efficient
    def calculate_user_activity_score(df: pd.DataFrame) -> pd.DataFrame:
        """计算用户活跃度得分"""
        df = df.copy()
        
        # 标准化各项指标
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        
        activity_features = ['微博数', '关注数', '粉丝数', '转发数', '评论数', '点赞数']
        available_features = [col for col in activity_features if col in df.columns]
        
        if available_features:
            df[available_features] = scaler.fit_transform(df[available_features].fillna(0))
            df['activity_score'] = df[available_features].mean(axis=1)
        
        return df


if __name__ == "__main__":
    # 测试代码
    loader = BigDataLoader()
    
    # 测试数据信息获取
    file_path = "切片.xlsx"  # 使用相对路径
    if os.path.exists(file_path):
        info = loader.get_data_info(file_path)
        print("数据文件信息:")
        for key, value in info.items():
            print(f"{key}: {value}")
        
        # 测试样本加载
        sample_df = loader.load_data_sample(file_path, sample_size=50)
        print(f"\n样本数据形状: {sample_df.shape}")
        print(f"内存使用: {sample_df.memory_usage(deep=True).sum() / 1024:.2f} KB")
import streamlit as st
import pandas as pd
import hashlib
import pickle
import os
from typing import Any, Optional, Callable
from functools import wraps
import time

class StreamlitCacheManager:
    """
    Streamlit缓存管理器，提供更灵活的缓存控制
    """
    
    def __init__(self, cache_dir: str = "streamlit_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, func_name: str, *args, **kwargs) -> str:
        """生成缓存键"""
        cache_data = {
            'func_name': func_name,
            'args': str(args),
            'kwargs': str(sorted(kwargs.items()))
        }
        cache_str = str(cache_data)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _save_to_disk(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """保存数据到磁盘"""
        cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
        cache_info = {
            'data': data,
            'timestamp': time.time(),
            'ttl': ttl
        }
        with open(cache_file, 'wb') as f:
            pickle.dump(cache_info, f)
    
    def _load_from_disk(self, key: str) -> Optional[Any]:
        """从磁盘加载数据"""
        cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                cache_info = pickle.load(f)
            
            # 检查TTL
            if cache_info.get('ttl'):
                if time.time() - cache_info['timestamp'] > cache_info['ttl']:
                    os.remove(cache_file)
                    return None
            
            return cache_info['data']
        except Exception:
            # 缓存文件损坏，删除它
            if os.path.exists(cache_file):
                os.remove(cache_file)
            return None
    
    def cache_data(self, func: Callable = None, *, ttl: Optional[int] = None, 
                   persist: bool = False, show_spinner: bool = True):
        """缓存装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = self._get_cache_key(func.__name__, *args, **kwargs)
                
                # 尝试从Streamlit缓存加载
                if not persist:
                    if cache_key in st.session_state:
                        return st.session_state[cache_key]
                else:
                    # 尝试从磁盘加载
                    cached_data = self._load_from_disk(cache_key)
                    if cached_data is not None:
                        return cached_data
                
                # 执行函数
                if show_spinner:
                    with st.spinner(f'正在执行 {func.__name__}...'):
                        result = func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # 保存到缓存
                if not persist:
                    st.session_state[cache_key] = result
                else:
                    self._save_to_disk(cache_key, result, ttl)
                
                return result
            
            return wrapper
        
        if func is None:
            return decorator
        else:
            return decorator(func)
    
    def clear_cache(self, pattern: Optional[str] = None) -> None:
        """清空缓存"""
        # 清空session state
        if pattern:
            keys_to_remove = [key for key in st.session_state.keys() if pattern in key]
            for key in keys_to_remove:
                del st.session_state[key]
        else:
            st.session_state.clear()
        
        # 清空磁盘缓存
        for file in os.listdir(self.cache_dir):
            if file.endswith('.pkl'):
                if pattern is None or pattern in file:
                    os.remove(os.path.join(self.cache_dir, file))
    
    def get_cache_info(self) -> dict:
        """获取缓存信息"""
        session_cache_size = len(st.session_state)
        
        disk_cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.pkl')]
        disk_cache_size = len(disk_cache_files)
        
        total_disk_size = sum(
            os.path.getsize(os.path.join(self.cache_dir, f)) 
            for f in disk_cache_files
        ) / (1024 * 1024)  # MB
        
        return {
            'session_cache_items': session_cache_size,
            'disk_cache_items': disk_cache_size,
            'disk_cache_size_mb': round(total_disk_size, 2)
        }


# 全局缓存管理器实例
cache_manager = StreamlitCacheManager()


# 常用缓存装饰器
def cache_data(func=None, *, ttl=None, persist=False, show_spinner=True):
    """数据缓存装饰器"""
    return cache_manager.cache_data(func, ttl=ttl, persist=persist, show_spinner=show_spinner)


def cache_resource(func=None, *, ttl=None, show_spinner=True):
    """资源缓存装饰器（持久化）"""
    return cache_manager.cache_data(func, ttl=ttl, persist=True, show_spinner=show_spinner)


class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, total_steps: int, description: str = "处理中"):
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
    
    def update(self, step: int = 1, status: str = None):
        """更新进度"""
        self.current_step += step
        progress = min(self.current_step / self.total_steps, 1.0)
        self.progress_bar.progress(progress)
        
        if status:
            self.status_text.text(f"{self.description}: {status} ({self.current_step}/{self.total_steps})")
        else:
            self.status_text.text(f"{self.description}: {self.current_step}/{self.total_steps}")
    
    def complete(self, message: str = "完成"):
        """完成进度"""
        self.progress_bar.progress(1.0)
        self.status_text.text(message)
    
    def clear(self):
        """清除进度显示"""
        self.progress_bar.empty()
        self.status_text.empty()


class DataCache:
    """数据缓存类"""
    
    @staticmethod
    @cache_data(persist=True, ttl=3600)  # 1小时TTL
    def load_processed_data(file_path: str, processing_params: dict) -> pd.DataFrame:
        """加载处理后的数据"""
        from .data_loader import BigDataLoader
        
        loader = BigDataLoader()
        
        # 根据参数决定加载方式
        if processing_params.get('sample_only', False):
            return loader.load_data_sample(
                file_path, 
                sample_size=processing_params.get('sample_size', 1000)
            )
        else:
            # 分块加载并合并
            chunks = []
            for chunk in loader.load_data_chunked(
                file_path, 
                chunk_size=processing_params.get('chunk_size', 10000)
            ):
                chunks.append(chunk)
            return pd.concat(chunks, ignore_index=True)
    
    @staticmethod
    @cache_data(persist=True, ttl=1800)  # 30分钟TTL
    def get_user_aggregation(df: pd.DataFrame) -> pd.DataFrame:
        """获取用户聚合数据"""
        from .data_loader import DataProcessor
        return DataProcessor.aggregate_by_user(df)
    
    @staticmethod
    @cache_data(persist=True, ttl=1800)
    def get_time_analysis_data(df: pd.DataFrame) -> pd.DataFrame:
        """获取时间分析数据"""
        from .data_loader import DataProcessor
        return DataProcessor.extract_time_features(df)
    
    @staticmethod
    @cache_resource(ttl=7200)  # 2小时TTL
    def load_ml_models():
        """加载机器学习模型"""
        # 这里可以加载预训练的模型
        # 例如：情感分析模型、主题模型等
        return {
            'sentiment_model': None,  # 实际使用时加载真实模型
            'topic_model': None,
            'clustering_model': None
        }


def clear_all_cache():
    """清空所有缓存"""
    cache_manager.clear_cache()
    st.success("所有缓存已清空")


def show_cache_info():
    """显示缓存信息"""
    info = cache_manager.get_cache_info()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("会话缓存项", info['session_cache_items'])
    with col2:
        st.metric("磁盘缓存项", info['disk_cache_items'])
    with col3:
        st.metric("磁盘缓存大小(MB)", info['disk_cache_size_mb'])


if __name__ == "__main__":
    # 测试代码
    @cache_data(ttl=60)
    def test_function(x, y):
        time.sleep(1)  # 模拟耗时操作
        return x + y
    
    print("测试缓存功能...")
    start_time = time.time()
    result1 = test_function(1, 2)
    print(f"第一次调用耗时: {time.time() - start_time:.2f}秒")
    
    start_time = time.time()
    result2 = test_function(1, 2)
    print(f"第二次调用耗时: {time.time() - start_time:.2f}秒")
    
    print(f"结果一致: {result1 == result2}")
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, List, Optional, Tuple, Any
import folium
from streamlit_folium import st_folium
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

class UserBehaviorVisualizer:
    """
    用户行为分析可视化工具类
    """
    
    def __init__(self):
        # 设置中文字体和颜色主题
        self.color_palette = px.colors.qualitative.Set3
        self.map_style = "OpenStreetMap"
        
        # 中文字体设置（用于wordcloud）
        self.font_path = None  # 可以设置中文字体路径
    
    def plot_user_distribution(self, df: pd.DataFrame, 
                              group_by: str = '性别',
                              chart_type: str = 'pie') -> go.Figure:
        """用户分布图"""
        if group_by not in df.columns:
            st.error(f"列 '{group_by}' 不存在")
            return go.Figure()
        
        # 统计分布
        distribution = df[group_by].value_counts()
        
        if chart_type == 'pie':
            fig = px.pie(
                values=distribution.values,
                names=distribution.index,
                title=f'用户{group_by}分布',
                color_discrete_sequence=self.color_palette
            )
        elif chart_type == 'bar':
            fig = px.bar(
                x=distribution.index,
                y=distribution.values,
                title=f'用户{group_by}分布',
                labels={'x': group_by, 'y': '用户数量'},
                color_discrete_sequence=self.color_palette
            )
        else:
            fig = go.Figure()
        
        fig.update_layout(
            font=dict(size=12),
            title_font_size=16,
            showlegend=True
        )
        
        return fig
    
    def plot_activity_metrics(self, df: pd.DataFrame) -> go.Figure:
        """用户活跃度指标图"""
        metrics = ['微博数', '关注数', '粉丝数', '转发数', '评论数', '点赞数']
        available_metrics = [m for m in metrics if m in df.columns]
        
        if not available_metrics:
            st.error("没有找到活跃度相关指标")
            return go.Figure()
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=available_metrics[:6],
            specs=[[{"secondary_y": False}] * 3] * 2
        )
        
        for i, metric in enumerate(available_metrics[:6]):
            row = i // 3 + 1
            col = i % 3 + 1
            
            # 计算统计信息
            data = df[metric].dropna()
            
            # 添加直方图
            fig.add_trace(
                go.Histogram(
                    x=data,
                    name=metric,
                    showlegend=False,
                    marker_color=self.color_palette[i % len(self.color_palette)]
                ),
                row=row, col=col
            )
        
        fig.update_layout(
            title_text="用户活跃度指标分布",
            title_font_size=16,
            height=600
        )
        
        return fig
    
    def plot_geographic_heatmap(self, df: pd.DataFrame, 
                               lat_col: str = '纬度', 
                               lon_col: str = '经度') -> folium.Map:
        """地理位置热力图"""
        if lat_col not in df.columns or lon_col not in df.columns:
            st.error(f"缺少地理坐标列: {lat_col}, {lon_col}")
            return folium.Map()
        
        # 过滤有效坐标
        geo_df = df[[lat_col, lon_col]].dropna()
        
        if geo_df.empty:
            st.error("没有有效的地理坐标数据")
            return folium.Map()
        
        # 计算地图中心点
        center_lat = geo_df[lat_col].mean()
        center_lon = geo_df[lon_col].mean()
        
        # 创建地图
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=10,
            tiles='OpenStreetMap'
        )
        
        # 添加热力图
        from folium.plugins import HeatMap
        heat_data = [[row[lat_col], row[lon_col]] for idx, row in geo_df.iterrows()]
        HeatMap(heat_data).add_to(m)
        
        # 添加聚类标记
        from folium.plugins import MarkerCluster
        marker_cluster = MarkerCluster().add_to(m)
        
        # 采样显示部分点（避免过多标记）
        sample_size = min(100, len(geo_df))
        sample_df = geo_df.sample(n=sample_size)
        
        for idx, row in sample_df.iterrows():
            folium.Marker(
                [row[lat_col], row[lon_col]],
                popup=f"位置: ({row[lat_col]:.4f}, {row[lon_col]:.4f})"
            ).add_to(marker_cluster)
        
        return m
    
    def plot_time_series(self, df: pd.DataFrame, 
                        time_col: str = '发布时间',
                        value_col: str = None,
                        aggregation: str = 'count') -> go.Figure:
        """时间序列分析图"""
        if time_col not in df.columns:
            st.error(f"时间列 '{time_col}' 不存在")
            return go.Figure()
        
        # 转换时间格式
        df_time = df.copy()
        df_time[time_col] = pd.to_datetime(df_time[time_col])
        
        if aggregation == 'count':
            # 按时间统计数量
            time_series = df_time.set_index(time_col).resample('H').size()
            y_label = '发布数量'
            title = '用户发布时间分布'
        elif value_col and value_col in df.columns:
            # 按时间聚合指定列
            if aggregation == 'sum':
                time_series = df_time.set_index(time_col)[value_col].resample('H').sum()
            elif aggregation == 'mean':
                time_series = df_time.set_index(time_col)[value_col].resample('H').mean()
            else:
                time_series = df_time.set_index(time_col)[value_col].resample('H').count()
            y_label = f'{value_col} ({aggregation})'
            title = f'{value_col}时间趋势'
        else:
            st.error("请指定有效的数值列")
            return go.Figure()
        
        # 创建时间序列图
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=time_series.index,
            y=time_series.values,
            mode='lines+markers',
            name=y_label,
            line=dict(color=self.color_palette[0])
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title='时间',
            yaxis_title=y_label,
            font=dict(size=12),
            title_font_size=16
        )
        
        return fig
    
    def plot_hourly_activity(self, df: pd.DataFrame, 
                           time_col: str = '发布时间') -> go.Figure:
        """24小时活跃度分析"""
        if time_col not in df.columns:
            st.error(f"时间列 '{time_col}' 不存在")
            return go.Figure()
        
        # 提取小时信息
        df_hour = df.copy()
        df_hour[time_col] = pd.to_datetime(df_hour[time_col])
        df_hour['hour'] = df_hour[time_col].dt.hour
        
        # 统计每小时活跃度
        hourly_activity = df_hour['hour'].value_counts().sort_index()
        
        # 创建极坐标图
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=hourly_activity.values,
            theta=[f"{h}:00" for h in hourly_activity.index],
            fill='toself',
            name='活跃度',
            line_color=self.color_palette[0]
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, hourly_activity.max()]
                )
            ),
            title="24小时活跃度分布",
            title_font_size=16
        )
        
        return fig
    
    def plot_correlation_matrix(self, df: pd.DataFrame, 
                              numeric_cols: Optional[List[str]] = None) -> go.Figure:
        """相关性矩阵热力图"""
        if numeric_cols is None:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            st.error("需要至少2个数值列来计算相关性")
            return go.Figure()
        
        # 计算相关性矩阵
        corr_matrix = df[numeric_cols].corr()
        
        # 创建热力图
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmid=0,
            text=np.round(corr_matrix.values, 2),
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title='特征相关性矩阵',
            title_font_size=16,
            width=600,
            height=600
        )
        
        return fig
    
    def create_wordcloud(self, text_data: List[str], 
                        max_words: int = 100) -> plt.Figure:
        """生成词云图"""
        if not text_data:
            st.error("没有文本数据")
            return plt.figure()
        
        # 合并所有文本
        text = ' '.join([str(t) for t in text_data if pd.notna(t)])
        
        if not text.strip():
            st.error("文本数据为空")
            return plt.figure()
        
        # 创建词云
        try:
            # 尝试使用系统字体
            wordcloud = WordCloud(
                width=800,
                height=400,
                background_color='white',
                max_words=max_words,
                colormap='viridis',
                prefer_horizontal=0.9,
                relative_scaling=0.5
            ).generate(text)
        except Exception:
            # 如果出现字体问题，使用默认设置
            wordcloud = WordCloud(
                width=800,
                height=400,
                background_color='white',
                max_words=max_words,
                colormap='viridis'
            ).generate(text)
        
        # 创建matplotlib图形
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_title('词云图', fontsize=16)
        
        return fig
    
    def plot_user_influence_scatter(self, df: pd.DataFrame) -> go.Figure:
        """用户影响力散点图"""
        required_cols = ['粉丝数', '微博数', '转发数']
        available_cols = [col for col in required_cols if col in df.columns]
        
        if len(available_cols) < 2:
            st.error("需要至少2个影响力指标")
            return go.Figure()
        
        x_col = available_cols[0]
        y_col = available_cols[1]
        size_col = available_cols[2] if len(available_cols) > 2 else None
        
        # 过滤异常值
        df_clean = df[(df[x_col] >= 0) & (df[y_col] >= 0)].copy()
        
        if size_col:
            df_clean = df_clean[df_clean[size_col] >= 0]
        
        # 创建散点图
        fig = px.scatter(
            df_clean,
            x=x_col,
            y=y_col,
            size=size_col if size_col else None,
            color='性别' if '性别' in df.columns else None,
            hover_data=['昵称'] if '昵称' in df.columns else None,
            title='用户影响力分析',
            labels={x_col: x_col, y_col: y_col}
        )
        
        fig.update_layout(
            font=dict(size=12),
            title_font_size=16
        )
        
        return fig
    
    def plot_engagement_funnel(self, df: pd.DataFrame) -> go.Figure:
        """用户参与度漏斗图"""
        engagement_cols = ['转发数', '评论数', '点赞数']
        available_cols = [col for col in engagement_cols if col in df.columns]
        
        if not available_cols:
            st.error("没有找到参与度相关指标")
            return go.Figure()
        
        # 计算各级参与度的用户数
        funnel_data = []
        for col in available_cols:
            count = (df[col] > 0).sum()
            funnel_data.append((col, count))
        
        # 添加总用户数
        funnel_data.insert(0, ('总用户数', len(df)))
        
        # 创建漏斗图
        fig = go.Figure(go.Funnel(
            y=[item[0] for item in funnel_data],
            x=[item[1] for item in funnel_data],
            textinfo="value+percent initial"
        ))
        
        fig.update_layout(
            title="用户参与度漏斗分析",
            title_font_size=16
        )
        
        return fig


def create_dashboard_metrics(df):
    """创建仪表板指标"""
    metrics = {}
    
    # 检查数据是否为None或空
    if df is None:
        return {
            'total_users': 0,
            'total_posts': 0,
            'avg_activity': 0,
            'avg_engagement': 0,
            'top_province': '无数据',
            'date_range': '无数据'
        }
    
    if df.empty:
        return {
            'total_users': 0,
            'total_posts': 0,
            'avg_activity': 0,
            'avg_engagement': 0,
            'top_province': '无数据',
            'date_range': '无数据'
        }
    
    # 基础指标
    metrics['total_users'] = len(df['用户ID'].unique()) if '用户ID' in df.columns else 0
    metrics['total_posts'] = len(df)
    
    # 活跃度指标
    if '微博数' in df.columns:
        weibo_data = df['微博数'].replace([np.inf, -np.inf], np.nan).dropna()
        metrics['avg_posts_per_user'] = weibo_data.mean() if len(weibo_data) > 0 else 0
    
    if '粉丝数' in df.columns:
        fans_data = df['粉丝数'].replace([np.inf, -np.inf], np.nan).dropna()
        if len(fans_data) > 0:
            metrics['avg_followers'] = fans_data.mean()
            metrics['max_followers'] = fans_data.max()
        else:
            metrics['avg_followers'] = 0
            metrics['max_followers'] = 0
    
    # 参与度指标
    engagement_cols = ['转发数', '评论数', '点赞数']
    for col in engagement_cols:
        if col in df.columns:
            col_data = df[col].replace([np.inf, -np.inf], np.nan).dropna()
            if len(col_data) > 0:
                metrics[f'total_{col}'] = col_data.sum()
                metrics[f'avg_{col}'] = col_data.mean()
            else:
                metrics[f'total_{col}'] = 0
                metrics[f'avg_{col}'] = 0
    
    # 地理分布
    if '注册省份' in df.columns:
        province_data = df['注册省份'].dropna()
        metrics['provinces_count'] = province_data.nunique() if len(province_data) > 0 else 0
    
    # 时间范围
    if '发布时间' in df.columns:
        try:
            df_time = df.copy()
            df_time['发布时间'] = pd.to_datetime(df_time['发布时间'], errors='coerce')
            time_data = df_time['发布时间'].dropna()
            if len(time_data) > 1:
                metrics['time_range_days'] = (time_data.max() - time_data.min()).days
            else:
                metrics['time_range_days'] = 0
        except Exception:
            metrics['time_range_days'] = 0
    
    return metrics


def display_metrics_cards(metrics: Dict[str, Any]):
    """显示指标卡片"""
    # 创建指标卡片布局
    cols = st.columns(4)
    
    metric_configs = [
        ('total_users', '总用户数', '👥'),
        ('total_posts', '总发布数', '📝'),
        ('avg_followers', '平均粉丝数', '👥'),
        ('provinces_count', '覆盖省份', '🗺️')
    ]
    
    for i, (key, label, icon) in enumerate(metric_configs):
        if key in metrics:
            with cols[i % 4]:
                value = metrics[key]
                if isinstance(value, float):
                    value = f"{value:.1f}"
                st.metric(
                    label=f"{icon} {label}",
                    value=value
                )


if __name__ == "__main__":
    # 测试代码
    print("可视化工具模块已创建")
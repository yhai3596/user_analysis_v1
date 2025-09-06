import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from utils.visualizer import UserBehaviorVisualizer, create_dashboard_metrics, display_metrics_cards
from utils.cache_manager import cache_data
from config.settings import get_config

# 页面配置
st.set_page_config(
    page_title="用户画像分析",
    page_icon="👥",
    layout="wide"
)

class UserProfileAnalyzer:
    """用户画像分析器"""
    
    def __init__(self):
        self.visualizer = UserBehaviorVisualizer()
        self.viz_config = get_config('viz')
    
    @cache_data(ttl=1800)
    def analyze_basic_attributes(self, df: pd.DataFrame) -> dict:
        """分析基础属性"""
        analysis = {}
        
        # 性别分布
        if '性别' in df.columns:
            gender_dist = df['性别'].value_counts()
            analysis['gender_distribution'] = gender_dist.to_dict()
        
        # 地域分布
        if '注册省份' in df.columns:
            province_dist = df['注册省份'].value_counts().head(10)
            analysis['province_distribution'] = province_dist.to_dict()
        
        if '注册城市' in df.columns:
            city_dist = df['注册城市'].value_counts().head(10)
            analysis['city_distribution'] = city_dist.to_dict()
        
        # 用户规模统计
        analysis['total_users'] = len(df['用户ID'].unique()) if '用户ID' in df.columns else len(df)
        
        return analysis
    
    @cache_data(ttl=1800)
    def analyze_activity_levels(self, df: pd.DataFrame) -> dict:
        """分析活跃度水平"""
        analysis = {}
        
        activity_metrics = ['微博数', '关注数', '粉丝数']
        available_metrics = [m for m in activity_metrics if m in df.columns]
        
        for metric in available_metrics:
            data = df[metric].dropna()
            analysis[metric] = {
                'mean': data.mean(),
                'median': data.median(),
                'std': data.std(),
                'min': data.min(),
                'max': data.max(),
                'q25': data.quantile(0.25),
                'q75': data.quantile(0.75)
            }
        
        # 活跃度分级
        if '微博数' in df.columns:
            weibo_counts = df['微博数'].dropna()
            analysis['activity_levels'] = {
                '低活跃(0-100)': (weibo_counts <= 100).sum(),
                '中活跃(101-1000)': ((weibo_counts > 100) & (weibo_counts <= 1000)).sum(),
                '高活跃(1001-5000)': ((weibo_counts > 1000) & (weibo_counts <= 5000)).sum(),
                '超高活跃(5000+)': (weibo_counts > 5000).sum()
            }
        
        return analysis
    
    @cache_data(ttl=1800)
    def analyze_influence_metrics(self, df: pd.DataFrame) -> dict:
        """分析影响力指标"""
        analysis = {}
        
        # 粉丝影响力分析
        if '粉丝数' in df.columns:
            followers = df['粉丝数'].dropna()
            analysis['influence_levels'] = {
                '微影响力(0-100)': (followers <= 100).sum(),
                '小影响力(101-1000)': ((followers > 100) & (followers <= 1000)).sum(),
                '中影响力(1001-10000)': ((followers > 1000) & (followers <= 10000)).sum(),
                '大影响力(10000+)': (followers > 10000).sum()
            }
        
        # 互动影响力分析
        interaction_metrics = ['转发数', '评论数', '点赞数']
        available_interactions = [m for m in interaction_metrics if m in df.columns]
        
        if available_interactions:
            # 计算总互动数
            df_temp = df.copy()
            interaction_cols = [col for col in available_interactions if col in df_temp.columns]
            df_temp['total_interactions'] = df_temp[interaction_cols].sum(axis=1)
            
            total_interactions = df_temp['total_interactions']
            analysis['interaction_influence'] = {
                'mean_interactions': total_interactions.mean(),
                'top_10_percent_threshold': total_interactions.quantile(0.9),
                'top_1_percent_threshold': total_interactions.quantile(0.99)
            }
        
        # 影响力综合评分
        if '粉丝数' in df.columns and '微博数' in df.columns:
            df_temp = df.copy()
            # 简单的影响力评分算法
            df_temp['influence_score'] = (
                np.log1p(df_temp['粉丝数']) * 0.4 +
                np.log1p(df_temp['微博数']) * 0.3 +
                np.log1p(df_temp.get('转发数', 0)) * 0.3
            )
            
            analysis['influence_score_stats'] = {
                'mean': df_temp['influence_score'].mean(),
                'std': df_temp['influence_score'].std(),
                'top_10_percent': df_temp['influence_score'].quantile(0.9)
            }
        
        return analysis
    
    @cache_data(ttl=1800)
    def create_user_segments(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建用户细分"""
        df_segment = df.copy()
        
        # 基于活跃度和影响力的用户分群
        if '微博数' in df.columns and '粉丝数' in df.columns:
            # 活跃度分级
            df_segment['activity_level'] = pd.cut(
                df_segment['微博数'],
                bins=[0, 100, 1000, 5000, float('inf')],
                labels=['低活跃', '中活跃', '高活跃', '超高活跃']
            )
            
            # 影响力分级
            df_segment['influence_level'] = pd.cut(
                df_segment['粉丝数'],
                bins=[0, 100, 1000, 10000, float('inf')],
                labels=['微影响力', '小影响力', '中影响力', '大影响力']
            )
            
            # 用户类型组合
            df_segment['user_type'] = (
                df_segment['activity_level'].astype(str) + ' + ' +
                df_segment['influence_level'].astype(str)
            )
        
        return df_segment

def main():
    """主函数"""
    st.title("👥 用户画像分析")
    
    # 检查数据是否已加载
    if 'data_loaded' not in st.session_state or not st.session_state.data_loaded:
        st.warning("⚠️ 请先在主页加载数据")
        st.stop()
    
    # 获取数据
    df = st.session_state.get('filtered_data', st.session_state.current_data)
    
    # 确保数据不为None
    if df is None:
        st.error("❌ 数据获取失败，请返回主页重新加载数据")
        st.stop()
    
    analyzer = UserProfileAnalyzer()
    
    # 侧边栏控制
    st.sidebar.subheader("📊 分析选项")
    
    analysis_type = st.sidebar.selectbox(
        "选择分析类型",
        ["基础属性分析", "活跃度分析", "影响力分析", "用户细分", "综合画像"]
    )
    
    # 数据概览
    st.subheader("📈 数据概览")
    metrics = create_dashboard_metrics(df)
    display_metrics_cards(metrics)
    
    # 根据选择的分析类型显示内容
    if analysis_type == "基础属性分析":
        show_basic_attributes_analysis(df, analyzer)
    elif analysis_type == "活跃度分析":
        show_activity_analysis(df, analyzer)
    elif analysis_type == "影响力分析":
        show_influence_analysis(df, analyzer)
    elif analysis_type == "用户细分":
        show_user_segmentation(df, analyzer)
    elif analysis_type == "综合画像":
        show_comprehensive_profile(df, analyzer)

def show_basic_attributes_analysis(df: pd.DataFrame, analyzer: UserProfileAnalyzer):
    """显示基础属性分析"""
    st.subheader("👤 基础属性分析")
    
    # 分析基础属性
    basic_analysis = analyzer.analyze_basic_attributes(df)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 性别分布
        if 'gender_distribution' in basic_analysis:
            st.write("**性别分布**")
            fig_gender = analyzer.visualizer.plot_user_distribution(df, '性别', 'pie')
            st.plotly_chart(fig_gender, use_container_width=True)
    
    with col2:
        # 地域分布
        if 'province_distribution' in basic_analysis:
            st.write("**省份分布 (Top 10)**")
            fig_province = analyzer.visualizer.plot_user_distribution(df, '注册省份', 'bar')
            st.plotly_chart(fig_province, use_container_width=True)
    
    # 详细统计表
    st.subheader("📊 详细统计")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'gender_distribution' in basic_analysis:
            st.write("**性别统计**")
            gender_df = pd.DataFrame(list(basic_analysis['gender_distribution'].items()),
                                   columns=['性别', '用户数'])
            gender_df['占比'] = (gender_df['用户数'] / gender_df['用户数'].sum() * 100).round(2)
            st.dataframe(gender_df, use_container_width=True)
    
    with col2:
        if 'province_distribution' in basic_analysis:
            st.write("**省份统计 (Top 5)**")
            province_df = pd.DataFrame(list(basic_analysis['province_distribution'].items())[:5],
                                     columns=['省份', '用户数'])
            province_df['占比'] = (province_df['用户数'] / df.shape[0] * 100).round(2)
            st.dataframe(province_df, use_container_width=True)
    
    with col3:
        if 'city_distribution' in basic_analysis:
            st.write("**城市统计 (Top 5)**")
            city_df = pd.DataFrame(list(basic_analysis['city_distribution'].items())[:5],
                                 columns=['城市', '用户数'])
            city_df['占比'] = (city_df['用户数'] / df.shape[0] * 100).round(2)
            st.dataframe(city_df, use_container_width=True)

def show_activity_analysis(df: pd.DataFrame, analyzer: UserProfileAnalyzer):
    """显示活跃度分析"""
    st.subheader("⚡ 活跃度分析")
    
    # 分析活跃度
    activity_analysis = analyzer.analyze_activity_levels(df)
    
    # 活跃度指标分布图
    st.write("**活跃度指标分布**")
    fig_activity = analyzer.visualizer.plot_activity_metrics(df)
    st.plotly_chart(fig_activity, use_container_width=True)
    
    # 活跃度分级
    if 'activity_levels' in activity_analysis:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**活跃度分级**")
            activity_levels = activity_analysis['activity_levels']
            fig_levels = go.Figure(data=[
                go.Bar(
                    x=list(activity_levels.keys()),
                    y=list(activity_levels.values()),
                    marker_color=analyzer.visualizer.color_palette[:len(activity_levels)]
                )
            ])
            fig_levels.update_layout(
                title="用户活跃度分级分布",
                xaxis_title="活跃度等级",
                yaxis_title="用户数量"
            )
            st.plotly_chart(fig_levels, use_container_width=True)
        
        with col2:
            st.write("**活跃度统计表**")
            levels_df = pd.DataFrame(list(activity_levels.items()),
                                   columns=['活跃度等级', '用户数'])
            levels_df['占比(%)'] = (levels_df['用户数'] / levels_df['用户数'].sum() * 100).round(2)
            st.dataframe(levels_df, use_container_width=True)
    
    # 活跃度指标统计
    st.subheader("📈 活跃度指标统计")
    
    activity_metrics = ['微博数', '关注数', '粉丝数']
    available_metrics = [m for m in activity_metrics if m in activity_analysis]
    
    if available_metrics:
        stats_data = []
        for metric in available_metrics:
            stats = activity_analysis[metric]
            stats_data.append({
                '指标': metric,
                '平均值': f"{stats['mean']:.1f}",
                '中位数': f"{stats['median']:.1f}",
                '标准差': f"{stats['std']:.1f}",
                '最小值': f"{stats['min']:.0f}",
                '最大值': f"{stats['max']:.0f}",
                '25%分位': f"{stats['q25']:.1f}",
                '75%分位': f"{stats['q75']:.1f}"
            })
        
        stats_df = pd.DataFrame(stats_data)
        st.dataframe(stats_df, use_container_width=True)

def show_influence_analysis(df: pd.DataFrame, analyzer: UserProfileAnalyzer):
    """显示影响力分析"""
    st.subheader("🌟 影响力分析")
    
    # 分析影响力
    influence_analysis = analyzer.analyze_influence_metrics(df)
    
    # 影响力散点图
    if '粉丝数' in df.columns and '微博数' in df.columns:
        st.write("**用户影响力散点图**")
        fig_influence = analyzer.visualizer.plot_user_influence_scatter(df)
        st.plotly_chart(fig_influence, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 影响力分级
        if 'influence_levels' in influence_analysis:
            st.write("**影响力分级分布**")
            influence_levels = influence_analysis['influence_levels']
            fig_influence_levels = go.Figure(data=[
                go.Pie(
                    labels=list(influence_levels.keys()),
                    values=list(influence_levels.values()),
                    hole=0.3
                )
            ])
            fig_influence_levels.update_layout(title="用户影响力分级")
            st.plotly_chart(fig_influence_levels, use_container_width=True)
    
    with col2:
        # 互动影响力
        if 'interaction_influence' in influence_analysis:
            st.write("**互动影响力指标**")
            interaction_stats = influence_analysis['interaction_influence']
            
            metrics_data = [
                ["平均互动数", f"{interaction_stats['mean_interactions']:.1f}"],
                ["Top 10%阈值", f"{interaction_stats['top_10_percent_threshold']:.1f}"],
                ["Top 1%阈值", f"{interaction_stats['top_1_percent_threshold']:.1f}"]
            ]
            
            interaction_df = pd.DataFrame(metrics_data, columns=['指标', '数值'])
            st.dataframe(interaction_df, use_container_width=True)
    
    # 影响力综合评分
    if 'influence_score_stats' in influence_analysis:
        st.subheader("🏆 影响力综合评分")
        score_stats = influence_analysis['influence_score_stats']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("平均评分", f"{score_stats['mean']:.2f}")
        with col2:
            st.metric("标准差", f"{score_stats['std']:.2f}")
        with col3:
            st.metric("Top 10%阈值", f"{score_stats['top_10_percent']:.2f}")

def show_user_segmentation(df: pd.DataFrame, analyzer: UserProfileAnalyzer):
    """显示用户细分"""
    st.subheader("🎯 用户细分")
    
    # 创建用户细分
    df_segment = analyzer.create_user_segments(df)
    
    if 'user_type' in df_segment.columns:
        # 用户类型分布
        st.write("**用户类型分布**")
        user_type_dist = df_segment['user_type'].value_counts().head(10)
        
        fig_segments = go.Figure(data=[
            go.Bar(
                x=user_type_dist.values,
                y=user_type_dist.index,
                orientation='h',
                marker_color=analyzer.visualizer.color_palette[:len(user_type_dist)]
            )
        ])
        fig_segments.update_layout(
            title="用户类型分布 (Top 10)",
            xaxis_title="用户数量",
            yaxis_title="用户类型",
            height=500
        )
        st.plotly_chart(fig_segments, use_container_width=True)
        
        # 细分统计表
        st.write("**用户细分统计**")
        segment_stats = df_segment['user_type'].value_counts().reset_index()
        segment_stats.columns = ['用户类型', '用户数量']
        segment_stats['占比(%)'] = (segment_stats['用户数量'] / segment_stats['用户数量'].sum() * 100).round(2)
        st.dataframe(segment_stats, use_container_width=True)
    
    # 二维细分矩阵
    if 'activity_level' in df_segment.columns and 'influence_level' in df_segment.columns:
        st.subheader("📊 用户细分矩阵")
        
        # 创建交叉表
        cross_tab = pd.crosstab(df_segment['activity_level'], df_segment['influence_level'])
        
        # 热力图
        fig_matrix = go.Figure(data=go.Heatmap(
            z=cross_tab.values,
            x=cross_tab.columns,
            y=cross_tab.index,
            colorscale='Blues',
            text=cross_tab.values,
            texttemplate="%{text}",
            textfont={"size": 12}
        ))
        
        fig_matrix.update_layout(
            title="活跃度 × 影响力 用户分布矩阵",
            xaxis_title="影响力等级",
            yaxis_title="活跃度等级"
        )
        st.plotly_chart(fig_matrix, use_container_width=True)

def show_comprehensive_profile(df: pd.DataFrame, analyzer: UserProfileAnalyzer):
    """显示综合画像"""
    st.subheader("🎨 综合用户画像")
    
    # 获取所有分析结果
    basic_analysis = analyzer.analyze_basic_attributes(df)
    activity_analysis = analyzer.analyze_activity_levels(df)
    influence_analysis = analyzer.analyze_influence_metrics(df)
    
    # 关键洞察
    st.subheader("💡 关键洞察")
    
    insights = []
    
    # 基础属性洞察
    if 'gender_distribution' in basic_analysis:
        gender_dist = basic_analysis['gender_distribution']
        dominant_gender = max(gender_dist, key=gender_dist.get)
        gender_ratio = gender_dist[dominant_gender] / sum(gender_dist.values()) * 100
        insights.append(f"👥 用户群体以{dominant_gender}性为主，占比{gender_ratio:.1f}%")
    
    # 活跃度洞察
    if 'activity_levels' in activity_analysis:
        activity_levels = activity_analysis['activity_levels']
        most_active_level = max(activity_levels, key=activity_levels.get)
        insights.append(f"⚡ 大部分用户属于{most_active_level}用户")
    
    # 影响力洞察
    if 'influence_levels' in influence_analysis:
        influence_levels = influence_analysis['influence_levels']
        most_influence_level = max(influence_levels, key=influence_levels.get)
        insights.append(f"🌟 用户影响力主要集中在{most_influence_level}层级")
    
    # 地域洞察
    if 'province_distribution' in basic_analysis:
        top_province = list(basic_analysis['province_distribution'].keys())[0]
        insights.append(f"🗺️ 用户主要集中在{top_province}地区")
    
    for insight in insights:
        st.info(insight)
    
    # 综合指标仪表板
    st.subheader("📊 综合指标仪表板")
    
    # 创建综合指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_users = basic_analysis.get('total_users', 0)
        st.metric("总用户数", f"{total_users:,}")
    
    with col2:
        if '微博数' in activity_analysis:
            avg_posts = activity_analysis['微博数']['mean']
            st.metric("平均微博数", f"{avg_posts:.0f}")
    
    with col3:
        if '粉丝数' in activity_analysis:
            avg_followers = activity_analysis['粉丝数']['mean']
            st.metric("平均粉丝数", f"{avg_followers:.0f}")
    
    with col4:
        if 'province_distribution' in basic_analysis:
            provinces_count = len(basic_analysis['province_distribution'])
            st.metric("覆盖省份", f"{provinces_count}")
    
    # 用户画像总结
    st.subheader("📋 用户画像总结")
    
    summary_text = f"""
    **用户群体特征总结：**
    
    📊 **规模特征**：共有 {basic_analysis.get('total_users', 0):,} 名用户
    
    👥 **人群特征**：{list(basic_analysis.get('gender_distribution', {}).keys())[0] if basic_analysis.get('gender_distribution') else '未知'}性用户占主导地位
    
    🗺️ **地域特征**：主要分布在{list(basic_analysis.get('province_distribution', {}).keys())[0] if basic_analysis.get('province_distribution') else '未知'}等地区
    
    ⚡ **活跃特征**：平均发布{activity_analysis.get('微博数', {}).get('mean', 0):.0f}条微博
    
    🌟 **影响特征**：平均拥有{activity_analysis.get('粉丝数', {}).get('mean', 0):.0f}名粉丝
    
    **建议策略：**
    - 针对主要用户群体制定个性化内容策略
    - 重点关注高活跃度和高影响力用户
    - 加强地域化运营，深耕重点区域
    - 提升用户参与度和互动质量
    """
    
    st.markdown(summary_text)

if __name__ == "__main__":
    main()
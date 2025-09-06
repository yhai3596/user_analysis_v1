import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from utils.visualizer import UserBehaviorVisualizer, create_dashboard_metrics, display_metrics_cards
from utils.cache_manager import cache_data
from config.settings import get_config

# 页面配置
st.set_page_config(
    page_title="地理行为分析",
    page_icon="🗺️",
    layout="wide"
)

class GeoAnalyzer:
    """地理行为分析器"""
    
    def __init__(self):
        self.visualizer = UserBehaviorVisualizer()
        self.viz_config = get_config('viz')
        
        # 中国主要城市坐标（示例数据）
        self.city_coordinates = {
            '北京': [39.9042, 116.4074],
            '上海': [31.2304, 121.4737],
            '广州': [23.1291, 113.2644],
            '深圳': [22.5431, 114.0579],
            '杭州': [30.2741, 120.1551],
            '南京': [32.0603, 118.7969],
            '武汉': [30.5928, 114.3055],
            '成都': [30.5728, 104.0668],
            '西安': [34.3416, 108.9398],
            '重庆': [29.5630, 106.5516],
            '天津': [39.3434, 117.3616],
            '苏州': [31.2989, 120.5853],
            '青岛': [36.0986, 120.3719],
            '长沙': [28.2282, 112.9388],
            '大连': [38.9140, 121.6147],
            '厦门': [24.4798, 118.0894],
            '无锡': [31.4912, 120.3124],
            '福州': [26.0745, 119.2965],
            '济南': [36.6512, 117.1201],
            '宁波': [29.8683, 121.5440]
        }
    
    @cache_data(ttl=1800)
    def analyze_geographic_distribution(self, df: pd.DataFrame) -> dict:
        """分析地理分布"""
        analysis = {}
        
        # 省份分布
        if '注册省份' in df.columns:
            province_dist = df['注册省份'].value_counts()
            analysis['province_distribution'] = province_dist.to_dict()
            analysis['province_stats'] = {
                'total_provinces': len(province_dist),
                'top_province': province_dist.index[0],
                'top_province_ratio': province_dist.iloc[0] / len(df) * 100
            }
        
        # 城市分布
        if '注册城市' in df.columns:
            city_dist = df['注册城市'].value_counts()
            analysis['city_distribution'] = city_dist.to_dict()
            analysis['city_stats'] = {
                'total_cities': len(city_dist),
                'top_city': city_dist.index[0],
                'top_city_ratio': city_dist.iloc[0] / len(df) * 100
            }
        
        # 地理集中度分析
        if '注册省份' in df.columns:
            # 计算基尼系数（地理集中度）
            province_counts = df['注册省份'].value_counts().values
            province_counts_sorted = np.sort(province_counts)
            n = len(province_counts_sorted)
            cumsum = np.cumsum(province_counts_sorted)
            gini = (2 * np.sum((np.arange(1, n + 1) * province_counts_sorted))) / (n * np.sum(province_counts_sorted)) - (n + 1) / n
            analysis['geographic_concentration'] = {
                'gini_coefficient': gini,
                'concentration_level': 'high' if gini > 0.6 else 'medium' if gini > 0.4 else 'low'
            }
        
        return analysis
    
    @cache_data(ttl=1800)
    def analyze_regional_behavior(self, df: pd.DataFrame) -> dict:
        """分析区域行为差异"""
        analysis = {}
        
        if '注册省份' in df.columns:
            # 按省份分组分析行为指标
            behavior_metrics = ['微博数', '关注数', '粉丝数']
            available_metrics = [m for m in behavior_metrics if m in df.columns]
            
            if available_metrics:
                province_behavior = df.groupby('注册省份')[available_metrics].agg({
                    metric: ['mean', 'median', 'std', 'count'] for metric in available_metrics
                }).round(2)
                
                analysis['province_behavior'] = province_behavior.to_dict()
                
                # 找出最活跃的省份
                if '微博数' in available_metrics:
                    most_active_province = df.groupby('注册省份')['微博数'].mean().idxmax()
                    analysis['most_active_province'] = most_active_province
                
                # 找出影响力最大的省份
                if '粉丝数' in available_metrics:
                    most_influential_province = df.groupby('注册省份')['粉丝数'].mean().idxmax()
                    analysis['most_influential_province'] = most_influential_province
        
        return analysis
    
    @cache_data(ttl=1800)
    def create_geographic_heatmap_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建地理热力图数据"""
        if '注册城市' not in df.columns:
            return pd.DataFrame()
        
        # 统计城市用户数
        city_counts = df['注册城市'].value_counts().reset_index()
        city_counts.columns = ['city', 'user_count']
        
        # 添加坐标信息
        city_counts['lat'] = city_counts['city'].map(lambda x: self.city_coordinates.get(x, [None, None])[0])
        city_counts['lon'] = city_counts['city'].map(lambda x: self.city_coordinates.get(x, [None, None])[1])
        
        # 过滤掉没有坐标的城市
        city_counts = city_counts.dropna(subset=['lat', 'lon'])
        
        return city_counts
    
    def create_folium_map(self, heatmap_data: pd.DataFrame) -> folium.Map:
        """创建Folium地图"""
        # 创建以中国为中心的地图
        m = folium.Map(
            location=[35.0, 105.0],  # 中国中心坐标
            zoom_start=5,
            tiles='OpenStreetMap'
        )
        
        if not heatmap_data.empty:
            # 添加热力图层
            from folium.plugins import HeatMap
            
            heat_data = [[row['lat'], row['lon'], row['user_count']] 
                        for idx, row in heatmap_data.iterrows()]
            
            HeatMap(heat_data, radius=15, blur=10, gradient={
                0.2: 'blue', 0.4: 'lime', 0.6: 'orange', 1: 'red'
            }).add_to(m)
            
            # 添加城市标记
            for idx, row in heatmap_data.head(10).iterrows():  # 只显示前10个城市
                folium.CircleMarker(
                    location=[row['lat'], row['lon']],
                    radius=min(row['user_count'] / 10, 20),  # 根据用户数调整大小
                    popup=f"{row['city']}: {row['user_count']}人",
                    color='red',
                    fill=True,
                    fillColor='red',
                    fillOpacity=0.6
                ).add_to(m)
        
        return m

def main():
    """主函数"""
    st.title("🗺️ 地理行为分析")
    
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
    
    analyzer = GeoAnalyzer()
    
    # 侧边栏控制
    st.sidebar.subheader("🗺️ 分析选项")
    
    analysis_type = st.sidebar.selectbox(
        "选择分析类型",
        ["地理分布概览", "区域行为差异", "地理热力图", "城市排行榜", "地理洞察报告"]
    )
    
    # 数据概览
    st.subheader("📈 数据概览")
    metrics = create_dashboard_metrics(df)
    display_metrics_cards(metrics)
    
    # 根据选择的分析类型显示内容
    if analysis_type == "地理分布概览":
        show_geographic_overview(df, analyzer)
    elif analysis_type == "区域行为差异":
        show_regional_behavior(df, analyzer)
    elif analysis_type == "地理热力图":
        show_geographic_heatmap(df, analyzer)
    elif analysis_type == "城市排行榜":
        show_city_rankings(df, analyzer)
    elif analysis_type == "地理洞察报告":
        show_geographic_insights(df, analyzer)

def show_geographic_overview(df: pd.DataFrame, analyzer: GeoAnalyzer):
    """显示地理分布概览"""
    st.subheader("🌍 地理分布概览")
    
    # 分析地理分布
    geo_analysis = analyzer.analyze_geographic_distribution(df)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 省份分布
        if 'province_distribution' in geo_analysis:
            st.write("**省份分布 (Top 10)**")
            province_data = dict(list(geo_analysis['province_distribution'].items())[:10])
            fig_province = go.Figure(data=[
                go.Bar(
                    x=list(province_data.values()),
                    y=list(province_data.keys()),
                    orientation='h',
                    marker_color=analyzer.visualizer.color_palette[:len(province_data)]
                )
            ])
            fig_province.update_layout(
                title="用户省份分布",
                xaxis_title="用户数量",
                yaxis_title="省份",
                height=400
            )
            st.plotly_chart(fig_province, use_container_width=True)
    
    with col2:
        # 城市分布
        if 'city_distribution' in geo_analysis:
            st.write("**城市分布 (Top 10)**")
            city_data = dict(list(geo_analysis['city_distribution'].items())[:10])
            fig_city = go.Figure(data=[
                go.Pie(
                    labels=list(city_data.keys()),
                    values=list(city_data.values()),
                    hole=0.3
                )
            ])
            fig_city.update_layout(title="用户城市分布")
            st.plotly_chart(fig_city, use_container_width=True)
    
    # 地理集中度分析
    if 'geographic_concentration' in geo_analysis:
        st.subheader("📊 地理集中度分析")
        
        concentration = geo_analysis['geographic_concentration']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("基尼系数", f"{concentration['gini_coefficient']:.3f}")
        with col2:
            st.metric("集中度水平", concentration['concentration_level'].upper())
        with col3:
            if 'province_stats' in geo_analysis:
                st.metric("覆盖省份数", geo_analysis['province_stats']['total_provinces'])
        
        # 集中度解释
        concentration_level = concentration['concentration_level']
        if concentration_level == 'high':
            st.info("🎯 用户地理分布高度集中，主要集中在少数几个省份")
        elif concentration_level == 'medium':
            st.info("📍 用户地理分布中等集中，分布相对均匀")
        else:
            st.info("🌐 用户地理分布较为分散，覆盖面广")
    
    # 详细统计表
    st.subheader("📋 详细统计表")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'province_distribution' in geo_analysis:
            st.write("**省份统计 (Top 10)**")
            province_items = list(geo_analysis['province_distribution'].items())[:10]
            province_df = pd.DataFrame(province_items, columns=['省份', '用户数'])
            province_df['占比(%)'] = (province_df['用户数'] / df.shape[0] * 100).round(2)
            st.dataframe(province_df, use_container_width=True)
    
    with col2:
        if 'city_distribution' in geo_analysis:
            st.write("**城市统计 (Top 10)**")
            city_items = list(geo_analysis['city_distribution'].items())[:10]
            city_df = pd.DataFrame(city_items, columns=['城市', '用户数'])
            city_df['占比(%)'] = (city_df['用户数'] / df.shape[0] * 100).round(2)
            st.dataframe(city_df, use_container_width=True)

def show_regional_behavior(df: pd.DataFrame, analyzer: GeoAnalyzer):
    """显示区域行为差异"""
    st.subheader("🏙️ 区域行为差异分析")
    
    # 分析区域行为
    behavior_analysis = analyzer.analyze_regional_behavior(df)
    
    if '注册省份' not in df.columns:
        st.warning("数据中缺少省份信息，无法进行区域行为分析")
        return
    
    # 选择分析指标
    available_metrics = [col for col in ['微博数', '关注数', '粉丝数'] if col in df.columns]
    
    if not available_metrics:
        st.warning("数据中缺少行为指标，无法进行分析")
        return
    
    selected_metric = st.selectbox("选择分析指标", available_metrics)
    
    # 按省份统计选定指标
    province_stats = df.groupby('注册省份')[selected_metric].agg([
        'count', 'mean', 'median', 'std'
    ]).round(2).reset_index()
    province_stats.columns = ['省份', '用户数', '平均值', '中位数', '标准差']
    province_stats = province_stats.sort_values('平均值', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 省份行为指标排行
        st.write(f"**{selected_metric} - 省份排行 (Top 10)**")
        top_provinces = province_stats.head(10)
        
        fig_ranking = go.Figure(data=[
            go.Bar(
                x=top_provinces['平均值'],
                y=top_provinces['省份'],
                orientation='h',
                marker_color=analyzer.visualizer.color_palette[:len(top_provinces)],
                text=top_provinces['平均值'].round(1),
                textposition='auto'
            )
        ])
        fig_ranking.update_layout(
            title=f"{selected_metric}省份平均值排行",
            xaxis_title=f"平均{selected_metric}",
            yaxis_title="省份",
            height=400
        )
        st.plotly_chart(fig_ranking, use_container_width=True)
    
    with col2:
        # 省份行为分布箱线图
        st.write(f"**{selected_metric} - 分布箱线图**")
        
        # 选择用户数较多的省份进行箱线图分析
        top_provinces_for_box = province_stats.head(8)['省份'].tolist()
        df_filtered = df[df['注册省份'].isin(top_provinces_for_box)]
        
        fig_box = go.Figure()
        
        for province in top_provinces_for_box:
            province_data = df_filtered[df_filtered['注册省份'] == province][selected_metric]
            fig_box.add_trace(go.Box(
                y=province_data,
                name=province,
                boxpoints='outliers'
            ))
        
        fig_box.update_layout(
            title=f"{selected_metric}省份分布对比",
            yaxis_title=selected_metric,
            xaxis_title="省份",
            height=400
        )
        st.plotly_chart(fig_box, use_container_width=True)
    
    # 详细统计表
    st.subheader("📊 省份行为统计表")
    st.dataframe(province_stats, use_container_width=True)
    
    # 行为差异洞察
    if len(province_stats) > 1:
        st.subheader("💡 区域行为洞察")
        
        max_province = province_stats.iloc[0]
        min_province = province_stats.iloc[-1]
        
        insights = [
            f"🏆 {selected_metric}最高的省份是{max_province['省份']}，平均值为{max_province['平均值']:.1f}",
            f"📉 {selected_metric}最低的省份是{min_province['省份']}，平均值为{min_province['平均值']:.1f}",
            f"📈 最高与最低省份的差异倍数为{max_province['平均值'] / max_province['平均值'] if min_province['平均值'] > 0 else 'N/A':.1f}倍"
        ]
        
        for insight in insights:
            st.info(insight)

def show_geographic_heatmap(df: pd.DataFrame, analyzer: GeoAnalyzer):
    """显示地理热力图"""
    st.subheader("🔥 地理热力图")
    
    # 创建热力图数据
    heatmap_data = analyzer.create_geographic_heatmap_data(df)
    
    if heatmap_data.empty:
        st.warning("数据中缺少城市坐标信息，无法生成热力图")
        st.info("💡 提示：当前支持的城市包括：" + "、".join(list(analyzer.city_coordinates.keys())[:10]) + "等")
        return
    
    # 显示热力图
    st.write("**用户分布热力图**")
    
    # 创建Folium地图
    folium_map = analyzer.create_folium_map(heatmap_data)
    
    # 在Streamlit中显示地图
    map_data = st_folium(folium_map, width=700, height=500)
    
    # 热力图数据统计
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 热力图统计")
        st.metric("覆盖城市数", len(heatmap_data))
        st.metric("总用户数", heatmap_data['user_count'].sum())
        st.metric("平均每城市用户数", f"{heatmap_data['user_count'].mean():.1f}")
    
    with col2:
        st.subheader("🏙️ Top 5 城市")
        top_cities = heatmap_data.head(5)
        for idx, row in top_cities.iterrows():
            st.write(f"**{row['city']}**: {row['user_count']}人")
    
    # 详细城市数据表
    st.subheader("📋 城市用户分布详情")
    heatmap_display = heatmap_data.copy()
    heatmap_display['占比(%)'] = (heatmap_display['user_count'] / heatmap_display['user_count'].sum() * 100).round(2)
    heatmap_display = heatmap_display[['city', 'user_count', '占比(%)']]
    heatmap_display.columns = ['城市', '用户数', '占比(%)']
    st.dataframe(heatmap_display, use_container_width=True)

def show_city_rankings(df: pd.DataFrame, analyzer: GeoAnalyzer):
    """显示城市排行榜"""
    st.subheader("🏆 城市排行榜")
    
    if '注册城市' not in df.columns:
        st.warning("数据中缺少城市信息")
        return
    
    # 选择排行指标
    ranking_options = {
        '用户数量': 'count',
        '平均微博数': 'mean_posts',
        '平均粉丝数': 'mean_followers',
        '平均关注数': 'mean_following'
    }
    
    selected_ranking = st.selectbox("选择排行指标", list(ranking_options.keys()))
    
    # 计算城市统计数据
    city_stats = df.groupby('注册城市').agg({
        '用户ID': 'count',
        '微博数': 'mean' if '微博数' in df.columns else lambda x: 0,
        '粉丝数': 'mean' if '粉丝数' in df.columns else lambda x: 0,
        '关注数': 'mean' if '关注数' in df.columns else lambda x: 0
    }).round(2).reset_index()
    
    city_stats.columns = ['城市', '用户数量', '平均微博数', '平均粉丝数', '平均关注数']
    
    # 根据选择的指标排序
    sort_column = selected_ranking
    city_stats_sorted = city_stats.sort_values(sort_column, ascending=False)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 排行榜图表
        st.write(f"**{selected_ranking}排行榜 (Top 15)**")
        top_cities = city_stats_sorted.head(15)
        
        fig_ranking = go.Figure(data=[
            go.Bar(
                x=top_cities[sort_column],
                y=top_cities['城市'],
                orientation='h',
                marker_color=analyzer.visualizer.color_palette[:len(top_cities)],
                text=top_cities[sort_column].round(1),
                textposition='auto'
            )
        ])
        
        fig_ranking.update_layout(
            title=f"城市{selected_ranking}排行榜",
            xaxis_title=selected_ranking,
            yaxis_title="城市",
            height=600
        )
        st.plotly_chart(fig_ranking, use_container_width=True)
    
    with col2:
        # Top 10 排行榜
        st.write(f"**Top 10 {selected_ranking}**")
        top_10 = city_stats_sorted.head(10)
        
        for idx, (_, row) in enumerate(top_10.iterrows(), 1):
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
            st.write(f"{medal} **{row['城市']}**: {row[sort_column]:.1f}")
    
    # 完整排行榜表格
    st.subheader("📊 完整城市排行榜")
    
    # 添加排名列
    city_stats_sorted['排名'] = range(1, len(city_stats_sorted) + 1)
    city_stats_display = city_stats_sorted[['排名', '城市', '用户数量', '平均微博数', '平均粉丝数', '平均关注数']]
    
    st.dataframe(city_stats_display, use_container_width=True)
    
    # 排行榜洞察
    st.subheader("💡 排行榜洞察")
    
    top_city = city_stats_sorted.iloc[0]
    insights = [
        f"🏆 {selected_ranking}第一名：{top_city['城市']}，数值为{top_city[sort_column]:.1f}",
        f"📊 共有{len(city_stats_sorted)}个城市参与排名",
        f"📈 前三名城市占总用户数的{city_stats_sorted.head(3)['用户数量'].sum() / city_stats_sorted['用户数量'].sum() * 100:.1f}%"
    ]
    
    for insight in insights:
        st.info(insight)

def show_geographic_insights(df: pd.DataFrame, analyzer: GeoAnalyzer):
    """显示地理洞察报告"""
    st.subheader("📋 地理洞察报告")
    
    # 获取所有分析结果
    geo_analysis = analyzer.analyze_geographic_distribution(df)
    behavior_analysis = analyzer.analyze_regional_behavior(df)
    heatmap_data = analyzer.create_geographic_heatmap_data(df)
    
    # 关键指标概览
    st.subheader("📊 关键指标概览")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'province_stats' in geo_analysis:
            st.metric("覆盖省份", geo_analysis['province_stats']['total_provinces'])
    
    with col2:
        if 'city_stats' in geo_analysis:
            st.metric("覆盖城市", geo_analysis['city_stats']['total_cities'])
    
    with col3:
        if 'province_stats' in geo_analysis:
            st.metric("主要省份占比", f"{geo_analysis['province_stats']['top_province_ratio']:.1f}%")
    
    with col4:
        if not heatmap_data.empty:
            st.metric("热力图覆盖城市", len(heatmap_data))
    
    # 地理分布特征
    st.subheader("🗺️ 地理分布特征")
    
    distribution_insights = []
    
    if 'province_stats' in geo_analysis:
        top_province = geo_analysis['province_stats']['top_province']
        top_ratio = geo_analysis['province_stats']['top_province_ratio']
        distribution_insights.append(f"🎯 用户主要集中在{top_province}，占比{top_ratio:.1f}%")
    
    if 'geographic_concentration' in geo_analysis:
        concentration = geo_analysis['geographic_concentration']
        gini = concentration['gini_coefficient']
        level = concentration['concentration_level']
        distribution_insights.append(f"📈 地理集中度基尼系数为{gini:.3f}，属于{level}集中度")
    
    if 'city_stats' in geo_analysis:
        top_city = geo_analysis['city_stats']['top_city']
        city_ratio = geo_analysis['city_stats']['top_city_ratio']
        distribution_insights.append(f"🏙️ 用户最多的城市是{top_city}，占比{city_ratio:.1f}%")
    
    for insight in distribution_insights:
        st.info(insight)
    
    # 区域行为特征
    if behavior_analysis:
        st.subheader("🏃 区域行为特征")
        
        behavior_insights = []
        
        if 'most_active_province' in behavior_analysis:
            most_active = behavior_analysis['most_active_province']
            behavior_insights.append(f"⚡ 最活跃的省份：{most_active}（平均微博数最高）")
        
        if 'most_influential_province' in behavior_analysis:
            most_influential = behavior_analysis['most_influential_province']
            behavior_insights.append(f"🌟 最具影响力的省份：{most_influential}（平均粉丝数最高）")
        
        for insight in behavior_insights:
            st.success(insight)
    
    # 热力图分析
    if not heatmap_data.empty:
        st.subheader("🔥 热力图分析")
        
        top_3_cities = heatmap_data.head(3)
        heatmap_insights = [
            f"🏆 用户密度最高的三个城市：{', '.join(top_3_cities['city'].tolist())}",
            f"📊 热力图覆盖{len(heatmap_data)}个主要城市",
            f"🎯 前三名城市用户数占热力图总数的{top_3_cities['user_count'].sum() / heatmap_data['user_count'].sum() * 100:.1f}%"
        ]
        
        for insight in heatmap_insights:
            st.info(insight)
    
    # 综合建议
    st.subheader("💡 策略建议")
    
    recommendations = [
        "🎯 **重点区域策略**：针对用户集中的主要省份和城市制定专门的运营策略",
        "🌐 **区域扩张策略**：在用户较少但潜力较大的地区加强推广和运营",
        "📊 **差异化运营**：根据不同地区用户的行为特征制定个性化内容策略",
        "🔥 **热点城市深耕**：在用户密度高的城市加强本地化服务和活动",
        "📈 **数据驱动决策**：持续监控地理分布变化，及时调整区域策略"
    ]
    
    for recommendation in recommendations:
        st.markdown(recommendation)
    
    # 数据质量说明
    st.subheader("ℹ️ 数据说明")
    
    data_notes = [
        f"📅 数据时间范围：基于当前加载的{len(df)}条用户数据",
        "🗺️ 地理坐标：热力图基于预设的主要城市坐标，可能不包含所有城市",
        "📊 统计方法：采用描述性统计和基尼系数等方法分析地理集中度",
        "⚠️ 数据限制：分析结果基于样本数据，实际应用时需考虑数据完整性"
    ]
    
    for note in data_notes:
        st.caption(note)

if __name__ == "__main__":
    main()
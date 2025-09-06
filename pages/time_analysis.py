import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime as dt
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from utils.visualizer import UserBehaviorVisualizer, create_dashboard_metrics, display_metrics_cards
from utils.cache_manager import cache_data
from config.settings import get_config

# 页面配置
st.set_page_config(
    page_title="时间行为分析",
    page_icon="⏰",
    layout="wide"
)

class TimeAnalyzer:
    """时间行为分析器"""
    
    def __init__(self):
        self.visualizer = UserBehaviorVisualizer()
        self.viz_config = get_config('viz')
    
    @cache_data(ttl=1800)
    def analyze_posting_patterns(self, df: pd.DataFrame) -> dict:
        """分析发布时间模式"""
        analysis = {}
        
        if '发布时间' not in df.columns:
            return analysis
        
        # 确保发布时间是datetime类型
        df_temp = df.copy()
        df_temp['发布时间'] = pd.to_datetime(df_temp['发布时间'], errors='coerce')
        df_temp = df_temp.dropna(subset=['发布时间'])
        
        if df_temp.empty:
            return analysis
        
        # 提取时间特征
        df_temp['hour'] = df_temp['发布时间'].dt.hour
        df_temp['day_of_week'] = df_temp['发布时间'].dt.dayofweek  # 0=Monday
        df_temp['day_name'] = df_temp['发布时间'].dt.day_name()
        df_temp['month'] = df_temp['发布时间'].dt.month
        df_temp['date'] = df_temp['发布时间'].dt.date
        
        # 小时分布
        hourly_dist = df_temp['hour'].value_counts().sort_index()
        analysis['hourly_distribution'] = hourly_dist.to_dict()
        
        # 星期分布
        weekly_dist = df_temp['day_name'].value_counts()
        analysis['weekly_distribution'] = weekly_dist.to_dict()
        
        # 月份分布
        monthly_dist = df_temp['month'].value_counts().sort_index()
        analysis['monthly_distribution'] = monthly_dist.to_dict()
        
        # 日期分布（时间序列）
        daily_dist = df_temp['date'].value_counts().sort_index()
        analysis['daily_distribution'] = daily_dist.to_dict()
        
        # 活跃时段分析
        analysis['peak_hours'] = {
            'most_active_hour': hourly_dist.idxmax(),
            'least_active_hour': hourly_dist.idxmin(),
            'morning_posts': hourly_dist[6:12].sum(),  # 6-12点
            'afternoon_posts': hourly_dist[12:18].sum(),  # 12-18点
            'evening_posts': hourly_dist[18:24].sum(),  # 18-24点
            'night_posts': hourly_dist[0:6].sum()  # 0-6点
        }
        
        # 工作日vs周末
        df_temp['is_weekend'] = df_temp['day_of_week'].isin([5, 6])  # Saturday, Sunday
        weekend_analysis = df_temp.groupby('is_weekend').size()
        analysis['weekend_vs_weekday'] = {
            'weekday_posts': weekend_analysis.get(False, 0),
            'weekend_posts': weekend_analysis.get(True, 0)
        }
        
        return analysis
    
    @cache_data(ttl=1800)
    def analyze_user_activity_patterns(self, df: pd.DataFrame) -> dict:
        """分析用户活跃模式"""
        analysis = {}
        
        if '发布时间' not in df.columns or '用户ID' not in df.columns:
            return analysis
        
        # 确保发布时间是datetime类型
        df_temp = df.copy()
        df_temp['发布时间'] = pd.to_datetime(df_temp['发布时间'], errors='coerce')
        df_temp = df_temp.dropna(subset=['发布时间'])
        
        if df_temp.empty:
            return analysis
        
        # 用户活跃天数统计
        user_active_days = df_temp.groupby('用户ID')['发布时间'].apply(
            lambda x: x.dt.date.nunique()
        )
        analysis['user_active_days'] = {
            'mean': user_active_days.mean(),
            'median': user_active_days.median(),
            'std': user_active_days.std(),
            'max': user_active_days.max(),
            'min': user_active_days.min()
        }
        
        # 用户发布频率分析
        df_temp['date'] = df_temp['发布时间'].dt.date
        user_daily_posts = df_temp.groupby(['用户ID', 'date']).size().reset_index(name='daily_posts')
        user_avg_daily_posts = user_daily_posts.groupby('用户ID')['daily_posts'].mean()
        
        analysis['user_posting_frequency'] = {
            'avg_posts_per_day': user_avg_daily_posts.mean(),
            'median_posts_per_day': user_avg_daily_posts.median(),
            'high_frequency_users': (user_avg_daily_posts > 5).sum(),  # 每天超过5条
            'low_frequency_users': (user_avg_daily_posts < 1).sum()   # 每天少于1条
        }
        
        # 用户活跃时段偏好
        df_temp['hour'] = df_temp['发布时间'].dt.hour
        user_hour_preference = df_temp.groupby('用户ID')['hour'].apply(
            lambda x: x.mode().iloc[0] if not x.mode().empty else x.mean()
        )
        
        # 按时段分类用户
        morning_users = (user_hour_preference.between(6, 12)).sum()
        afternoon_users = (user_hour_preference.between(12, 18)).sum()
        evening_users = (user_hour_preference.between(18, 24)).sum()
        night_users = (user_hour_preference.between(0, 6)).sum()
        
        analysis['user_time_preference'] = {
            'morning_users': morning_users,
            'afternoon_users': afternoon_users,
            'evening_users': evening_users,
            'night_users': night_users
        }
        
        return analysis
    
    @cache_data(ttl=1800)
    def analyze_temporal_trends(self, df: pd.DataFrame) -> dict:
        """分析时间趋势"""
        analysis = {}
        
        if '发布时间' not in df.columns:
            return analysis
        
        # 确保发布时间是datetime类型
        df_temp = df.copy()
        df_temp['发布时间'] = pd.to_datetime(df_temp['发布时间'], errors='coerce')
        df_temp = df_temp.dropna(subset=['发布时间'])
        
        if df_temp.empty:
            return analysis
        
        # 按日期统计发布量
        df_temp['date'] = df_temp['发布时间'].dt.date
        daily_posts = df_temp['date'].value_counts().sort_index()
        
        # 计算趋势
        if len(daily_posts) > 1:
            # 简单线性趋势
            x = np.arange(len(daily_posts))
            y = daily_posts.values
            trend_slope = np.polyfit(x, y, 1)[0]
            
            analysis['trend_analysis'] = {
                'trend_slope': trend_slope,
                'trend_direction': 'increasing' if trend_slope > 0 else 'decreasing' if trend_slope < 0 else 'stable',
                'total_days': len(daily_posts),
                'avg_daily_posts': daily_posts.mean(),
                'max_daily_posts': daily_posts.max(),
                'min_daily_posts': daily_posts.min()
            }
        
        # 周期性分析
        df_temp['day_of_week'] = df_temp['发布时间'].dt.dayofweek
        weekly_pattern = df_temp['day_of_week'].value_counts().sort_index()
        
        # 计算周期性强度（标准差/均值）
        weekly_cv = weekly_pattern.std() / weekly_pattern.mean()
        analysis['periodicity'] = {
            'weekly_coefficient_variation': weekly_cv,
            'has_strong_weekly_pattern': weekly_cv > 0.3
        }
        
        return analysis
    
    def create_time_heatmap(self, df: pd.DataFrame) -> go.Figure:
        """创建时间热力图"""
        if '发布时间' not in df.columns:
            return go.Figure()
        
        # 确保发布时间是datetime类型
        df_temp = df.copy()
        df_temp['发布时间'] = pd.to_datetime(df_temp['发布时间'], errors='coerce')
        df_temp = df_temp.dropna(subset=['发布时间'])
        
        if df_temp.empty:
            return go.Figure()
        
        # 提取小时和星期
        df_temp['hour'] = df_temp['发布时间'].dt.hour
        df_temp['day_of_week'] = df_temp['发布时间'].dt.dayofweek
        
        # 创建热力图数据
        heatmap_data = df_temp.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
        heatmap_pivot = heatmap_data.pivot(index='day_of_week', columns='hour', values='count').fillna(0)
        
        # 星期标签
        day_labels = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_pivot.values,
            x=list(range(24)),
            y=day_labels,
            colorscale='Blues',
            text=heatmap_pivot.values,
            texttemplate="%{text}",
            textfont={"size": 10}
        ))
        
        fig.update_layout(
            title="发布时间热力图（星期 × 小时）",
            xaxis_title="小时",
            yaxis_title="星期",
            height=400
        )
        
        return fig

def main():
    """主函数"""
    st.title("⏰ 时间行为分析")
    
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
    
    # 检查是否有时间数据
    if '发布时间' not in df.columns:
        st.error("❌ 数据中缺少发布时间字段，无法进行时间分析")
        st.stop()
    
    analyzer = TimeAnalyzer()
    
    # 侧边栏控制
    st.sidebar.subheader("⏰ 分析选项")
    
    analysis_type = st.sidebar.selectbox(
        "选择分析类型",
        ["发布时间模式", "用户活跃模式", "时间趋势分析", "时间热力图", "综合时间报告"]
    )
    
    # 数据概览
    st.subheader("📈 数据概览")
    metrics = create_dashboard_metrics(df)
    display_metrics_cards(metrics)
    
    # 根据选择的分析类型显示内容
    if analysis_type == "发布时间模式":
        show_posting_patterns(df, analyzer)
    elif analysis_type == "用户活跃模式":
        show_user_activity_patterns(df, analyzer)
    elif analysis_type == "时间趋势分析":
        show_temporal_trends(df, analyzer)
    elif analysis_type == "时间热力图":
        show_time_heatmap(df, analyzer)
    elif analysis_type == "综合时间报告":
        show_comprehensive_time_report(df, analyzer)

def show_posting_patterns(df: pd.DataFrame, analyzer: TimeAnalyzer):
    """显示发布时间模式"""
    st.subheader("📅 发布时间模式分析")
    
    # 分析发布模式
    posting_analysis = analyzer.analyze_posting_patterns(df)
    
    if not posting_analysis:
        st.warning("无法分析发布时间模式，请检查数据格式")
        return
    
    # 小时分布
    col1, col2 = st.columns(2)
    
    with col1:
        if 'hourly_distribution' in posting_analysis:
            st.write("**24小时发布分布**")
            hourly_data = posting_analysis['hourly_distribution']
            
            fig_hourly = go.Figure(data=[
                go.Bar(
                    x=list(hourly_data.keys()),
                    y=list(hourly_data.values()),
                    marker_color=analyzer.visualizer.color_palette[0],
                    text=list(hourly_data.values()),
                    textposition='auto'
                )
            ])
            fig_hourly.update_layout(
                title="每小时发布量分布",
                xaxis_title="小时",
                yaxis_title="发布数量",
                xaxis=dict(tickmode='linear', tick0=0, dtick=2)
            )
            st.plotly_chart(fig_hourly, use_container_width=True)
    
    with col2:
        if 'weekly_distribution' in posting_analysis:
            st.write("**星期发布分布**")
            weekly_data = posting_analysis['weekly_distribution']
            
            # 重新排序星期
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            ordered_weekly_data = {day: weekly_data.get(day, 0) for day in day_order}
            
            fig_weekly = go.Figure(data=[
                go.Bar(
                    x=list(ordered_weekly_data.keys()),
                    y=list(ordered_weekly_data.values()),
                    marker_color=analyzer.visualizer.color_palette[1],
                    text=list(ordered_weekly_data.values()),
                    textposition='auto'
                )
            ])
            fig_weekly.update_layout(
                title="每周发布量分布",
                xaxis_title="星期",
                yaxis_title="发布数量"
            )
            st.plotly_chart(fig_weekly, use_container_width=True)
    
    # 活跃时段分析
    if 'peak_hours' in posting_analysis:
        st.subheader("🕐 活跃时段分析")
        
        peak_data = posting_analysis['peak_hours']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("最活跃时间", f"{peak_data['most_active_hour']}:00")
        with col2:
            st.metric("最不活跃时间", f"{peak_data['least_active_hour']}:00")
        with col3:
            st.metric("上午发布量", peak_data['morning_posts'])
        with col4:
            st.metric("晚上发布量", peak_data['evening_posts'])
        
        # 时段分布饼图
        time_periods = {
            '夜间(0-6点)': peak_data['night_posts'],
            '上午(6-12点)': peak_data['morning_posts'],
            '下午(12-18点)': peak_data['afternoon_posts'],
            '晚上(18-24点)': peak_data['evening_posts']
        }
        
        fig_periods = go.Figure(data=[
            go.Pie(
                labels=list(time_periods.keys()),
                values=list(time_periods.values()),
                hole=0.3
            )
        ])
        fig_periods.update_layout(title="时段发布分布")
        st.plotly_chart(fig_periods, use_container_width=True)
    
    # 工作日vs周末
    if 'weekend_vs_weekday' in posting_analysis:
        st.subheader("📊 工作日 vs 周末")
        
        weekend_data = posting_analysis['weekend_vs_weekday']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("工作日发布量", weekend_data['weekday_posts'])
        with col2:
            st.metric("周末发布量", weekend_data['weekend_posts'])
        
        # 工作日周末对比
        total_posts = weekend_data['weekday_posts'] + weekend_data['weekend_posts']
        if total_posts > 0:
            weekday_ratio = weekend_data['weekday_posts'] / total_posts * 100
            weekend_ratio = weekend_data['weekend_posts'] / total_posts * 100
            
            fig_weekend = go.Figure(data=[
                go.Bar(
                    x=['工作日', '周末'],
                    y=[weekend_data['weekday_posts'], weekend_data['weekend_posts']],
                    marker_color=[analyzer.visualizer.color_palette[0], analyzer.visualizer.color_palette[1]],
                    text=[f"{weekday_ratio:.1f}%", f"{weekend_ratio:.1f}%"],
                    textposition='auto'
                )
            ])
            fig_weekend.update_layout(
                title="工作日 vs 周末发布量对比",
                yaxis_title="发布数量"
            )
            st.plotly_chart(fig_weekend, use_container_width=True)

def show_user_activity_patterns(df: pd.DataFrame, analyzer: TimeAnalyzer):
    """显示用户活跃模式"""
    st.subheader("👥 用户活跃模式分析")
    
    # 分析用户活跃模式
    activity_analysis = analyzer.analyze_user_activity_patterns(df)
    
    if not activity_analysis:
        st.warning("无法分析用户活跃模式，请检查数据格式")
        return
    
    # 用户活跃天数统计
    if 'user_active_days' in activity_analysis:
        st.subheader("📅 用户活跃天数统计")
        
        active_days_stats = activity_analysis['user_active_days']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("平均活跃天数", f"{active_days_stats['mean']:.1f}")
        with col2:
            st.metric("中位数活跃天数", f"{active_days_stats['median']:.1f}")
        with col3:
            st.metric("最大活跃天数", f"{active_days_stats['max']:.0f}")
        with col4:
            st.metric("最小活跃天数", f"{active_days_stats['min']:.0f}")
    
    # 用户发布频率分析
    if 'user_posting_frequency' in activity_analysis:
        st.subheader("📊 用户发布频率分析")
        
        freq_stats = activity_analysis['user_posting_frequency']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**发布频率统计**")
            freq_metrics = [
                ["平均每日发布量", f"{freq_stats['avg_posts_per_day']:.2f}"],
                ["中位数每日发布量", f"{freq_stats['median_posts_per_day']:.2f}"],
                ["高频用户数(>5条/天)", f"{freq_stats['high_frequency_users']}"],
                ["低频用户数(<1条/天)", f"{freq_stats['low_frequency_users']}"]
            ]
            freq_df = pd.DataFrame(freq_metrics, columns=['指标', '数值'])
            st.dataframe(freq_df, use_container_width=True)
        
        with col2:
            # 用户频率分布
            freq_categories = {
                '低频用户(<1条/天)': freq_stats['low_frequency_users'],
                '中频用户(1-5条/天)': max(0, len(df['用户ID'].unique()) - freq_stats['high_frequency_users'] - freq_stats['low_frequency_users']),
                '高频用户(>5条/天)': freq_stats['high_frequency_users']
            }
            
            fig_freq = go.Figure(data=[
                go.Pie(
                    labels=list(freq_categories.keys()),
                    values=list(freq_categories.values()),
                    hole=0.3
                )
            ])
            fig_freq.update_layout(title="用户发布频率分布")
            st.plotly_chart(fig_freq, use_container_width=True)
    
    # 用户时段偏好
    if 'user_time_preference' in activity_analysis:
        st.subheader("🕐 用户时段偏好分析")
        
        time_pref = activity_analysis['user_time_preference']
        
        # 时段偏好分布
        time_periods = {
            '上午型(6-12点)': time_pref['morning_users'],
            '下午型(12-18点)': time_pref['afternoon_users'],
            '晚上型(18-24点)': time_pref['evening_users'],
            '夜间型(0-6点)': time_pref['night_users']
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 时段偏好柱状图
            fig_time_pref = go.Figure(data=[
                go.Bar(
                    x=list(time_periods.keys()),
                    y=list(time_periods.values()),
                    marker_color=analyzer.visualizer.color_palette[:4],
                    text=list(time_periods.values()),
                    textposition='auto'
                )
            ])
            fig_time_pref.update_layout(
                title="用户时段偏好分布",
                xaxis_title="时段类型",
                yaxis_title="用户数量"
            )
            st.plotly_chart(fig_time_pref, use_container_width=True)
        
        with col2:
            # 时段偏好饼图
            fig_time_pie = go.Figure(data=[
                go.Pie(
                    labels=list(time_periods.keys()),
                    values=list(time_periods.values()),
                    hole=0.3
                )
            ])
            fig_time_pie.update_layout(title="用户时段偏好占比")
            st.plotly_chart(fig_time_pie, use_container_width=True)
        
        # 时段偏好洞察
        most_popular_period = max(time_periods, key=time_periods.get)
        st.info(f"💡 最受欢迎的活跃时段：{most_popular_period}，共有{time_periods[most_popular_period]}名用户偏好此时段")

def show_temporal_trends(df: pd.DataFrame, analyzer: TimeAnalyzer):
    """显示时间趋势分析"""
    st.subheader("📈 时间趋势分析")
    
    # 分析时间趋势
    trend_analysis = analyzer.analyze_temporal_trends(df)
    
    if not trend_analysis:
        st.warning("无法分析时间趋势，请检查数据格式")
        return
    
    # 趋势分析
    if 'trend_analysis' in trend_analysis:
        st.subheader("📊 发布量趋势")
        
        trend_data = trend_analysis['trend_analysis']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总天数", trend_data['total_days'])
        with col2:
            st.metric("平均每日发布量", f"{trend_data['avg_daily_posts']:.1f}")
        with col3:
            st.metric("最高日发布量", trend_data['max_daily_posts'])
        with col4:
            st.metric("最低日发布量", trend_data['min_daily_posts'])
        
        # 趋势方向
        trend_direction = trend_data['trend_direction']
        trend_slope = trend_data['trend_slope']
        
        if trend_direction == 'increasing':
            st.success(f"📈 发布量呈上升趋势，斜率：{trend_slope:.3f}")
        elif trend_direction == 'decreasing':
            st.error(f"📉 发布量呈下降趋势，斜率：{trend_slope:.3f}")
        else:
            st.info(f"➡️ 发布量保持稳定，斜率：{trend_slope:.3f}")
        
        # 绘制时间序列图
        if '发布时间' in df.columns:
            df_temp = df.copy()
            df_temp['发布时间'] = pd.to_datetime(df_temp['发布时间'], errors='coerce')
            df_temp = df_temp.dropna(subset=['发布时间'])
            df_temp['date'] = df_temp['发布时间'].dt.date
            
            daily_posts = df_temp['date'].value_counts().sort_index()
            
            fig_trend = go.Figure()
            
            # 添加实际数据
            fig_trend.add_trace(go.Scatter(
                x=daily_posts.index,
                y=daily_posts.values,
                mode='lines+markers',
                name='每日发布量',
                line=dict(color=analyzer.visualizer.color_palette[0])
            ))
            
            # 添加趋势线
            x_numeric = np.arange(len(daily_posts))
            trend_line = np.polyval([trend_slope, daily_posts.values[0]], x_numeric)
            
            fig_trend.add_trace(go.Scatter(
                x=daily_posts.index,
                y=trend_line,
                mode='lines',
                name='趋势线',
                line=dict(color='red', dash='dash')
            ))
            
            fig_trend.update_layout(
                title="发布量时间趋势",
                xaxis_title="日期",
                yaxis_title="发布数量",
                height=400
            )
            st.plotly_chart(fig_trend, use_container_width=True)
    
    # 周期性分析
    if 'periodicity' in trend_analysis:
        st.subheader("🔄 周期性分析")
        
        periodicity_data = trend_analysis['periodicity']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("周期性系数", f"{periodicity_data['weekly_coefficient_variation']:.3f}")
        with col2:
            has_pattern = periodicity_data['has_strong_weekly_pattern']
            pattern_text = "强" if has_pattern else "弱"
            st.metric("周期性强度", pattern_text)
        
        if has_pattern:
            st.success("📅 数据显示出明显的周期性模式")
        else:
            st.info("📊 数据的周期性模式不明显")

def show_time_heatmap(df: pd.DataFrame, analyzer: TimeAnalyzer):
    """显示时间热力图"""
    st.subheader("🔥 时间热力图")
    
    # 创建时间热力图
    heatmap_fig = analyzer.create_time_heatmap(df)
    
    if heatmap_fig.data:
        st.plotly_chart(heatmap_fig, use_container_width=True)
        
        # 热力图洞察
        st.subheader("💡 热力图洞察")
        
        # 分析最活跃的时间段
        df_temp = df.copy()
        df_temp['发布时间'] = pd.to_datetime(df_temp['发布时间'], errors='coerce')
        df_temp = df_temp.dropna(subset=['发布时间'])
        
        if not df_temp.empty:
            df_temp['hour'] = df_temp['发布时间'].dt.hour
            df_temp['day_of_week'] = df_temp['发布时间'].dt.dayofweek
            
            # 找出最活跃的时间点
            time_counts = df_temp.groupby(['day_of_week', 'hour']).size()
            max_time = time_counts.idxmax()
            max_count = time_counts.max()
            
            day_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            peak_day = day_names[max_time[0]]
            peak_hour = max_time[1]
            
            insights = [
                f"🔥 最活跃时间：{peak_day} {peak_hour}:00，发布量：{max_count}",
                f"📊 热力图显示了用户在不同时间的活跃程度分布",
                f"⏰ 可以根据热力图优化内容发布时间策略"
            ]
            
            for insight in insights:
                st.info(insight)
    else:
        st.warning("无法生成时间热力图，请检查数据格式")

def show_comprehensive_time_report(df: pd.DataFrame, analyzer: TimeAnalyzer):
    """显示综合时间报告"""
    st.subheader("📋 综合时间行为报告")
    
    # 获取所有分析结果
    posting_analysis = analyzer.analyze_posting_patterns(df)
    activity_analysis = analyzer.analyze_user_activity_patterns(df)
    trend_analysis = analyzer.analyze_temporal_trends(df)
    
    # 关键指标概览
    st.subheader("📊 关键指标概览")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if posting_analysis and 'peak_hours' in posting_analysis:
            peak_hour = posting_analysis['peak_hours']['most_active_hour']
            st.metric("最活跃时间", f"{peak_hour}:00")
    
    with col2:
        if activity_analysis and 'user_active_days' in activity_analysis:
            avg_days = activity_analysis['user_active_days']['mean']
            st.metric("平均活跃天数", f"{avg_days:.1f}")
    
    with col3:
        if trend_analysis and 'trend_analysis' in trend_analysis:
            avg_daily = trend_analysis['trend_analysis']['avg_daily_posts']
            st.metric("平均每日发布量", f"{avg_daily:.1f}")
    
    with col4:
        if posting_analysis and 'weekend_vs_weekday' in posting_analysis:
            weekend_data = posting_analysis['weekend_vs_weekday']
            total = weekend_data['weekday_posts'] + weekend_data['weekend_posts']
            weekend_ratio = weekend_data['weekend_posts'] / total * 100 if total > 0 else 0
            st.metric("周末发布占比", f"{weekend_ratio:.1f}%")
    
    # 时间行为特征总结
    st.subheader("⏰ 时间行为特征")
    
    behavior_insights = []
    
    # 发布时间特征
    if posting_analysis:
        if 'peak_hours' in posting_analysis:
            peak_data = posting_analysis['peak_hours']
            most_active = peak_data['most_active_hour']
            behavior_insights.append(f"🕐 用户最活跃的时间是{most_active}:00")
            
            # 判断主要活跃时段
            time_periods = {
                '上午': peak_data['morning_posts'],
                '下午': peak_data['afternoon_posts'],
                '晚上': peak_data['evening_posts'],
                '夜间': peak_data['night_posts']
            }
            main_period = max(time_periods, key=time_periods.get)
            behavior_insights.append(f"📅 用户主要在{main_period}时段活跃")
        
        if 'weekend_vs_weekday' in posting_analysis:
            weekend_data = posting_analysis['weekend_vs_weekday']
            if weekend_data['weekday_posts'] > weekend_data['weekend_posts']:
                behavior_insights.append("💼 用户在工作日更加活跃")
            else:
                behavior_insights.append("🎉 用户在周末更加活跃")
    
    # 用户活跃模式特征
    if activity_analysis:
        if 'user_posting_frequency' in activity_analysis:
            freq_data = activity_analysis['user_posting_frequency']
            avg_freq = freq_data['avg_posts_per_day']
            if avg_freq > 3:
                behavior_insights.append(f"📈 用户发布频率较高，平均每天{avg_freq:.1f}条")
            elif avg_freq > 1:
                behavior_insights.append(f"📊 用户发布频率适中，平均每天{avg_freq:.1f}条")
            else:
                behavior_insights.append(f"📉 用户发布频率较低，平均每天{avg_freq:.1f}条")
        
        if 'user_time_preference' in activity_analysis:
            time_pref = activity_analysis['user_time_preference']
            pref_periods = {
                '上午型': time_pref['morning_users'],
                '下午型': time_pref['afternoon_users'],
                '晚上型': time_pref['evening_users'],
                '夜间型': time_pref['night_users']
            }
            dominant_type = max(pref_periods, key=pref_periods.get)
            behavior_insights.append(f"👥 用户群体以{dominant_type}为主")
    
    # 趋势特征
    if trend_analysis:
        if 'trend_analysis' in trend_analysis:
            trend_data = trend_analysis['trend_analysis']
            direction = trend_data['trend_direction']
            if direction == 'increasing':
                behavior_insights.append("📈 用户活跃度呈上升趋势")
            elif direction == 'decreasing':
                behavior_insights.append("📉 用户活跃度呈下降趋势")
            else:
                behavior_insights.append("➡️ 用户活跃度保持稳定")
        
        if 'periodicity' in trend_analysis:
            has_pattern = trend_analysis['periodicity']['has_strong_weekly_pattern']
            if has_pattern:
                behavior_insights.append("🔄 用户行为具有明显的周期性规律")
    
    for insight in behavior_insights:
        st.info(insight)
    
    # 策略建议
    st.subheader("💡 策略建议")
    
    recommendations = [
        "⏰ **最佳发布时间**：根据用户最活跃时间段安排内容发布",
        "📅 **周期性运营**：利用用户的周期性行为模式制定运营计划",
        "👥 **分群策略**：针对不同时段偏好的用户群体制定个性化策略",
        "📈 **趋势跟踪**：持续监控用户活跃度趋势，及时调整策略",
        "🎯 **精准投放**：在用户最活跃的时间段进行广告或内容投放"
    ]
    
    for recommendation in recommendations:
        st.markdown(recommendation)
    
    # 数据质量说明
    st.subheader("ℹ️ 数据说明")
    
    data_notes = [
        f"📅 分析时间范围：基于{len(df)}条记录的发布时间数据",
        "⏰ 时间精度：分析精确到小时级别",
        "📊 统计方法：采用描述性统计和趋势分析方法",
        "⚠️ 数据限制：分析结果基于样本数据，实际应用时需考虑时区和数据完整性"
    ]
    
    for note in data_notes:
        st.caption(note)

if __name__ == "__main__":
    main()
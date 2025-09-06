import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx
import sys
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from utils.visualizer import UserBehaviorVisualizer, create_dashboard_metrics, display_metrics_cards
from utils.cache_manager import cache_data
from config.settings import get_config

# 页面配置
st.set_page_config(
    page_title="社交网络分析",
    page_icon="🌐",
    layout="wide"
)

class SocialNetworkAnalyzer:
    """社交网络分析器"""
    
    def __init__(self):
        self.visualizer = UserBehaviorVisualizer()
        self.viz_config = get_config('viz')
    
    @cache_data(ttl=1800)
    def analyze_user_interactions(self, df: pd.DataFrame) -> dict:
        """分析用户互动模式"""
        analysis = {}
        
        # 检查必要字段
        required_fields = ['用户ID', '昵称']
        missing_fields = [field for field in required_fields if field not in df.columns]
        
        if missing_fields:
            analysis['error'] = f"缺少必要字段: {missing_fields}"
            return analysis
        
        # 用户基础统计
        unique_users = df['用户ID'].nunique()
        total_posts = len(df)
        
        analysis['basic_stats'] = {
            'unique_users': unique_users,
            'total_posts': total_posts,
            'avg_posts_per_user': total_posts / unique_users if unique_users > 0 else 0
        }
        
        # 用户活跃度分析
        user_activity = df.groupby('用户ID').agg({
            '昵称': 'first',
            '微博数': 'first',
            '关注数': 'first',
            '粉丝数': 'first'
        }).reset_index()
        
        # 计算互动指标
        if '微博数' in df.columns:
            user_activity['发布活跃度'] = user_activity['微博数']
        
        if '关注数' in df.columns and '粉丝数' in df.columns:
            user_activity['关注粉丝比'] = user_activity['关注数'] / (user_activity['粉丝数'] + 1)
            user_activity['影响力指数'] = user_activity['粉丝数'] / (user_activity['关注数'] + 1)
        
        analysis['user_activity'] = user_activity
        
        # 活跃度分层
        if '微博数' in df.columns:
            weibo_counts = user_activity['微博数'].fillna(0)
            
            # 定义活跃度等级
            activity_levels = {
                '超级活跃': weibo_counts >= weibo_counts.quantile(0.9),
                '高度活跃': (weibo_counts >= weibo_counts.quantile(0.7)) & (weibo_counts < weibo_counts.quantile(0.9)),
                '中度活跃': (weibo_counts >= weibo_counts.quantile(0.3)) & (weibo_counts < weibo_counts.quantile(0.7)),
                '低度活跃': weibo_counts < weibo_counts.quantile(0.3)
            }
            
            activity_distribution = {}
            for level, condition in activity_levels.items():
                activity_distribution[level] = condition.sum()
            
            analysis['activity_distribution'] = activity_distribution
        
        # 影响力分析
        if '粉丝数' in df.columns:
            fans_counts = user_activity['粉丝数'].fillna(0)
            
            influence_levels = {
                'KOL级别': fans_counts >= fans_counts.quantile(0.95),
                '高影响力': (fans_counts >= fans_counts.quantile(0.8)) & (fans_counts < fans_counts.quantile(0.95)),
                '中等影响力': (fans_counts >= fans_counts.quantile(0.5)) & (fans_counts < fans_counts.quantile(0.8)),
                '普通用户': fans_counts < fans_counts.quantile(0.5)
            }
            
            influence_distribution = {}
            for level, condition in influence_levels.items():
                influence_distribution[level] = condition.sum()
            
            analysis['influence_distribution'] = influence_distribution
        
        return analysis
    
    @cache_data(ttl=1800)
    def analyze_mention_network(self, df: pd.DataFrame, text_column: str = '微博文本') -> dict:
        """分析@提及网络"""
        analysis = {}
        
        if text_column not in df.columns:
            analysis['error'] = f"缺少文本字段: {text_column}"
            return analysis
        
        # 提取@提及
        import re
        mention_pattern = re.compile(r'@([\w\u4e00-\u9fff]+)')
        
        mentions_data = []
        
        for idx, row in df.iterrows():
            if pd.notna(row[text_column]):
                text = str(row[text_column])
                mentions = mention_pattern.findall(text)
                
                for mentioned_user in mentions:
                    mentions_data.append({
                        'from_user': row.get('昵称', row.get('用户ID', f'用户{idx}')),
                        'to_user': mentioned_user,
                        'from_user_id': row.get('用户ID', idx),
                        'post_content': text[:100] + '...' if len(text) > 100 else text
                    })
        
        if not mentions_data:
            analysis['mentions_count'] = 0
            analysis['network_stats'] = {'nodes': 0, 'edges': 0, 'density': 0}
            return analysis
        
        mentions_df = pd.DataFrame(mentions_data)
        
        # 提及统计
        analysis['mentions_count'] = len(mentions_df)
        analysis['unique_mentioners'] = mentions_df['from_user'].nunique()
        analysis['unique_mentioned'] = mentions_df['to_user'].nunique()
        
        # 最常被提及的用户
        most_mentioned = mentions_df['to_user'].value_counts().head(10)
        analysis['most_mentioned'] = most_mentioned.to_dict()
        
        # 最活跃的提及者
        most_mentioners = mentions_df['from_user'].value_counts().head(10)
        analysis['most_mentioners'] = most_mentioners.to_dict()
        
        # 构建网络图
        try:
            G = nx.from_pandas_edgelist(
                mentions_df, 
                source='from_user', 
                target='to_user', 
                create_using=nx.DiGraph()
            )
            
            # 网络统计
            analysis['network_stats'] = {
                'nodes': G.number_of_nodes(),
                'edges': G.number_of_edges(),
                'density': nx.density(G),
                'is_connected': nx.is_weakly_connected(G)
            }
            
            # 中心性分析
            if G.number_of_nodes() > 0:
                # 度中心性
                in_degree_centrality = nx.in_degree_centrality(G)
                out_degree_centrality = nx.out_degree_centrality(G)
                
                # 获取前10个最有影响力的节点
                top_in_degree = sorted(in_degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
                top_out_degree = sorted(out_degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
                
                analysis['centrality'] = {
                    'top_in_degree': dict(top_in_degree),
                    'top_out_degree': dict(top_out_degree)
                }
                
                # 保存网络图数据用于可视化
                pos = nx.spring_layout(G, k=1, iterations=50)
                
                edge_trace = []
                node_trace = []
                
                # 边数据
                for edge in G.edges():
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_trace.extend([x0, x1, None])
                    edge_trace.extend([y0, y1, None])
                
                # 节点数据
                node_x = []
                node_y = []
                node_text = []
                node_size = []
                
                for node in G.nodes():
                    x, y = pos[node]
                    node_x.append(x)
                    node_y.append(y)
                    
                    # 节点大小基于入度
                    in_degree = G.in_degree(node)
                    node_size.append(max(10, in_degree * 5))
                    
                    # 节点标签
                    node_text.append(f"{node}<br>被提及: {in_degree}次")
                
                analysis['network_viz'] = {
                    'edge_x': edge_trace[::3],
                    'edge_y': edge_trace[1::3],
                    'node_x': node_x,
                    'node_y': node_y,
                    'node_text': node_text,
                    'node_size': node_size
                }
        
        except Exception as e:
            analysis['network_error'] = str(e)
        
        return analysis
    
    @cache_data(ttl=1800)
    def analyze_follower_patterns(self, df: pd.DataFrame) -> dict:
        """分析关注者模式"""
        analysis = {}
        
        # 检查必要字段
        if '关注数' not in df.columns or '粉丝数' not in df.columns:
            analysis['error'] = "缺少关注数或粉丝数字段"
            return analysis
        
        # 过滤有效数据
        valid_data = df[(df['关注数'].notna()) & (df['粉丝数'].notna())].copy()
        
        if valid_data.empty:
            analysis['error'] = "没有有效的关注/粉丝数据"
            return analysis
        
        # 基础统计
        analysis['basic_stats'] = {
            'total_users': len(valid_data),
            'avg_following': valid_data['关注数'].mean(),
            'avg_followers': valid_data['粉丝数'].mean(),
            'median_following': valid_data['关注数'].median(),
            'median_followers': valid_data['粉丝数'].median(),
            'max_following': valid_data['关注数'].max(),
            'max_followers': valid_data['粉丝数'].max()
        }
        
        # 关注粉丝比分析
        valid_data['关注粉丝比'] = valid_data['关注数'] / (valid_data['粉丝数'] + 1)
        valid_data['影响力指数'] = valid_data['粉丝数'] / (valid_data['关注数'] + 1)
        
        # 用户类型分类
        user_types = {
            '意见领袖': (valid_data['粉丝数'] > valid_data['粉丝数'].quantile(0.9)) & 
                      (valid_data['关注粉丝比'] < 1),
            '活跃用户': (valid_data['关注数'] > valid_data['关注数'].quantile(0.7)) & 
                      (valid_data['粉丝数'] > valid_data['粉丝数'].quantile(0.3)),
            '潜水用户': (valid_data['关注数'] < valid_data['关注数'].quantile(0.3)) & 
                      (valid_data['粉丝数'] < valid_data['粉丝数'].quantile(0.3)),
            '关注狂': valid_data['关注数'] > valid_data['关注数'].quantile(0.9),
            '普通用户': True  # 默认类别
        }
        
        user_type_distribution = {}
        for user_type, condition in user_types.items():
            if user_type == '普通用户':
                # 普通用户是其他类型之外的用户
                other_conditions = [user_types[t] for t in user_types.keys() if t != '普通用户']
                combined_condition = pd.Series([False] * len(valid_data))
                for cond in other_conditions:
                    combined_condition = combined_condition | cond
                user_type_distribution[user_type] = (~combined_condition).sum()
            else:
                user_type_distribution[user_type] = condition.sum()
        
        analysis['user_type_distribution'] = user_type_distribution
        
        # 关注粉丝比分布
        ratio_bins = [0, 0.1, 0.5, 1, 2, 5, float('inf')]
        ratio_labels = ['超高影响力', '高影响力', '平衡型', '关注型', '高关注型', '关注狂']
        
        ratio_distribution = pd.cut(
            valid_data['关注粉丝比'], 
            bins=ratio_bins, 
            labels=ratio_labels, 
            right=False
        ).value_counts()
        
        analysis['ratio_distribution'] = ratio_distribution.to_dict()
        
        # 影响力分层
        influence_levels = {
            '超级影响者': valid_data['粉丝数'] >= valid_data['粉丝数'].quantile(0.95),
            '高影响者': (valid_data['粉丝数'] >= valid_data['粉丝数'].quantile(0.8)) & 
                       (valid_data['粉丝数'] < valid_data['粉丝数'].quantile(0.95)),
            '中等影响者': (valid_data['粉丝数'] >= valid_data['粉丝数'].quantile(0.5)) & 
                        (valid_data['粉丝数'] < valid_data['粉丝数'].quantile(0.8)),
            '普通用户': valid_data['粉丝数'] < valid_data['粉丝数'].quantile(0.5)
        }
        
        influence_distribution = {}
        for level, condition in influence_levels.items():
            influence_distribution[level] = condition.sum()
        
        analysis['influence_distribution'] = influence_distribution
        
        # 相关性分析
        correlation = valid_data[['关注数', '粉丝数']].corr().iloc[0, 1]
        analysis['following_followers_correlation'] = correlation
        
        # 异常值检测
        following_q99 = valid_data['关注数'].quantile(0.99)
        followers_q99 = valid_data['粉丝数'].quantile(0.99)
        
        outliers = valid_data[
            (valid_data['关注数'] > following_q99) | 
            (valid_data['粉丝数'] > followers_q99)
        ]
        
        analysis['outliers'] = {
            'count': len(outliers),
            'high_following': (valid_data['关注数'] > following_q99).sum(),
            'high_followers': (valid_data['粉丝数'] > followers_q99).sum()
        }
        
        return analysis
    
    @cache_data(ttl=1800)
    def analyze_interaction_intensity(self, df: pd.DataFrame) -> dict:
        """分析互动强度"""
        analysis = {}
        
        # 检查文本字段
        text_columns = [col for col in df.columns if '内容' in col]
        if not text_columns:
            analysis['error'] = "没有找到内容字段"
            return analysis
        
        text_column = text_columns[0]
        
        # 提取互动元素
        import re
        
        mention_pattern = re.compile(r'@[\w\u4e00-\u9fff]+')
        hashtag_pattern = re.compile(r'#[^#]+#')
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        
        interaction_data = []
        
        for idx, row in df.iterrows():
            if pd.notna(row[text_column]):
                text = str(row[text_column])
                
                mentions = len(mention_pattern.findall(text))
                hashtags = len(hashtag_pattern.findall(text))
                urls = len(url_pattern.findall(text))
                
                # 计算互动强度得分
                interaction_score = mentions * 3 + hashtags * 2 + urls * 1
                
                interaction_data.append({
                    'user_id': row.get('用户ID', idx),
                    'user_name': row.get('昵称', f'用户{idx}'),
                    'mentions': mentions,
                    'hashtags': hashtags,
                    'urls': urls,
                    'interaction_score': interaction_score,
                    'text_length': len(text)
                })
        
        if not interaction_data:
            analysis['error'] = "没有有效的互动数据"
            return analysis
        
        interaction_df = pd.DataFrame(interaction_data)
        
        # 基础统计
        analysis['basic_stats'] = {
            'total_posts': len(interaction_df),
            'avg_mentions': interaction_df['mentions'].mean(),
            'avg_hashtags': interaction_df['hashtags'].mean(),
            'avg_urls': interaction_df['urls'].mean(),
            'avg_interaction_score': interaction_df['interaction_score'].mean()
        }
        
        # 互动强度分布
        score_bins = [0, 1, 3, 6, 10, float('inf')]
        score_labels = ['无互动', '低互动', '中等互动', '高互动', '超高互动']
        
        intensity_distribution = pd.cut(
            interaction_df['interaction_score'],
            bins=score_bins,
            labels=score_labels,
            right=False
        ).value_counts()
        
        analysis['intensity_distribution'] = intensity_distribution.to_dict()
        
        # 用户互动排行
        user_interaction = interaction_df.groupby(['user_id', 'user_name']).agg({
            'mentions': 'sum',
            'hashtags': 'sum',
            'urls': 'sum',
            'interaction_score': 'sum'
        }).reset_index()
        
        # 最活跃互动用户
        top_interactive_users = user_interaction.nlargest(10, 'interaction_score')
        analysis['top_interactive_users'] = top_interactive_users.to_dict('records')
        
        # 互动类型偏好
        total_interactions = {
            'mentions': interaction_df['mentions'].sum(),
            'hashtags': interaction_df['hashtags'].sum(),
            'urls': interaction_df['urls'].sum()
        }
        
        total_count = sum(total_interactions.values())
        if total_count > 0:
            interaction_preferences = {
                k: v / total_count * 100 for k, v in total_interactions.items()
            }
            analysis['interaction_preferences'] = interaction_preferences
        
        # 互动与文本长度的关系
        if len(interaction_df) > 1:
            length_interaction_corr = interaction_df[['text_length', 'interaction_score']].corr().iloc[0, 1]
            analysis['length_interaction_correlation'] = length_interaction_corr
        
        return analysis

def main():
    """主函数"""
    st.title("🌐 社交网络分析")
    
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
    
    analyzer = SocialNetworkAnalyzer()
    
    # 侧边栏控制
    st.sidebar.subheader("🌐 分析选项")
    
    analysis_type = st.sidebar.selectbox(
        "选择分析类型",
        ["用户互动分析", "@提及网络", "关注者模式", "互动强度分析", "社交网络报告"]
    )
    
    # 数据概览
    st.subheader("📈 数据概览")
    metrics = create_dashboard_metrics(df)
    display_metrics_cards(metrics)
    
    # 根据选择的分析类型显示内容
    if analysis_type == "用户互动分析":
        show_user_interaction_analysis(df, analyzer)
    elif analysis_type == "@提及网络":
        show_mention_network_analysis(df, analyzer)
    elif analysis_type == "关注者模式":
        show_follower_pattern_analysis(df, analyzer)
    elif analysis_type == "互动强度分析":
        show_interaction_intensity_analysis(df, analyzer)
    elif analysis_type == "社交网络报告":
        show_social_network_report(df, analyzer)

def show_user_interaction_analysis(df: pd.DataFrame, analyzer: SocialNetworkAnalyzer):
    """显示用户互动分析"""
    st.subheader("👥 用户互动分析")
    
    # 分析用户互动
    interaction_analysis = analyzer.analyze_user_interactions(df)
    
    if 'error' in interaction_analysis:
        st.error(f"❌ {interaction_analysis['error']}")
        return
    
    # 基础统计
    if 'basic_stats' in interaction_analysis:
        st.subheader("📊 基础统计")
        
        stats = interaction_analysis['basic_stats']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("用户总数", stats['unique_users'])
        with col2:
            st.metric("内容总数", stats['total_posts'])
        with col3:
            st.metric("人均发布", f"{stats['avg_posts_per_user']:.1f}条")
    
    # 活跃度分布
    if 'activity_distribution' in interaction_analysis:
        st.subheader("📈 用户活跃度分布")
        
        activity_dist = interaction_analysis['activity_distribution']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 活跃度柱状图
            fig_activity = go.Figure(data=[
                go.Bar(
                    x=list(activity_dist.keys()),
                    y=list(activity_dist.values()),
                    marker_color=analyzer.visualizer.color_palette[0],
                    text=list(activity_dist.values()),
                    textposition='auto'
                )
            ])
            fig_activity.update_layout(
                title="用户活跃度分布",
                xaxis_title="活跃度等级",
                yaxis_title="用户数量"
            )
            st.plotly_chart(fig_activity, use_container_width=True)
        
        with col2:
            # 活跃度饼图
            fig_activity_pie = go.Figure(data=[
                go.Pie(
                    labels=list(activity_dist.keys()),
                    values=list(activity_dist.values()),
                    hole=0.3
                )
            ])
            fig_activity_pie.update_layout(title="活跃度占比")
            st.plotly_chart(fig_activity_pie, use_container_width=True)
    
    # 影响力分布
    if 'influence_distribution' in interaction_analysis:
        st.subheader("⭐ 用户影响力分布")
        
        influence_dist = interaction_analysis['influence_distribution']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 影响力柱状图
            fig_influence = go.Figure(data=[
                go.Bar(
                    x=list(influence_dist.keys()),
                    y=list(influence_dist.values()),
                    marker_color=analyzer.visualizer.color_palette[1],
                    text=list(influence_dist.values()),
                    textposition='auto'
                )
            ])
            fig_influence.update_layout(
                title="用户影响力分布",
                xaxis_title="影响力等级",
                yaxis_title="用户数量"
            )
            st.plotly_chart(fig_influence, use_container_width=True)
        
        with col2:
            # 影响力饼图
            fig_influence_pie = go.Figure(data=[
                go.Pie(
                    labels=list(influence_dist.keys()),
                    values=list(influence_dist.values()),
                    hole=0.3
                )
            ])
            fig_influence_pie.update_layout(title="影响力占比")
            st.plotly_chart(fig_influence_pie, use_container_width=True)
    
    # 用户活动详情
    if 'user_activity' in interaction_analysis:
        st.subheader("📋 用户活动详情")
        
        user_activity = interaction_analysis['user_activity']
        
        # 显示前20个最活跃用户
        if '微博数' in user_activity.columns:
            top_active_users = user_activity.nlargest(20, '微博数')
            
            st.write("**最活跃用户(前20)**")
            display_columns = ['昵称', '微博数', '关注数', '粉丝数']
            available_columns = [col for col in display_columns if col in top_active_users.columns]
            
            if available_columns:
                st.dataframe(
                    top_active_users[available_columns].reset_index(drop=True),
                    use_container_width=True
                )
        
        # 显示最有影响力用户
        if '粉丝数' in user_activity.columns:
            top_influential_users = user_activity.nlargest(20, '粉丝数')
            
            st.write("**最有影响力用户(前20)**")
            display_columns = ['昵称', '粉丝数', '关注数', '微博数']
            available_columns = [col for col in display_columns if col in top_influential_users.columns]
            
            if available_columns:
                st.dataframe(
                    top_influential_users[available_columns].reset_index(drop=True),
                    use_container_width=True
                )

def show_mention_network_analysis(df: pd.DataFrame, analyzer: SocialNetworkAnalyzer):
    """显示@提及网络分析"""
    st.subheader("🔗 @提及网络分析")
    
    # 选择文本列
    text_columns = [col for col in df.columns if '内容' in col]
    if not text_columns:
        st.error("❌ 数据中没有找到内容字段")
        return
    
    text_column = st.selectbox("选择文本字段", text_columns, index=0)
    
    # 分析@提及网络
    mention_analysis = analyzer.analyze_mention_network(df, text_column)
    
    if 'error' in mention_analysis:
        st.error(f"❌ {mention_analysis['error']}")
        return
    
    if mention_analysis.get('mentions_count', 0) == 0:
        st.warning("⚠️ 数据中没有发现@提及")
        return
    
    # 基础统计
    st.subheader("📊 @提及统计")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总提及次数", mention_analysis['mentions_count'])
    with col2:
        st.metric("提及者数量", mention_analysis['unique_mentioners'])
    with col3:
        st.metric("被提及者数量", mention_analysis['unique_mentioned'])
    
    # 网络统计
    if 'network_stats' in mention_analysis:
        st.subheader("🌐 网络结构统计")
        
        network_stats = mention_analysis['network_stats']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("网络节点", network_stats['nodes'])
        with col2:
            st.metric("网络边", network_stats['edges'])
        with col3:
            st.metric("网络密度", f"{network_stats['density']:.4f}")
        with col4:
            connected_status = "是" if network_stats.get('is_connected', False) else "否"
            st.metric("弱连通", connected_status)
    
    # 最常被提及的用户
    if 'most_mentioned' in mention_analysis:
        st.subheader("🏆 最常被提及用户")
        
        most_mentioned = mention_analysis['most_mentioned']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 被提及次数柱状图
            users = list(most_mentioned.keys())[:10]
            counts = [most_mentioned[user] for user in users]
            
            fig_mentioned = go.Figure(data=[
                go.Bar(
                    x=counts,
                    y=users,
                    orientation='h',
                    marker_color=analyzer.visualizer.color_palette[0],
                    text=counts,
                    textposition='auto'
                )
            ])
            fig_mentioned.update_layout(
                title="最常被提及用户(前10)",
                xaxis_title="被提及次数",
                yaxis_title="用户",
                height=400
            )
            st.plotly_chart(fig_mentioned, use_container_width=True)
        
        with col2:
            # 被提及用户表格
            mentioned_data = []
            for user, count in list(most_mentioned.items())[:10]:
                mentioned_data.append({'用户': user, '被提及次数': count})
            
            mentioned_df = pd.DataFrame(mentioned_data)
            st.dataframe(mentioned_df, use_container_width=True)
    
    # 最活跃的提及者
    if 'most_mentioners' in mention_analysis:
        st.subheader("📢 最活跃提及者")
        
        most_mentioners = mention_analysis['most_mentioners']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 提及次数柱状图
            mentioners = list(most_mentioners.keys())[:10]
            counts = [most_mentioners[user] for user in mentioners]
            
            fig_mentioners = go.Figure(data=[
                go.Bar(
                    x=counts,
                    y=mentioners,
                    orientation='h',
                    marker_color=analyzer.visualizer.color_palette[1],
                    text=counts,
                    textposition='auto'
                )
            ])
            fig_mentioners.update_layout(
                title="最活跃提及者(前10)",
                xaxis_title="提及次数",
                yaxis_title="用户",
                height=400
            )
            st.plotly_chart(fig_mentioners, use_container_width=True)
        
        with col2:
            # 提及者表格
            mentioner_data = []
            for user, count in list(most_mentioners.items())[:10]:
                mentioner_data.append({'用户': user, '提及次数': count})
            
            mentioner_df = pd.DataFrame(mentioner_data)
            st.dataframe(mentioner_df, use_container_width=True)
    
    # 中心性分析
    if 'centrality' in mention_analysis:
        st.subheader("🎯 网络中心性分析")
        
        centrality = mention_analysis['centrality']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**入度中心性(影响力)**")
            in_degree_data = []
            for user, score in list(centrality['top_in_degree'].items())[:10]:
                in_degree_data.append({'用户': user, '入度中心性': f"{score:.4f}"})
            
            if in_degree_data:
                in_degree_df = pd.DataFrame(in_degree_data)
                st.dataframe(in_degree_df, use_container_width=True)
        
        with col2:
            st.write("**出度中心性(活跃度)**")
            out_degree_data = []
            for user, score in list(centrality['top_out_degree'].items())[:10]:
                out_degree_data.append({'用户': user, '出度中心性': f"{score:.4f}"})
            
            if out_degree_data:
                out_degree_df = pd.DataFrame(out_degree_data)
                st.dataframe(out_degree_df, use_container_width=True)
    
    # 网络可视化
    if 'network_viz' in mention_analysis:
        st.subheader("🕸️ 网络可视化")
        
        viz_data = mention_analysis['network_viz']
        
        # 创建网络图
        fig_network = go.Figure()
        
        # 添加边
        fig_network.add_trace(go.Scatter(
            x=viz_data['edge_x'],
            y=viz_data['edge_y'],
            mode='lines',
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            showlegend=False
        ))
        
        # 添加节点
        fig_network.add_trace(go.Scatter(
            x=viz_data['node_x'],
            y=viz_data['node_y'],
            mode='markers+text',
            marker=dict(
                size=viz_data['node_size'],
                color=analyzer.visualizer.color_palette[0],
                line=dict(width=2, color='white')
            ),
            text=[text.split('<br>')[0] for text in viz_data['node_text']],  # 只显示用户名
            textposition="middle center",
            hovertext=viz_data['node_text'],
            hoverinfo='text',
            showlegend=False
        ))
        
        fig_network.update_layout(
            title="@提及网络图",
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[
                dict(
                    text="节点大小表示被提及次数，连线表示提及关系",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002,
                    xanchor='left', yanchor='bottom',
                    font=dict(size=12)
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        st.plotly_chart(fig_network, use_container_width=True)
        
        # 网络洞察
        st.subheader("💡 网络洞察")
        
        network_insights = [
            f"🌐 网络包含{mention_analysis['network_stats']['nodes']}个用户节点",
            f"🔗 共有{mention_analysis['network_stats']['edges']}条提及关系",
            f"📊 网络密度为{mention_analysis['network_stats']['density']:.4f}，表示连接程度",
            f"👑 最有影响力的用户是被提及最多的用户",
            f"📢 最活跃的用户是提及他人最多的用户"
        ]
        
        for insight in network_insights:
            st.info(insight)

def show_follower_pattern_analysis(df: pd.DataFrame, analyzer: SocialNetworkAnalyzer):
    """显示关注者模式分析"""
    st.subheader("👥 关注者模式分析")
    
    # 分析关注者模式
    follower_analysis = analyzer.analyze_follower_patterns(df)
    
    if 'error' in follower_analysis:
        st.error(f"❌ {follower_analysis['error']}")
        return
    
    # 基础统计
    if 'basic_stats' in follower_analysis:
        st.subheader("📊 关注/粉丝统计")
        
        stats = follower_analysis['basic_stats']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("分析用户数", stats['total_users'])
        with col2:
            st.metric("平均关注数", f"{stats['avg_following']:.0f}")
        with col3:
            st.metric("平均粉丝数", f"{stats['avg_followers']:.0f}")
        with col4:
            correlation = follower_analysis.get('following_followers_correlation', 0)
            st.metric("关注粉丝相关性", f"{correlation:.3f}")
        
        # 最大值统计
        col1, col2 = st.columns(2)
        with col1:
            st.metric("最大关注数", f"{stats['max_following']:,}")
        with col2:
            st.metric("最大粉丝数", f"{stats['max_followers']:,}")
    
    # 用户类型分布
    if 'user_type_distribution' in follower_analysis:
        st.subheader("👤 用户类型分布")
        
        user_types = follower_analysis['user_type_distribution']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 用户类型柱状图
            fig_types = go.Figure(data=[
                go.Bar(
                    x=list(user_types.keys()),
                    y=list(user_types.values()),
                    marker_color=analyzer.visualizer.color_palette[0],
                    text=list(user_types.values()),
                    textposition='auto'
                )
            ])
            fig_types.update_layout(
                title="用户类型分布",
                xaxis_title="用户类型",
                yaxis_title="用户数量",
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig_types, use_container_width=True)
        
        with col2:
            # 用户类型饼图
            fig_types_pie = go.Figure(data=[
                go.Pie(
                    labels=list(user_types.keys()),
                    values=list(user_types.values()),
                    hole=0.3
                )
            ])
            fig_types_pie.update_layout(title="用户类型占比")
            st.plotly_chart(fig_types_pie, use_container_width=True)
    
    # 关注粉丝比分布
    if 'ratio_distribution' in follower_analysis:
        st.subheader("⚖️ 关注粉丝比分布")
        
        ratio_dist = follower_analysis['ratio_distribution']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 比例分布柱状图
            fig_ratio = go.Figure(data=[
                go.Bar(
                    x=list(ratio_dist.keys()),
                    y=list(ratio_dist.values()),
                    marker_color=analyzer.visualizer.color_palette[1],
                    text=list(ratio_dist.values()),
                    textposition='auto'
                )
            ])
            fig_ratio.update_layout(
                title="关注粉丝比分布",
                xaxis_title="比例类型",
                yaxis_title="用户数量",
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig_ratio, use_container_width=True)
        
        with col2:
            # 比例分布饼图
            fig_ratio_pie = go.Figure(data=[
                go.Pie(
                    labels=list(ratio_dist.keys()),
                    values=list(ratio_dist.values()),
                    hole=0.3
                )
            ])
            fig_ratio_pie.update_layout(title="关注粉丝比占比")
            st.plotly_chart(fig_ratio_pie, use_container_width=True)
    
    # 影响力分布
    if 'influence_distribution' in follower_analysis:
        st.subheader("⭐ 影响力分布")
        
        influence_dist = follower_analysis['influence_distribution']
        
        # 影响力金字塔图
        fig_influence = go.Figure(data=[
            go.Bar(
                x=list(influence_dist.keys()),
                y=list(influence_dist.values()),
                marker_color=analyzer.visualizer.color_palette[2],
                text=list(influence_dist.values()),
                textposition='auto'
            )
        ])
        fig_influence.update_layout(
            title="用户影响力分布",
            xaxis_title="影响力等级",
            yaxis_title="用户数量"
        )
        st.plotly_chart(fig_influence, use_container_width=True)
        
        # 影响力洞察
        total_users = sum(influence_dist.values())
        if total_users > 0:
            kol_ratio = influence_dist.get('超级影响者', 0) / total_users * 100
            high_influence_ratio = influence_dist.get('高影响者', 0) / total_users * 100
            
            insights = [
                f"👑 超级影响者占比：{kol_ratio:.1f}%",
                f"⭐ 高影响者占比：{high_influence_ratio:.1f}%",
                f"📊 影响力呈现金字塔分布，符合社交网络特征"
            ]
            
            for insight in insights:
                st.info(insight)
    
    # 异常值分析
    if 'outliers' in follower_analysis:
        st.subheader("🔍 异常值分析")
        
        outliers = follower_analysis['outliers']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("异常用户总数", outliers['count'])
        with col2:
            st.metric("高关注用户", outliers['high_following'])
        with col3:
            st.metric("高粉丝用户", outliers['high_followers'])
        
        if outliers['count'] > 0:
            st.info(f"🔍 发现{outliers['count']}个异常用户，可能是机器人账号或特殊用户")

def show_interaction_intensity_analysis(df: pd.DataFrame, analyzer: SocialNetworkAnalyzer):
    """显示互动强度分析"""
    st.subheader("🔥 互动强度分析")
    
    # 分析互动强度
    intensity_analysis = analyzer.analyze_interaction_intensity(df)
    
    if 'error' in intensity_analysis:
        st.error(f"❌ {intensity_analysis['error']}")
        return
    
    # 基础统计
    if 'basic_stats' in intensity_analysis:
        st.subheader("📊 互动统计")
        
        stats = intensity_analysis['basic_stats']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总内容数", stats['total_posts'])
        with col2:
            st.metric("平均@提及", f"{stats['avg_mentions']:.2f}")
        with col3:
            st.metric("平均话题标签", f"{stats['avg_hashtags']:.2f}")
        with col4:
            st.metric("平均链接", f"{stats['avg_urls']:.2f}")
        
        st.metric("平均互动得分", f"{stats['avg_interaction_score']:.2f}")
    
    # 互动强度分布
    if 'intensity_distribution' in intensity_analysis:
        st.subheader("📈 互动强度分布")
        
        intensity_dist = intensity_analysis['intensity_distribution']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 强度分布柱状图
            fig_intensity = go.Figure(data=[
                go.Bar(
                    x=list(intensity_dist.keys()),
                    y=list(intensity_dist.values()),
                    marker_color=analyzer.visualizer.color_palette[0],
                    text=list(intensity_dist.values()),
                    textposition='auto'
                )
            ])
            fig_intensity.update_layout(
                title="互动强度分布",
                xaxis_title="互动强度",
                yaxis_title="内容数量"
            )
            st.plotly_chart(fig_intensity, use_container_width=True)
        
        with col2:
            # 强度分布饼图
            fig_intensity_pie = go.Figure(data=[
                go.Pie(
                    labels=list(intensity_dist.keys()),
                    values=list(intensity_dist.values()),
                    hole=0.3
                )
            ])
            fig_intensity_pie.update_layout(title="互动强度占比")
            st.plotly_chart(fig_intensity_pie, use_container_width=True)
    
    # 最活跃互动用户
    if 'top_interactive_users' in intensity_analysis:
        st.subheader("🏆 最活跃互动用户")
        
        top_users = intensity_analysis['top_interactive_users']
        
        if top_users:
            # 转换为DataFrame显示
            top_users_df = pd.DataFrame(top_users)
            
            # 重命名列
            column_mapping = {
                'user_name': '用户名',
                'mentions': '@提及数',
                'hashtags': '话题标签数',
                'urls': '链接数',
                'interaction_score': '互动得分'
            }
            
            display_columns = [col for col in column_mapping.keys() if col in top_users_df.columns]
            top_users_display = top_users_df[display_columns].rename(columns=column_mapping)
            
            st.dataframe(top_users_display, use_container_width=True)
            
            # 可视化前10用户的互动得分
            if len(top_users) > 0:
                top_10 = top_users[:10]
                
                fig_top_users = go.Figure(data=[
                    go.Bar(
                        x=[user['interaction_score'] for user in top_10],
                        y=[user['user_name'] for user in top_10],
                        orientation='h',
                        marker_color=analyzer.visualizer.color_palette[1],
                        text=[user['interaction_score'] for user in top_10],
                        textposition='auto'
                    )
                ])
                fig_top_users.update_layout(
                    title="最活跃互动用户(前10)",
                    xaxis_title="互动得分",
                    yaxis_title="用户",
                    height=400
                )
                st.plotly_chart(fig_top_users, use_container_width=True)
    
    # 互动类型偏好
    if 'interaction_preferences' in intensity_analysis:
        st.subheader("🎯 互动类型偏好")
        
        preferences = intensity_analysis['interaction_preferences']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 偏好柱状图
            pref_labels = {'mentions': '@提及', 'hashtags': '话题标签', 'urls': '链接分享'}
            labels = [pref_labels.get(k, k) for k in preferences.keys()]
            values = list(preferences.values())
            
            fig_pref = go.Figure(data=[
                go.Bar(
                    x=labels,
                    y=values,
                    marker_color=analyzer.visualizer.color_palette[2],
                    text=[f"{v:.1f}%" for v in values],
                    textposition='auto'
                )
            ])
            fig_pref.update_layout(
                title="互动类型偏好",
                xaxis_title="互动类型",
                yaxis_title="占比(%)"
            )
            st.plotly_chart(fig_pref, use_container_width=True)
        
        with col2:
            # 偏好饼图
            fig_pref_pie = go.Figure(data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.3
                )
            ])
            fig_pref_pie.update_layout(title="互动类型分布")
            st.plotly_chart(fig_pref_pie, use_container_width=True)
    
    # 互动与文本长度关系
    if 'length_interaction_correlation' in intensity_analysis:
        st.subheader("📏 互动与文本长度关系")
        
        correlation = intensity_analysis['length_interaction_correlation']
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric("相关系数", f"{correlation:.3f}")
            
            if correlation > 0.3:
                st.success("📈 强正相关：长文本倾向于有更多互动")
            elif correlation > 0.1:
                st.info("📊 弱正相关：文本长度与互动有一定关系")
            elif correlation < -0.1:
                st.warning("📉 负相关：短文本可能有更多互动")
            else:
                st.info("➡️ 无明显相关性")
        
        with col2:
            # 相关性解释
            correlation_insights = [
                f"📊 文本长度与互动强度的相关系数为{correlation:.3f}",
                "📝 正相关表示长文本通常包含更多互动元素",
                "💬 负相关表示短文本可能更容易引起互动",
                "🎯 可以根据此关系优化内容策略"
            ]
            
            for insight in correlation_insights:
                st.caption(insight)

def show_social_network_report(df: pd.DataFrame, analyzer: SocialNetworkAnalyzer):
    """显示社交网络综合报告"""
    st.subheader("📋 社交网络综合报告")
    
    # 获取所有分析结果
    interaction_analysis = analyzer.analyze_user_interactions(df)
    follower_analysis = analyzer.analyze_follower_patterns(df)
    intensity_analysis = analyzer.analyze_interaction_intensity(df)
    
    # 检查文本字段用于@提及分析
    text_columns = [col for col in df.columns if '内容' in col]
    mention_analysis = {}
    if text_columns:
        mention_analysis = analyzer.analyze_mention_network(df, text_columns[0])
    
    # 关键指标概览
    st.subheader("📊 关键指标概览")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'basic_stats' in interaction_analysis:
            unique_users = interaction_analysis['basic_stats']['unique_users']
            st.metric("活跃用户数", unique_users)
    
    with col2:
        if 'basic_stats' in follower_analysis:
            avg_followers = follower_analysis['basic_stats']['avg_followers']
            st.metric("平均粉丝数", f"{avg_followers:.0f}")
    
    with col3:
        if mention_analysis and 'mentions_count' in mention_analysis:
            mentions_count = mention_analysis['mentions_count']
            st.metric("@提及总数", mentions_count)
    
    with col4:
        if 'basic_stats' in intensity_analysis:
            avg_score = intensity_analysis['basic_stats']['avg_interaction_score']
            st.metric("平均互动得分", f"{avg_score:.2f}")
    
    # 社交网络特征总结
    st.subheader("🌐 社交网络特征")
    
    network_insights = []
    
    # 用户活跃度特征
    if 'activity_distribution' in interaction_analysis:
        activity_dist = interaction_analysis['activity_distribution']
        total_users = sum(activity_dist.values())
        
        if total_users > 0:
            super_active = activity_dist.get('超级活跃', 0) / total_users * 100
            if super_active > 20:
                network_insights.append(f"🔥 高活跃度网络：{super_active:.1f}%的用户为超级活跃用户")
            elif super_active > 10:
                network_insights.append(f"📊 中等活跃度网络：{super_active:.1f}%的用户为超级活跃用户")
            else:
                network_insights.append(f"😴 低活跃度网络：仅{super_active:.1f}%的用户为超级活跃用户")
    
    # 影响力分布特征
    if 'influence_distribution' in follower_analysis:
        influence_dist = follower_analysis['influence_distribution']
        total_users = sum(influence_dist.values())
        
        if total_users > 0:
            kol_ratio = influence_dist.get('超级影响者', 0) / total_users * 100
            if kol_ratio > 5:
                network_insights.append(f"👑 KOL密集型网络：{kol_ratio:.1f}%的用户具有超级影响力")
            else:
                network_insights.append(f"👥 平民化网络：仅{kol_ratio:.1f}%的用户具有超级影响力")
    
    # 互动模式特征
    if 'intensity_distribution' in intensity_analysis:
        intensity_dist = intensity_analysis['intensity_distribution']
        total_posts = sum(intensity_dist.values())
        
        if total_posts > 0:
            high_interaction = intensity_dist.get('高互动', 0) + intensity_dist.get('超高互动', 0)
            high_ratio = high_interaction / total_posts * 100
            
            if high_ratio > 30:
                network_insights.append(f"🔥 高互动网络：{high_ratio:.1f}%的内容具有高互动性")
            elif high_ratio > 15:
                network_insights.append(f"📊 中等互动网络：{high_ratio:.1f}%的内容具有高互动性")
            else:
                network_insights.append(f"😐 低互动网络：仅{high_ratio:.1f}%的内容具有高互动性")
    
    # 网络连通性特征
    if mention_analysis and 'network_stats' in mention_analysis:
        network_stats = mention_analysis['network_stats']
        density = network_stats.get('density', 0)
        
        if density > 0.1:
            network_insights.append(f"🕸️ 高密度网络：网络密度为{density:.4f}，用户间联系紧密")
        elif density > 0.01:
            network_insights.append(f"🔗 中密度网络：网络密度为{density:.4f}，用户间有一定联系")
        else:
            network_insights.append(f"🌌 稀疏网络：网络密度为{density:.4f}，用户间联系较少")
    
    # 显示网络洞察
    if network_insights:
        for insight in network_insights:
            st.info(insight)
    
    # 网络健康度评估
    st.subheader("💊 网络健康度评估")
    
    health_score = 0
    health_factors = []
    
    # 活跃度评分
    if 'activity_distribution' in interaction_analysis:
        activity_dist = interaction_analysis['activity_distribution']
        total_users = sum(activity_dist.values())
        
        if total_users > 0:
            active_ratio = (activity_dist.get('高度活跃', 0) + activity_dist.get('超级活跃', 0)) / total_users
            activity_score = min(active_ratio * 100, 25)  # 最高25分
            health_score += activity_score
            health_factors.append(f"用户活跃度：{activity_score:.1f}/25")
    
    # 影响力分布评分
    if 'influence_distribution' in follower_analysis:
        influence_dist = follower_analysis['influence_distribution']
        total_users = sum(influence_dist.values())
        
        if total_users > 0:
            # 理想的影响力分布应该是金字塔型
            kol_ratio = influence_dist.get('超级影响者', 0) / total_users
            high_ratio = influence_dist.get('高影响者', 0) / total_users
            
            # 评分逻辑：KOL不能太多也不能太少，高影响者应该适中
            if 0.01 <= kol_ratio <= 0.05 and 0.05 <= high_ratio <= 0.15:
                influence_score = 25
            elif 0.005 <= kol_ratio <= 0.1 and 0.03 <= high_ratio <= 0.2:
                influence_score = 20
            else:
                influence_score = 15
            
            health_score += influence_score
            health_factors.append(f"影响力分布：{influence_score}/25")
    
    # 互动活跃度评分
    if 'intensity_distribution' in intensity_analysis:
        intensity_dist = intensity_analysis['intensity_distribution']
        total_posts = sum(intensity_dist.values())
        
        if total_posts > 0:
            interactive_ratio = (intensity_dist.get('中等互动', 0) + 
                               intensity_dist.get('高互动', 0) + 
                               intensity_dist.get('超高互动', 0)) / total_posts
            interaction_score = min(interactive_ratio * 50, 25)  # 最高25分
            health_score += interaction_score
            health_factors.append(f"互动活跃度：{interaction_score:.1f}/25")
    
    # 网络连通性评分
    if mention_analysis and 'network_stats' in mention_analysis:
        network_stats = mention_analysis['network_stats']
        density = network_stats.get('density', 0)
        
        # 密度评分
        if density > 0.05:
            connectivity_score = 25
        elif density > 0.01:
            connectivity_score = 20
        elif density > 0.001:
            connectivity_score = 15
        else:
            connectivity_score = 10
        
        health_score += connectivity_score
        health_factors.append(f"网络连通性：{connectivity_score}/25")
    
    # 显示健康度评分
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # 健康度仪表盘
        fig_health = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = health_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "网络健康度"},
            delta = {'reference': 80},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_health.update_layout(height=300)
        st.plotly_chart(fig_health, use_container_width=True)
    
    with col2:
        # 健康度因子详情
        st.write("**健康度评分详情：**")
        for factor in health_factors:
            st.write(f"• {factor}")
        
        # 健康度等级
        if health_score >= 80:
            st.success(f"🌟 优秀网络 ({health_score:.1f}/100)")
            st.write("网络活跃度高，用户参与度强，影响力分布合理")
        elif health_score >= 60:
            st.info(f"👍 良好网络 ({health_score:.1f}/100)")
            st.write("网络运行良好，但仍有优化空间")
        elif health_score >= 40:
            st.warning(f"⚠️ 一般网络 ({health_score:.1f}/100)")
            st.write("网络存在一些问题，需要关注和改进")
        else:
            st.error(f"❌ 待改善网络 ({health_score:.1f}/100)")
            st.write("网络活跃度低，需要采取措施提升用户参与度")
    
    # 改进建议
    st.subheader("💡 网络优化建议")
    
    suggestions = []
    
    # 基于活跃度的建议
    if 'activity_distribution' in interaction_analysis:
        activity_dist = interaction_analysis['activity_distribution']
        total_users = sum(activity_dist.values())
        
        if total_users > 0:
            low_active = activity_dist.get('低度活跃', 0) / total_users
            if low_active > 0.5:
                suggestions.append("📈 提升用户活跃度：考虑推出激励机制，鼓励用户更多参与")
    
    # 基于影响力的建议
    if 'influence_distribution' in follower_analysis:
        influence_dist = follower_analysis['influence_distribution']
        total_users = sum(influence_dist.values())
        
        if total_users > 0:
            kol_ratio = influence_dist.get('超级影响者', 0) / total_users
            if kol_ratio < 0.01:
                suggestions.append("👑 培养意见领袖：识别和培养潜在的KOL用户")
            elif kol_ratio > 0.1:
                suggestions.append("⚖️ 平衡影响力：避免过度依赖少数KOL用户")
    
    # 基于互动的建议
    if 'intensity_distribution' in intensity_analysis:
        intensity_dist = intensity_analysis['intensity_distribution']
        total_posts = sum(intensity_dist.values())
        
        if total_posts > 0:
            no_interaction = intensity_dist.get('无互动', 0) / total_posts
            if no_interaction > 0.6:
                suggestions.append("💬 促进用户互动：优化内容推荐算法，增加互动功能")
    
    # 基于网络连通性的建议
    if mention_analysis and 'network_stats' in mention_analysis:
        network_stats = mention_analysis['network_stats']
        density = network_stats.get('density', 0)
        
        if density < 0.001:
            suggestions.append("🔗 增强网络连接：推出话题讨论、用户推荐等功能")
    
    # 显示建议
    if suggestions:
        for suggestion in suggestions:
            st.info(suggestion)
    else:
        st.success("🎉 网络运行良好，继续保持当前策略！")
    
    # 数据导出选项
    st.subheader("📤 数据导出")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("导出用户互动数据"):
            if 'user_activity' in interaction_analysis:
                user_data = interaction_analysis['user_activity']
                csv = user_data.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="下载CSV文件",
                    data=csv,
                    file_name="user_interaction_data.csv",
                    mime="text/csv"
                )
    
    with col2:
        if st.button("导出网络统计报告"):
            report_data = {
                '指标': [],
                '数值': []
            }
            
            # 收集所有统计数据
            if 'basic_stats' in interaction_analysis:
                stats = interaction_analysis['basic_stats']
                for key, value in stats.items():
                    report_data['指标'].append(f"用户互动_{key}")
                    report_data['数值'].append(value)
            
            if 'basic_stats' in follower_analysis:
                stats = follower_analysis['basic_stats']
                for key, value in stats.items():
                    report_data['指标'].append(f"关注模式_{key}")
                    report_data['数值'].append(value)
            
            if report_data['指标']:
                report_df = pd.DataFrame(report_data)
                csv = report_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="下载统计报告",
                    data=csv,
                    file_name="network_statistics_report.csv",
                    mime="text/csv"
                )
    
    with col3:
        if st.button("导出健康度评估"):
            health_data = {
                '评估项目': health_factors,
                '总体健康度': [f"{health_score:.1f}/100"] + [''] * (len(health_factors) - 1)
            }
            
            health_df = pd.DataFrame(health_data)
            csv = health_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="下载健康度报告",
                data=csv,
                file_name="network_health_report.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
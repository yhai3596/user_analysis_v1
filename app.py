import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')
import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import json

# 添加项目路径到系统路径
import sys
sys.path.append(str(Path(__file__).parent))

# 导入自定义模块
from utils.data_loader import BigDataLoader, DataProcessor
from utils.cache_manager import cache_manager, cache_data, show_cache_info, clear_all_cache
from utils.visualizer import UserBehaviorVisualizer, create_dashboard_metrics, display_metrics_cards
from config.settings import get_config
from config.version import get_version_info, format_version_display, format_roadmap_display

# 导入分析页面模块
try:
    from pages import user_profile, geo_analysis, time_analysis, content_analysis, social_network
    print("✅ 所有分析模块导入成功")
except ImportError as e:
    print(f"❌ 分析模块导入失败: {e}")
    import_error_msg = str(e)
    # 如果pages模块不存在，创建占位符模块
    class PlaceholderModule:
        def main(self):
            st.error(f"此分析模块尚未实现，请检查pages目录下的模块文件。错误信息: {import_error_msg}")
    
    user_profile = PlaceholderModule()
    geo_analysis = PlaceholderModule()
    time_analysis = PlaceholderModule()
    content_analysis = PlaceholderModule()
    social_network = PlaceholderModule()
except Exception as e:
    print(f"❌ 分析模块导入出现其他错误: {e}")
    other_error_msg = str(e)
    # 创建占位符模块
    class PlaceholderModule:
        def main(self):
            st.error(f"分析模块加载出现错误: {other_error_msg}")
    
    user_profile = PlaceholderModule()
    geo_analysis = PlaceholderModule()
    time_analysis = PlaceholderModule()
    content_analysis = PlaceholderModule()
    social_network = PlaceholderModule()

# 页面配置
st.set_page_config(
    page_title="用户行为分析系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #ff7f0e;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .sidebar-info {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .version-update {
        background-color: #f0f8ff;
        border-left: 4px solid #1f77b4;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 0.3rem;
    }
    .update-item {
        margin: 0.3rem 0;
        font-size: 0.9rem;
    }
    .version-badge {
        background-color: #1f77b4;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def detect_available_fonts():
    """检测系统可用字体"""
    try:
        import matplotlib.font_manager as fm
        
        # 中文字体关键词
        chinese_keywords = [
            'SimHei', 'SimSun', 'Microsoft YaHei', 'Microsoft JhengHei',
            'PingFang', 'Hiragino', 'STHeiti', 'STSong', 'STKaiti',
            'FangSong', 'KaiTi', 'LiSu', 'YouYuan', 'Chinese', 'CJK'
        ]
        
        # 获取所有字体
        all_fonts = [f.name for f in fm.fontManager.ttflist]
        
        # 查找中文字体
        chinese_fonts = []
        for font_name in all_fonts:
            for keyword in chinese_keywords:
                if keyword.lower() in font_name.lower():
                    if font_name not in chinese_fonts:
                        chinese_fonts.append(font_name)
                    break
        
        # 常用英文字体
        common_fonts = ['Arial', 'Times New Roman', 'Calibri', 'Verdana', 'Helvetica']
        english_fonts = [font for font in common_fonts if font in all_fonts]
        
        # 合并字体列表，中文字体优先
        available_fonts = chinese_fonts + english_fonts
        
        # 如果没有找到任何字体，使用默认列表
        if not available_fonts:
            available_fonts = ['DejaVu Sans', 'Arial', 'Times New Roman']
        
        return available_fonts
        
    except Exception as e:
        st.warning(f"字体检测失败: {e}")
        return ['DejaVu Sans', 'Arial', 'Times New Roman']

def validate_font(font_name):
    """验证字体是否可用"""
    try:
        import matplotlib.font_manager as fm
        
        # 检查字体是否在系统中
        font_files = [f for f in fm.fontManager.ttflist if font_name in f.name]
        return len(font_files) > 0
    except:
        return False

def load_font_config():
    """加载字体配置"""
    try:
        # 检测可用字体
        available_fonts = detect_available_fonts()
        
        # 选择默认字体（优先选择中文字体）
        default_font = 'SimHei'  # 默认首选
        if default_font not in available_fonts and available_fonts:
            default_font = available_fonts[0]
        
        default_config = {
            'available_fonts': available_fonts,
            'selected_font': default_font,
            'font_size': 12,
            'font_validated': validate_font(default_font)
        }
        
        # 尝试从文件加载保存的配置
        config_file = os.path.join(os.path.dirname(__file__), 'font_config.json')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                
                # 验证保存的字体是否仍然可用
                if (saved_config.get('selected_font') in available_fonts and 
                    validate_font(saved_config.get('selected_font'))):
                    default_config.update({
                        'selected_font': saved_config.get('selected_font'),
                        'font_size': saved_config.get('font_size', 12),
                        'font_validated': True
                    })
            except Exception as e:
                st.warning(f"读取保存的字体配置失败: {e}")
        
        return default_config
        
    except Exception as e:
        st.warning(f"字体配置加载失败: {e}")
        return {
            'available_fonts': ['DejaVu Sans', 'Arial', 'Times New Roman'],
            'selected_font': 'DejaVu Sans',
            'font_size': 12,
            'font_validated': False
        }

def apply_font_config(font_config):
    """应用字体配置"""
    try:
        plt.rcParams['font.family'] = font_config['selected_font']
        plt.rcParams['font.size'] = font_config['font_size']
        plt.rcParams['axes.unicode_minus'] = False
    except Exception as e:
        st.warning(f"字体配置应用失败: {e}")

def save_font_config(font_config):
    """保存字体配置到文件"""
    try:
        config_file = os.path.join(os.path.dirname(__file__), 'font_config.json')
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump({
                'selected_font': font_config['selected_font'],
                'font_size': font_config['font_size']
            }, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.warning(f"保存字体配置失败: {e}")
        return False

def initialize_session_state():
    """初始化会话状态"""
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'current_data' not in st.session_state:
        st.session_state.current_data = None
    if 'data_info' not in st.session_state:
        st.session_state.data_info = None
    if 'processing_mode' not in st.session_state:
        st.session_state.processing_mode = 'sample'  # sample 或 full
    if 'font_config' not in st.session_state:
        st.session_state.font_config = load_font_config()

def check_data_loaded():
    """检查数据是否已加载"""
    return (st.session_state.get('data_loaded', False) and 
            st.session_state.get('current_data') is not None)

def show_data_required_message():
    """显示需要加载数据的提示信息"""
    st.error("❌ 数据获取失败，请返回主页重新加载数据")
    
    st.markdown("""
    ### 📋 解决方案
    
    1. **返回数据概览页面**: 点击左侧导航中的 "🏠 数据概览"
    2. **加载数据**: 在左侧控制面板中选择数据文件和处理模式
    3. **点击加载按钮**: 点击 "🚀 加载数据" 按钮开始数据加载
    4. **等待加载完成**: 数据加载成功后即可使用所有分析功能
    
    ### 💡 提示
    
    - **样本模式**: 快速加载1000条记录，适合数据预览
    - **完整模式**: 加载所有数据，适合完整分析
    - 确保数据文件路径正确且文件存在
    """)
    
    # 添加快速返回按钮
    if st.button("🏠 返回数据概览", type="primary"):
        st.session_state.page = "🏠 数据概览"
        st.rerun()

def load_data(file_path: str, processing_mode: str = 'sample'):
    """加载数据"""
    try:
        loader = BigDataLoader()
        
        if processing_mode == 'sample':
            # 样本模式：快速加载少量数据
            with st.spinner('正在加载样本数据...'):
                df = loader.load_data_sample(file_path, sample_size=1000)
                st.session_state.current_data = df
                st.session_state.data_loaded = True
                st.success(f"样本数据加载成功！共 {len(df)} 条记录")
        else:
            # 完整模式：分块加载所有数据
            with st.spinner('正在加载完整数据...'):
                chunks = []
                progress_bar = st.progress(0)
                chunk_count = 0
                
                for chunk in loader.load_data_chunked(file_path, chunk_size=5000):
                    chunks.append(chunk)
                    chunk_count += 1
                    progress_bar.progress(min(chunk_count * 0.1, 1.0))
                
                df = pd.concat(chunks, ignore_index=True)
                st.session_state.current_data = df
                st.session_state.data_loaded = True
                progress_bar.progress(1.0)
                st.success(f"完整数据加载成功！共 {len(df)} 条记录")
        
        # 获取数据信息
        st.session_state.data_info = loader.get_data_info(file_path)
        
        # 初始化筛选数据为原始数据
        st.session_state.filtered_data = st.session_state.current_data
        
    except Exception as e:
        st.error(f"数据加载失败: {str(e)}")
        st.session_state.data_loaded = False

def sidebar_controls():
    """侧边栏控制面板"""
    st.sidebar.markdown('<div class="sidebar-info">', unsafe_allow_html=True)
    st.sidebar.title("📊 控制面板")
    
    # 数据加载部分
    st.sidebar.subheader("📁 数据加载")
    
    # 文件选择
    default_file = "切片.xlsx"  # 使用相对路径
    file_path = st.sidebar.text_input(
        "数据文件路径",
        value=default_file,
        help="请输入Excel或CSV文件的完整路径"
    )
    
    # 处理模式选择
    processing_mode = st.sidebar.selectbox(
        "处理模式",
        options=['sample', 'full'],
        format_func=lambda x: '样本模式 (快速)' if x == 'sample' else '完整模式 (完整数据)',
        help="样本模式：快速加载1000条记录用于预览\n完整模式：加载所有数据进行完整分析"
    )
    
    st.session_state.processing_mode = processing_mode
    
    # 加载按钮
    if st.sidebar.button("🔄 加载数据", type="primary"):
        if os.path.exists(file_path):
            load_data(file_path, processing_mode)
        else:
            st.sidebar.error("文件不存在，请检查路径")
    
    # 数据状态显示
    if st.session_state.data_loaded:
        st.sidebar.success("✅ 数据已加载")
        df = st.session_state.current_data
        st.sidebar.info(f"📊 数据形状: {df.shape[0]} 行 × {df.shape[1]} 列")
        
        # 数据筛选选项
        st.sidebar.subheader("🔍 数据筛选")
        
        # 性别筛选
        if '性别' in df.columns:
            gender_options = ['全部'] + list(df['性别'].dropna().unique())
            selected_gender = st.sidebar.selectbox("性别", gender_options)
            if selected_gender != '全部':
                df = df[df['性别'] == selected_gender]
        
        # 省份筛选
        if '注册省份' in df.columns:
            province_options = ['全部'] + list(df['注册省份'].dropna().unique())
            selected_province = st.sidebar.selectbox("省份", province_options)
            if selected_province != '全部':
                df = df[df['注册省份'] == selected_province]
        
        # 更新筛选后的数据
        st.session_state.filtered_data = df
    else:
        st.sidebar.warning("⚠️ 请先加载数据")
    
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # 缓存管理
    st.sidebar.subheader("🗄️ 缓存管理")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("📊 缓存信息"):
            show_cache_info()
    with col2:
        if st.button("🗑️ 清空缓存"):
            clear_all_cache()
    
    # 应用信息
    st.sidebar.markdown("---")
    st.sidebar.subheader("ℹ️ 应用信息")
    
    # 获取版本信息
    version_info = get_version_info()
    st.sidebar.info(
        f"**{version_info['app_name']} v{version_info['version']}**\n\n"
        "功能模块：\n"
        "• 用户画像分析\n"
        "• 地理行为分析\n"
        "• 时间行为分析\n"
        "• 内容行为分析\n"
        "• 社交网络分析"
    )
    
    # 版本更新说明
    st.sidebar.subheader("🔄 版本更新")
    with st.sidebar.expander("📋 更新日志", expanded=False):
        changelog = format_version_display()
        st.markdown(changelog)
    
    with st.sidebar.expander("🚀 即将推出", expanded=False):
        roadmap = format_roadmap_display()
        st.markdown(roadmap)

def main_content():
    """主内容区域"""
    # 主标题
    st.markdown('<h1 class="main-header">📊 用户行为分析系统</h1>', unsafe_allow_html=True)
    
    if not st.session_state.data_loaded:
        # 欢迎页面
        st.markdown("""
        ## 👋 欢迎使用用户行为分析系统
        
        这是一个专业的用户行为分析工具，支持大数据量处理和多维度分析。
        
        ### 🚀 主要功能
        
        - **📊 用户画像分析**: 基础属性、活跃度、影响力分析
        - **🗺️ 地理行为分析**: 位置分布、热力图、轨迹分析
        - **⏰ 时间行为分析**: 发布时间模式、活跃时段分析
        - **📝 内容行为分析**: 文本分析、话题挖掘、情感分析
        - **🔗 社交网络分析**: 互动模式、影响力传播分析
        
        ### 📋 使用说明
        
        1. **数据加载**: 在左侧面板选择数据文件和处理模式
        2. **模式选择**: 
           - 样本模式：快速加载1000条记录，适合数据预览
           - 完整模式：加载所有数据，适合完整分析
        3. **分析探索**: 使用顶部导航切换不同分析模块
        4. **结果导出**: 支持图表下载和报告生成
        
        ### ⚡ 性能优化
        
        - 智能缓存机制，避免重复计算
        - 分块数据处理，支持大文件加载
        - 内存优化，提升处理效率
        
        **请在左侧面板加载数据开始分析！**
        """)
        
        # 示例数据展示
        st.subheader("📋 数据格式示例")
        example_data = {
            '用户ID': [1001, 1002, 1003],
            '性别': ['男', '女', '男'],
            '昵称': ['用户A', '用户B', '用户C'],
            '注册省份': ['上海', '北京', '广东'],
            '微博数': [1250, 890, 2100],
            '粉丝数': [500, 1200, 800],
            '发布时间': ['2019-10-15 14:30:00', '2019-10-15 16:45:00', '2019-10-15 18:20:00']
        }
        st.dataframe(pd.DataFrame(example_data))
        
    else:
        # 数据概览页面
        df = st.session_state.get('filtered_data', st.session_state.current_data)
        
        st.markdown('<h2 class="sub-header">📈 数据概览</h2>', unsafe_allow_html=True)
        
        # 显示关键指标
        metrics = create_dashboard_metrics(df)
        display_metrics_cards(metrics)
        
        # 数据预览
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📊 数据预览")
            st.dataframe(df.head(10), use_container_width=True)
        
        with col2:
            st.subheader("📋 数据信息")
            st.write(f"**总记录数**: {len(df):,}")
            st.write(f"**字段数量**: {len(df.columns)}")
            st.write(f"**处理模式**: {'样本模式' if st.session_state.processing_mode == 'sample' else '完整模式'}")
            
            # 缺失值统计
            missing_data = df.isnull().sum()
            missing_data = missing_data[missing_data > 0]
            if not missing_data.empty:
                st.write("**缺失值统计**:")
                for col, count in missing_data.items():
                    percentage = (count / len(df)) * 100
                    st.write(f"• {col}: {count} ({percentage:.1f}%)")
        
        # 数据类型信息
        st.subheader("🔍 字段信息")
        col_info = pd.DataFrame({
            '字段名': df.columns,
            '数据类型': [str(dtype) for dtype in df.dtypes],
            '非空值数量': [df[col].count() for col in df.columns],
            '唯一值数量': [df[col].nunique() for col in df.columns]
        })
        st.dataframe(col_info, use_container_width=True)
        
        # 导航提示
        st.info("💡 数据加载完成！请使用顶部导航栏选择具体的分析模块进行深入分析。")

# 重复的load_data函数已删除，使用第116行的版本

def main():
    """主函数"""
    # 初始化会话状态
    initialize_session_state()
    
    # 页面导航
    st.sidebar.title("🔍 用户行为分析平台")
    
    # 页面选择
    page = st.sidebar.selectbox(
        "选择分析模块",
        [
            "🏠 数据概览",
            "👤 用户画像分析", 
            "🌍 地理行为分析",
            "⏰ 时间行为分析",
            "📝 内容行为分析",
            "🕸️ 社交网络分析"
        ]
    )
    
    # 根据选择显示对应页面
    if page == "🏠 数据概览":
        show_data_overview()
    elif page == "👤 用户画像分析":
        if check_data_loaded():
            user_profile.main()
        else:
            show_data_required_message()
    elif page == "🌍 地理行为分析":
        if check_data_loaded():
            geo_analysis.main()
        else:
            show_data_required_message()
    elif page == "⏰ 时间行为分析":
        if check_data_loaded():
            time_analysis.main()
        else:
            show_data_required_message()
    elif page == "📝 内容行为分析":
        if check_data_loaded():
            content_analysis.main()
        else:
            show_data_required_message()
    elif page == "🕸️ 社交网络分析":
        if check_data_loaded():
            social_network.main()
        else:
            show_data_required_message()
    
    # 页脚
    st.markdown("---")
    version_info = get_version_info()
    st.markdown(
        f"<div style='text-align: center; color: #666; padding: 1rem;'>"
        f"{version_info['app_name']} v{version_info['version']} | 基于 Streamlit 构建 | © 2024 | "
        f"<a href='#' style='color: #1f77b4; text-decoration: none;'>📋 更新日志</a>"
        "</div>",
        unsafe_allow_html=True
    )

def show_data_overview():
    """显示数据概览页面"""
    st.title("🔍 用户行为分析平台 - 数据概览")
    st.markdown("---")
    
    # 侧边栏控制面板
    with st.sidebar:
        st.header("⚙️ 控制面板")
        
        # 数据加载选项
        st.subheader("📊 数据加载")
        data_mode = st.selectbox(
            "选择数据模式",
            ["样本数据 (快速预览)", "完整数据 (大数据处理)"],
            help="样本数据用于快速预览，完整数据启用大数据处理模式"
        )
        
        # 处理模式选择
        st.subheader("🔧 处理模式")
        processing_mode = st.selectbox(
            "选择处理模式",
            ["标准模式", "高性能模式", "内存优化模式"],
            help="不同模式适用于不同的数据量和硬件配置"
        )
        
        # 字体配置
        st.subheader("🎨 字体配置")
        font_config = st.session_state.font_config
        
        # 显示当前字体状态
        current_font = font_config.get('selected_font', 'DejaVu Sans')
        font_validated = font_config.get('font_validated', False)
        
        if font_validated:
            st.success(f"✅ 当前字体: {current_font}")
        else:
            st.warning(f"⚠️ 当前字体: {current_font} (可能不支持中文)")
        
        # 字体选择
        available_fonts = font_config.get('available_fonts', ['DejaVu Sans'])
        try:
            current_index = available_fonts.index(current_font)
        except ValueError:
            current_index = 0
        
        selected_font = st.selectbox(
            "选择字体",
            options=available_fonts,
            index=current_index,
            help="选择适合的字体以正确显示中文字符"
        )
        
        # 字体大小
        font_size = st.slider(
            "字体大小",
            min_value=8,
            max_value=20,
            value=font_config.get('font_size', 12),
            help="调整图表中文字的大小"
        )
        
        # 字体预览
        if st.checkbox("显示字体预览", value=False):
            try:
                import matplotlib.pyplot as plt
                import matplotlib.font_manager as fm
                
                fig, ax = plt.subplots(figsize=(6, 2))
                test_text = "字体预览 Font Preview 123"
                
                # 尝试使用选择的字体
                try:
                    plt.rcParams['font.family'] = selected_font
                    ax.text(0.5, 0.5, test_text, ha='center', va='center', 
                           fontsize=font_size, transform=ax.transAxes)
                except:
                    ax.text(0.5, 0.5, f"字体 {selected_font} 预览失败", 
                           ha='center', va='center', fontsize=font_size, 
                           transform=ax.transAxes)
                
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.axis('off')
                st.pyplot(fig)
                plt.close(fig)
            except Exception as e:
                st.error(f"字体预览失败: {e}")
        
        # 应用按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 刷新字体列表"):
                st.session_state.font_config = load_font_config()
                st.success("字体列表已刷新")
                st.rerun()
        
        with col2:
            if st.button("✅ 应用字体设置"):
                # 验证选择的字体
                is_valid = validate_font(selected_font)
                
                st.session_state.font_config['selected_font'] = selected_font
                st.session_state.font_config['font_size'] = font_size
                st.session_state.font_config['font_validated'] = is_valid
                
                apply_font_config(st.session_state.font_config)
                
                # 保存配置到文件
                if save_font_config(st.session_state.font_config):
                    if is_valid:
                        st.success("✅ 字体设置已应用并保存")
                    else:
                        st.warning("⚠️ 字体设置已应用并保存，但该字体可能不支持中文显示")
                else:
                    if is_valid:
                        st.success("✅ 字体设置已应用（保存失败）")
                    else:
                        st.warning("⚠️ 字体设置已应用（保存失败），但该字体可能不支持中文显示")
        
        # 字体信息
        with st.expander("📋 字体详细信息", expanded=False):
            st.write(f"**可用字体数量**: {len(available_fonts)}")
            st.write(f"**字体大小**: {font_size}")
            st.write(f"**验证状态**: {'✅ 已验证' if font_validated else '❌ 未验证'}")
            
            if st.checkbox("显示所有可用字体"):
                for i, font in enumerate(available_fonts, 1):
                    validation_status = "✅" if validate_font(font) else "❌"
                    st.write(f"{i}. {validation_status} {font}")
        
        # 缓存管理
        st.subheader("💾 缓存管理")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("清理缓存"):
                clear_all_cache()
                st.success("缓存已清理")
        
        with col2:
            if st.button("缓存信息"):
                show_cache_info()
        
        # 文件路径输入
        file_path = st.text_input(
            "数据文件路径",
            value="切片.xlsx",  # 使用相对路径
            help="请输入Excel或CSV文件的完整路径"
        )
        
        # 数据加载按钮
        if st.button("🚀 加载数据", type="primary"):
            if not file_path:
                st.error("请输入数据文件路径")
            else:
                # 确定处理模式
                processing_mode_map = {
                    "样本数据 (快速预览)": "sample",
                    "完整数据 (大数据处理)": "full"
                }
                mode = processing_mode_map.get(data_mode, "sample")
                st.session_state.processing_mode = mode
                
                # 加载数据
                load_data(file_path, mode)
                
                # 检查加载是否成功
                if st.session_state.get('data_loaded', False):
                    st.rerun()
    
    # 主内容区域
    if st.session_state.get('data_loaded', False):
        data = st.session_state.current_data
        
        # 数据概览
        st.header("📈 数据概览")
        
        # 关键指标
        metrics = create_dashboard_metrics(data)
        display_metrics_cards(metrics)
        
        # 数据预览
        st.subheader("🔍 数据预览")
        
        # 数据基本信息
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总记录数", f"{len(data):,}")
        with col2:
            if '用户ID' in data.columns:
                st.metric("用户数量", f"{data['用户ID'].nunique():,}")
            else:
                st.metric("用户数量", "N/A")
        with col3:
            if '发布时间' in data.columns:
                try:
                    time_span = (data['发布时间'].max() - data['发布时间'].min()).days
                    st.metric("时间跨度", f"{time_span} 天")
                except:
                    st.metric("时间跨度", "N/A")
            else:
                st.metric("时间跨度", "N/A")
        
        # 数据表格预览
        st.dataframe(
            data.head(100),
            use_container_width=True,
            height=300
        )
        
        # 快速统计
        st.subheader("📊 快速统计")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 发布时间分布
            if '发布时间' in data.columns:
                try:
                    fig_time = px.histogram(
                        data.head(10000),  # 限制数据量以提高性能
                        x='发布时间',
                        title="发布时间分布",
                        nbins=50
                    )
                    fig_time.update_layout(height=400)
                    st.plotly_chart(fig_time, use_container_width=True)
                except:
                    st.info("发布时间数据格式需要处理")
            else:
                st.info("发布时间数据不可用")
        
        with col2:
            # 地理分布
            if '地理位置' in data.columns:
                location_counts = data['地理位置'].value_counts().head(10)
                fig_geo = px.bar(
                    x=location_counts.values,
                    y=location_counts.index,
                    orientation='h',
                    title="热门地理位置 (Top 10)"
                )
                fig_geo.update_layout(height=400)
                st.plotly_chart(fig_geo, use_container_width=True)
            elif '注册省份' in data.columns:
                province_counts = data['注册省份'].value_counts().head(10)
                fig_geo = px.bar(
                    x=province_counts.values,
                    y=province_counts.index,
                    orientation='h',
                    title="用户省份分布 (Top 10)"
                )
                fig_geo.update_layout(height=400)
                st.plotly_chart(fig_geo, use_container_width=True)
            else:
                st.info("地理位置数据不可用")
        
        # 性能监控
        st.subheader("⚡ 性能监控")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            memory_usage = data.memory_usage(deep=True).sum() / 1024**2
            st.metric("内存使用", f"{memory_usage:.1f} MB")
        
        with col2:
            processing_time = st.session_state.get('processing_time', 0)
            st.metric("处理时间", f"{processing_time:.2f} 秒")
        
        with col3:
            st.metric("缓存状态", "活跃")
        
        with col4:
            data_quality = (data.notna().sum().sum() / (len(data) * len(data.columns))) * 100
            st.metric("数据完整度", f"{data_quality:.1f}%")
        
        # 导出选项
        st.subheader("📤 数据导出")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("导出处理后数据"):
                csv = data.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="下载CSV文件",
                    data=csv,
                    file_name=f"processed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("导出统计报告"):
                report = data.describe(include='all').to_csv(encoding='utf-8-sig')
                st.download_button(
                    label="下载统计报告",
                    data=report,
                    file_name=f"statistics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col3:
            if st.button("导出字段信息"):
                col_info = pd.DataFrame({
                    '字段名': data.columns,
                    '数据类型': [str(dtype) for dtype in data.dtypes],
                    '非空值数量': [data[col].count() for col in data.columns],
                    '唯一值数量': [data[col].nunique() for col in data.columns]
                })
                col_report = col_info.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="下载字段报告",
                    data=col_report,
                    file_name=f"column_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    else:
        # 欢迎页面
        st.header("👋 欢迎使用用户行为分析平台")
        
        st.markdown("""
        ### 🎯 平台功能
        
        - **📊 大数据处理**: 支持500MB+数据的高效处理
        - **🔍 多维度分析**: 用户画像、地理行为、时间模式等
        - **📈 可视化展示**: 丰富的图表和交互式仪表板
        - **💾 智能缓存**: 自动缓存提升分析效率
        - **📤 数据导出**: 支持多种格式的结果导出
        
        ### 🚀 开始使用
        
        1. 在左侧面板选择数据模式和处理模式
        2. 点击"加载数据"按钮开始分析
        3. 等待数据处理完成后查看分析结果
        4. 使用左侧导航切换到不同的分析模块
        
        ### 💡 使用建议
        
        - **样本数据模式**: 适合快速预览和测试
        - **完整数据模式**: 适合正式分析，启用大数据优化
        - **高性能模式**: 适合高配置机器，处理速度更快
        - **内存优化模式**: 适合内存受限环境，降低内存占用
        
        ### 📋 分析模块
        
        - **👤 用户画像分析**: 用户基础属性、活跃度、影响力分析
        - **🌍 地理行为分析**: 地理分布、区域行为差异、热力图
        - **⏰ 时间行为分析**: 发布时间模式、用户活跃时段分析
        - **📝 内容行为分析**: 文本内容、话题挖掘、情感分析
        - **🕸️ 社交网络分析**: 用户互动、网络结构、影响力传播
        """)
        
        # 系统状态
        st.subheader("🖥️ 系统状态")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("💾 缓存系统: 就绪")
        
        with col2:
            st.info("🔧 处理引擎: 就绪")
        
        with col3:
            st.info("📊 可视化引擎: 就绪")

if __name__ == "__main__":
    main()
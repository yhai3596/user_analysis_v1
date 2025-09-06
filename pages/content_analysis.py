import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import jieba
import jieba.analyse
from collections import Counter
import re
import sys
import os
import platform
from pathlib import Path
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import seaborn as sns
from textstat import flesch_reading_ease
import warnings
warnings.filterwarnings('ignore')

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from utils.visualizer import UserBehaviorVisualizer, create_dashboard_metrics, display_metrics_cards
from utils.cache_manager import cache_data
from config.settings import get_config

# 页面配置
st.set_page_config(
    page_title="内容行为分析",
    page_icon="📝",
    layout="wide"
)

class ContentAnalyzer:
    """内容行为分析器"""
    
    def __init__(self):
        self.visualizer = UserBehaviorVisualizer()
        self.viz_config = get_config('viz')
        
        # 初始化jieba
        jieba.initialize()
        
        # 扩展的停用词列表
        self.stop_words = set([
            # 基础停用词
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '他', '她', '它', '们', '这个', '那个',
            # 疑问词
            '什么', '怎么', '为什么', '哪里', '哪个', '多少', '几个', '怎样', '如何', '哪些', '谁', '何时', '何地',
            # 数量词
            '第一', '第二', '第三', '一些', '很多', '许多', '大量', '少量', '全部', '部分', '所有',
            # 情态词
            '可以', '应该', '能够', '必须', '需要', '想要', '希望', '愿意', '打算', '准备',
            # 时间词
            '已经', '正在', '将要', '曾经', '从来', '总是', '经常', '有时', '偶尔', '从不',
            # 连接词
            '还是', '或者', '但是', '因为', '所以', '如果', '虽然', '然后', '接着', '于是', '因此', '然而', '不过', '而且', '并且', '以及',
            # 时间表达
            '现在', '以后', '以前', '今天', '明天', '昨天', '前天', '后天', '最近', '刚才', '马上', '立刻', '突然',
            # 程度词
            '非常', '特别', '十分', '相当', '比较', '更加', '最', '极其', '格外', '尤其', '特别是',
            # 方位词
            '这里', '那里', '哪里', '到处', '处处', '各处', '某处', '别处', '此处', '彼处',
            # 代词
            '我们', '你们', '他们', '她们', '它们', '大家', '别人', '其他', '另外', '各自', '彼此',
            # 标点和符号
            '，', '。', '！', '？', '；', '：', '"', "'", '（', '）', '【', '】', '《', '》',
            # 网络用语
            'http', 'https', 'www', 'com', 'cn', 'org', 'net', 'html', 'php', 'asp',
            # 无意义词汇
            '啊', '呀', '哦', '嗯', '哈', '呵', '嘿', '哟', '咦', '哇', '唉', '额', '呃', '嗯嗯', '哈哈',
            # 常见动词
            '做', '搞', '弄', '来', '走', '跑', '坐', '站', '躺', '睡', '吃', '喝', '买', '卖', '给', '拿', '放',
            # 常见形容词
            '大', '小', '高', '低', '长', '短', '新', '旧', '多', '少', '快', '慢', '早', '晚', '远', '近',
            # 其他常见词
            '东西', '事情', '问题', '方面', '情况', '时候', '地方', '方式', '方法', '结果', '原因', '目的', '意思', '内容', '方向'
        ])
    
    @cache_data(ttl=1800)
    def analyze_text_content(self, df: pd.DataFrame, text_column: str = '微博文本') -> dict:
        """分析文本内容"""
        analysis = {}
        
        if text_column not in df.columns:
            return analysis
        
        # 过滤空值和异常内容
        df_text = df[df[text_column].notna()].copy()
        if df_text.empty:
            return analysis
        
        # 数据清洗
        texts = df_text[text_column].astype(str)
        
        # 过滤异常内容
        import re
        cleaned_texts = []
        for text in texts:
            text = text.strip()
            # 过滤空白内容
            if not text or text.isspace():
                continue
            # 过滤只有空格的内容
            if len(text.replace(' ', '').replace('\t', '').replace('\n', '')) == 0:
                continue
            # 过滤过短内容（少于2个有效字符）
            if len(re.sub(r'\s+', '', text)) < 2:
                continue
            # 过滤包含大量数字或英文的异常内容
            if re.search(r'[0-9]{8,}', text) or re.search(r'[A-Za-z]{15,}', text):
                continue
            cleaned_texts.append(text)
        
        if not cleaned_texts:
            return analysis
            
        # 去重
        texts = pd.Series(cleaned_texts).drop_duplicates()
        
        # 基础统计
        analysis['basic_stats'] = {
            'total_posts': len(texts),
            'avg_length': texts.str.len().mean(),
            'median_length': texts.str.len().median(),
            'max_length': texts.str.len().max(),
            'min_length': texts.str.len().min(),
            'std_length': texts.str.len().std()
        }
        
        # 长度分布
        length_bins = [0, 50, 100, 200, 500, float('inf')]
        length_labels = ['短文本(≤50)', '中短文本(51-100)', '中等文本(101-200)', '长文本(201-500)', '超长文本(>500)']
        length_distribution = pd.cut(texts.str.len(), bins=length_bins, labels=length_labels, right=False)
        analysis['length_distribution'] = length_distribution.value_counts().to_dict()
        
        # 提取关键词
        all_text = ' '.join(texts)
        keywords = jieba.analyse.extract_tags(all_text, topK=50, withWeight=True)
        analysis['keywords'] = [(word, weight) for word, weight in keywords if word not in self.stop_words]
        
        # 词频统计 - 增强版
        words = []
        for text in texts:
            # 分词并过滤
            text_words = jieba.cut(text)
            filtered_words = [
                word.strip() for word in text_words 
                if len(word.strip()) >= 2  # 至少2个字符
                and word.strip() not in self.stop_words  # 不在停用词中
                and not word.strip().isdigit()  # 不是纯数字
                and not word.strip().isspace()  # 不是空白字符
                and word.strip()  # 不为空
            ]
            words.extend(filtered_words)
        
        word_freq = Counter(words)
        # 过滤低频词（出现次数少于2次的词）
        filtered_freq = {word: freq for word, freq in word_freq.items() if freq >= 2}
        analysis['word_frequency'] = dict(Counter(filtered_freq).most_common(50))
        
        # 情感词分析（简单版本）
        positive_words = ['好', '棒', '赞', '喜欢', '开心', '快乐', '满意', '优秀', '完美', '美好', '幸福', '成功']
        negative_words = ['差', '坏', '烂', '讨厌', '难过', '失望', '糟糕', '痛苦', '失败', '问题', '错误']
        
        positive_count = sum(text.count(word) for text in texts for word in positive_words)
        negative_count = sum(text.count(word) for text in texts for word in negative_words)
        
        analysis['sentiment_simple'] = {
            'positive_mentions': positive_count,
            'negative_mentions': negative_count,
            'sentiment_ratio': positive_count / (positive_count + negative_count + 1)
        }
        
        # 特殊字符和表情分析
        emoji_pattern = re.compile(r'[😀-🙏🌀-🗿🚀-🛿🇀-🇿]+', re.UNICODE)
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        mention_pattern = re.compile(r'@[\w\u4e00-\u9fff]+')
        hashtag_pattern = re.compile(r'#[^#]+#')
        
        emoji_count = sum(len(emoji_pattern.findall(text)) for text in texts)
        url_count = sum(len(url_pattern.findall(text)) for text in texts)
        mention_count = sum(len(mention_pattern.findall(text)) for text in texts)
        hashtag_count = sum(len(hashtag_pattern.findall(text)) for text in texts)
        
        analysis['special_elements'] = {
            'emoji_count': emoji_count,
            'url_count': url_count,
            'mention_count': mention_count,
            'hashtag_count': hashtag_count,
            'avg_emoji_per_post': emoji_count / len(texts),
            'posts_with_emoji': sum(1 for text in texts if emoji_pattern.search(text)),
            'posts_with_url': sum(1 for text in texts if url_pattern.search(text)),
            'posts_with_mention': sum(1 for text in texts if mention_pattern.search(text)),
            'posts_with_hashtag': sum(1 for text in texts if hashtag_pattern.search(text))
        }
        
        return analysis
    
    @cache_data(ttl=1800)
    def analyze_posting_sources(self, df: pd.DataFrame, source_column: str = '发布来源') -> dict:
        """分析发布来源"""
        analysis = {}
        
        if source_column not in df.columns:
            return analysis
        
        # 过滤空值
        df_source = df[df[source_column].notna()].copy()
        if df_source.empty:
            return analysis
        
        sources = df_source[source_column]
        
        # 来源分布
        source_counts = sources.value_counts()
        analysis['source_distribution'] = source_counts.to_dict()
        
        # 来源类型分类
        mobile_keywords = ['iPhone', 'Android', '手机', '移动', 'mobile', 'iOS']
        web_keywords = ['网页', 'web', '浏览器', 'PC', '电脑']
        app_keywords = ['客户端', 'APP', '应用']
        
        mobile_count = 0
        web_count = 0
        app_count = 0
        other_count = 0
        
        for source in sources:
            source_lower = str(source).lower()
            if any(keyword.lower() in source_lower for keyword in mobile_keywords):
                mobile_count += 1
            elif any(keyword.lower() in source_lower for keyword in web_keywords):
                web_count += 1
            elif any(keyword.lower() in source_lower for keyword in app_keywords):
                app_count += 1
            else:
                other_count += 1
        
        analysis['source_categories'] = {
            'mobile': mobile_count,
            'web': web_count,
            'app': app_count,
            'other': other_count
        }
        
        # 主要来源统计
        total_posts = len(sources)
        analysis['source_stats'] = {
            'total_sources': len(source_counts),
            'most_popular_source': source_counts.index[0] if len(source_counts) > 0 else None,
            'most_popular_count': source_counts.iloc[0] if len(source_counts) > 0 else 0,
            'most_popular_ratio': source_counts.iloc[0] / total_posts if len(source_counts) > 0 else 0,
            'source_diversity': len(source_counts) / total_posts  # 来源多样性
        }
        
        return analysis
    
    @cache_data(ttl=1800)
    def analyze_content_topics(self, df: pd.DataFrame, text_column: str = '微博文本') -> dict:
        """分析内容主题"""
        analysis = {}
        
        if text_column not in df.columns:
            return analysis
        
        # 过滤空值
        df_text = df[df[text_column].notna()].copy()
        if df_text.empty:
            return analysis
        
        texts = df_text[text_column].astype(str)
        
        # 主题关键词分类（简单版本）
        topic_keywords = {
            '生活日常': ['生活', '日常', '吃饭', '睡觉', '工作', '学习', '家', '朋友', '家人'],
            '情感表达': ['爱', '喜欢', '讨厌', '开心', '难过', '生气', '感动', '想念', '思念'],
            '娱乐休闲': ['电影', '音乐', '游戏', '旅游', '购物', '美食', '运动', '健身'],
            '社会热点': ['新闻', '政治', '经济', '社会', '热点', '事件', '讨论', '观点'],
            '科技数码': ['科技', '手机', '电脑', '软件', '网络', '互联网', 'AI', '技术'],
            '健康养生': ['健康', '养生', '医疗', '锻炼', '饮食', '营养', '保健', '身体'],
            '教育学习': ['学习', '教育', '知识', '技能', '课程', '考试', '读书', '成长'],
            '职场工作': ['工作', '职场', '同事', '老板', '项目', '会议', '加班', '升职']
        }
        
        topic_counts = {topic: 0 for topic in topic_keywords.keys()}
        topic_posts = {topic: [] for topic in topic_keywords.keys()}
        
        for idx, text in enumerate(texts):
            text_lower = text.lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    topic_counts[topic] += 1
                    topic_posts[topic].append(idx)
        
        analysis['topic_distribution'] = topic_counts
        analysis['topic_posts'] = topic_posts
        
        # 主题多样性
        total_classified = sum(topic_counts.values())
        unclassified = len(texts) - total_classified
        
        analysis['topic_stats'] = {
            'total_classified': total_classified,
            'unclassified': unclassified,
            'classification_rate': total_classified / len(texts),
            'most_popular_topic': max(topic_counts, key=topic_counts.get) if total_classified > 0 else None,
            'topic_diversity': len([count for count in topic_counts.values() if count > 0])
        }
        
        return analysis
    
    def is_cloud_environment(self):
        """检测是否在云环境中运行"""
        # 检测常见的云环境标识
        cloud_indicators = [
            'STREAMLIT_SHARING',  # Streamlit Cloud
            'HEROKU',             # Heroku
            'VERCEL',             # Vercel
            'NETLIFY',            # Netlify
            'AWS_LAMBDA_FUNCTION_NAME',  # AWS Lambda
            'GOOGLE_CLOUD_PROJECT',      # Google Cloud
        ]
        
        for indicator in cloud_indicators:
            if os.environ.get(indicator):
                return True
        
        # 检测是否在容器环境中
        if os.path.exists('/.dockerenv'):
            return True
            
        # 检测Streamlit Cloud特有路径
        if '/mount/src' in os.getcwd():
            return True
        
        # 检测是否为Windows本地环境
        if platform.system() == 'Windows':
            # Windows本地环境通常有这些特征
            if os.path.exists('C:/Windows'):
                return False
                
        return False
    
    def detect_chinese_font(self):
        """检测并返回可用的中文字体路径"""
        # 云环境也尝试检测字体
        is_cloud = self.is_cloud_environment()
        if is_cloud:
            # 云环境字体检测
            return self._detect_cloud_chinese_font()
    
    def _detect_cloud_chinese_font(self):
        """专门为云环境检测中文字体"""
        try:
            import matplotlib.font_manager as fm
            
            # 优先查找Noto字体（Google开源，云环境常见）
            noto_fonts = []
            for font in fm.fontManager.ttflist:
                font_name_lower = font.name.lower()
                if 'noto' in font_name_lower and ('cjk' in font_name_lower or 'sans' in font_name_lower):
                    noto_fonts.append((font.name, font.fname))
            
            if noto_fonts:
                font_name, font_path = noto_fonts[0]
                st.info(f"☁️ 云环境模式：找到Noto字体 {font_name}")
                return font_path
            
            # 查找其他可能的中文字体
            chinese_keywords = ['simhei', 'simsun', 'yahei', 'kai', 'song', 'hei', 'chinese', 'cjk', 'han', 'source', 'adobe']
            chinese_fonts = []
            for font in fm.fontManager.ttflist:
                font_name_lower = font.name.lower()
                if any(keyword in font_name_lower for keyword in chinese_keywords):
                    chinese_fonts.append((font.name, font.fname))
            
            if chinese_fonts:
                font_name, font_path = chinese_fonts[0]
                st.info(f"☁️ 云环境模式：找到中文字体 {font_name}")
                return font_path
            
            # 查找DejaVu字体作为备选
            dejavu_fonts = []
            for font in fm.fontManager.ttflist:
                if 'dejavu' in font.name.lower() and 'sans' in font.name.lower():
                    dejavu_fonts.append((font.name, font.fname))
            
            if dejavu_fonts:
                font_name, font_path = dejavu_fonts[0]
                st.warning(f"☁️ 云环境模式：未找到中文字体，使用 {font_name}（可能显示方块）")
                return font_path
            
            # 如果没有找到任何合适字体，返回None
            st.warning("☁️ 云环境字体检测失败，将使用默认配置")
            return None
            
        except Exception as e:
            st.warning(f"☁️ 云环境字体检测失败: {e}")
            return None
    
    def _try_download_cloud_font(self):
         """尝试为云环境下载中文字体"""
         try:
             import tempfile
             import urllib.request
             
             # 使用开源的TTF中文字体（更兼容wordcloud）
             font_urls = [
                 # 使用GitHub上的开源中文字体
                 'https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SimplifiedChinese/SourceHanSansSC-Regular.otf',
                 'https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf'
             ]
             
             # 创建临时目录
             temp_dir = tempfile.mkdtemp()
             
             for i, url in enumerate(font_urls):
                 try:
                     font_extension = url.split('.')[-1]
                     font_path = os.path.join(temp_dir, f'chinese_font_{i}.{font_extension}')
                     
                     # 设置超时和用户代理
                     req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                     with urllib.request.urlopen(req, timeout=30) as response:
                         with open(font_path, 'wb') as f:
                             f.write(response.read())
                     
                     # 检查文件是否下载成功
                     if os.path.exists(font_path) and os.path.getsize(font_path) > 1000:  # 至少1KB
                         return font_path
                         
                 except Exception as download_error:
                     st.warning(f"字体下载失败 {i+1}: {download_error}")
                     continue
             
             return None
             
         except Exception as e:
             st.warning(f"云环境字体下载功能失败: {e}")
             return None
    
    def detect_chinese_font(self):
        """检测可用的中文字体"""
        # 云环境优先使用专用检测
        if self.is_cloud_environment():
            cloud_font = self._detect_cloud_chinese_font()
            if cloud_font:
                return cloud_font
            
            # 云环境字体检测失败时的警告
            st.warning("云环境字体检测失败，将使用默认配置")
        
        # 本地环境字体检测
        # 常见中文字体路径
        font_paths = []
        
        # Windows系统字体路径
        if platform.system() == 'Windows':
            windows_fonts = [
                'C:/Windows/Fonts/simhei.ttf',  # 黑体
                'C:/Windows/Fonts/simsun.ttc',  # 宋体
                'C:/Windows/Fonts/msyh.ttc',    # 微软雅黑
                'C:/Windows/Fonts/simkai.ttf',  # 楷体
            ]
            font_paths.extend(windows_fonts)
        
        # macOS系统字体路径
        elif platform.system() == 'Darwin':
            mac_fonts = [
                '/System/Library/Fonts/PingFang.ttc',
                '/System/Library/Fonts/Hiragino Sans GB.ttc',
                '/Library/Fonts/Arial Unicode MS.ttf',
                '/System/Library/Fonts/STHeiti Light.ttc',
            ]
            font_paths.extend(mac_fonts)
        
        # Linux系统字体路径
        else:
            linux_fonts = [
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            ]
            font_paths.extend(linux_fonts)
        
        # 检查字体文件是否存在
        for font_path in font_paths:
            if os.path.exists(font_path):
                return font_path
        
        # 如果没有找到字体文件，返回None
        return None
    
    def create_wordcloud(self, word_freq: dict, max_words: int = 100) -> plt.Figure:
        """创建词云图"""
        if not word_freq:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontsize=20)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            return fig
        
        # 获取用户字体配置
        font_config = st.session_state.get('font_config', {
            'selected_font': 'SimHei',
            'font_size': 12
        })
        
        # 设置matplotlib中文字体支持
        try:
            # 使用用户选择的字体
            selected_font = font_config.get('selected_font', 'SimHei')
            plt.rcParams['font.sans-serif'] = [selected_font, 'SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            plt.rcParams['font.size'] = font_config.get('font_size', 12)
        except Exception as e:
            st.warning(f"字体设置警告: {e}")
        
        # 检测运行环境和字体
        is_cloud = self.is_cloud_environment()
        font_path = self.detect_chinese_font()
        
        # 创建词云
        try:
            # 云环境优化配置
            wordcloud_config = {
                'width': 800,
                'height': 400,
                'background_color': 'white',
                'max_words': max_words,
                'colormap': 'viridis',
                'prefer_horizontal': 0.9,
                'relative_scaling': 0.5,
                'collocations': False,
                'mode': 'RGBA'
            }
            
            # 根据环境调整配置
            if is_cloud:
                # 云环境使用更保守的配置
                wordcloud_config.update({
                    'max_font_size': 80,
                    'min_font_size': 10,
                    'font_step': 2
                })
                
                # 云环境字体配置 - 直接使用检测结果
                if font_path:
                    wordcloud_config['font_path'] = font_path
                else:
                    # 如果字体检测失败，尝试下载字体
                    cloud_font_path = self._try_download_cloud_font()
                    if cloud_font_path:
                        wordcloud_config['font_path'] = cloud_font_path
                        st.success("☁️ 云环境模式：成功下载中文字体")
                    else:
                        # 使用特殊的wordcloud配置来处理Unicode
                        wordcloud_config.update({
                             'font_step': 1,
                             'max_font_size': 60,
                             'min_font_size': 12,
                             'prefer_horizontal': 1.0,  # 强制水平显示
                             'relative_scaling': 0.3,
                             'mode': 'RGB'  # 改用RGB模式
                        })
                        st.warning("☁️ 云环境模式：使用优化配置，如仍显示方块请联系管理员")
                        
                        # 尝试设置matplotlib的字体回退
                        try:
                            plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
                            plt.rcParams['axes.unicode_minus'] = False
                        except:
                            pass
            else:
                # 本地环境可以使用更丰富的配置
                base_font_size = font_config.get('font_size', 12)
                wordcloud_config.update({
                    'font_step': 1,
                    'max_font_size': min(100, base_font_size * 8),
                    'min_font_size': max(8, base_font_size // 2)
                })
                
                # 尝试使用用户选择的字体
                selected_font = font_config.get('selected_font', 'SimHei')
                
                # 优先使用用户选择的字体对应的字体文件
                font_used = False
                
                # Windows系统字体映射
                if platform.system() == 'Windows':
                    font_mapping = {
                        'SimHei': 'C:/Windows/Fonts/simhei.ttf',
                        'SimSun': 'C:/Windows/Fonts/simsun.ttc',
                        'Microsoft YaHei': 'C:/Windows/Fonts/msyh.ttc',
                        'KaiTi': 'C:/Windows/Fonts/simkai.ttf'
                    }
                    
                    if selected_font in font_mapping:
                        font_file = font_mapping[selected_font]
                        if os.path.exists(font_file):
                            wordcloud_config['font_path'] = font_file
                            st.info(f"🎨 使用用户选择的字体: {selected_font}")
                            font_used = True
                
                # 如果用户选择的字体不可用，尝试使用检测到的字体
                if not font_used and font_path:
                    wordcloud_config['font_path'] = font_path
                    st.info(f"🎨 使用检测到的字体文件: {os.path.basename(font_path)}")
                    font_used = True
                
                # 最后尝试通过matplotlib查找字体
                if not font_used:
                    try:
                        import matplotlib.font_manager as fm
                        # 查找用户选择的字体
                        font_files = [f for f in fm.fontManager.ttflist if selected_font in f.name]
                        if font_files:
                            wordcloud_config['font_path'] = font_files[0].fname
                            st.info(f"🎨 通过matplotlib找到字体: {selected_font}")
                            font_used = True
                    except Exception as font_error:
                        st.warning(f"字体检测失败: {font_error}")
                
                if not font_used:
                    st.warning(f"🎨 字体 {selected_font} 不可用，词云可能显示为方块")
                    st.info("💡 建议在侧边栏选择其他可用字体")
            
            wordcloud = WordCloud(**wordcloud_config).generate_from_frequencies(word_freq)
            
        except Exception as e:
            # 如果出现任何问题，使用最简配置
            try:
                st.warning(f"词云生成遇到问题，尝试简化配置: {str(e)}")
                simple_config = {
                    'width': 800,
                    'height': 400,
                    'background_color': 'white',
                    'max_words': max_words,
                    'mode': 'RGBA',
                    'max_font_size': 80,
                    'min_font_size': 10
                }
                
                if font_path:
                    simple_config['font_path'] = font_path
                
                wordcloud = WordCloud(**simple_config).generate_from_frequencies(word_freq)
                
            except Exception as e2:
                st.error(f"词云生成失败: {str(e2)}")
                st.info("💡 提示：这可能是云环境的字体或图像处理问题")
                # 显示字体检测信息
                st.info(f"🔍 系统类型: {platform.system()}")
                st.info(f"🔍 检测到的字体: {font_path or '无'}")
                return None
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        
        # 设置标题，确保中文显示正确
        try:
            selected_font = font_config.get('selected_font', 'SimHei')
            title_fontsize = max(14, font_config.get('font_size', 12) + 4)
            ax.set_title('词云图', fontsize=title_fontsize, pad=20, fontproperties=selected_font)
        except:
            # 如果用户选择的字体不可用，使用默认设置
            title_fontsize = max(14, font_config.get('font_size', 12) + 4)
            ax.set_title('词云图', fontsize=title_fontsize, pad=20)
        
        return fig

def main():
    """主函数"""
    st.title("📝 内容行为分析")
    
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
    
    analyzer = ContentAnalyzer()
    
    # 侧边栏控制
    st.sidebar.subheader("📝 分析选项")
    
    analysis_type = st.sidebar.selectbox(
        "选择分析类型",
        ["文本内容分析", "发布来源分析", "内容主题分析", "词云分析", "综合内容报告"]
    )
    
    # 选择文本列
    text_columns = [col for col in df.columns if df[col].dtype == 'object' and ('内容' in col or '文本' in col)]
    if not text_columns:
        text_columns = [col for col in df.columns if df[col].dtype == 'object']
    
    if text_columns:
        text_column = st.sidebar.selectbox("选择文本字段", text_columns, index=0)
    else:
        st.error("❌ 数据中没有找到文本字段")
        st.stop()
    
    # 数据概览
    st.subheader("📈 数据概览")
    metrics = create_dashboard_metrics(df)
    display_metrics_cards(metrics)
    
    # 根据选择的分析类型显示内容
    if analysis_type == "文本内容分析":
        show_text_content_analysis(df, analyzer, text_column)
    elif analysis_type == "发布来源分析":
        show_posting_source_analysis(df, analyzer)
    elif analysis_type == "内容主题分析":
        show_content_topic_analysis(df, analyzer, text_column)
    elif analysis_type == "词云分析":
        show_wordcloud_analysis(df, analyzer, text_column)
    elif analysis_type == "综合内容报告":
        show_comprehensive_content_report(df, analyzer, text_column)

def show_text_content_analysis(df: pd.DataFrame, analyzer: ContentAnalyzer, text_column: str):
    """显示文本内容分析"""
    st.subheader("📊 文本内容分析")
    
    # 分析文本内容
    content_analysis = analyzer.analyze_text_content(df, text_column)
    
    if not content_analysis:
        st.warning(f"无法分析文本内容，请检查{text_column}字段")
        return
    
    # 基础统计
    if 'basic_stats' in content_analysis:
        st.subheader("📏 文本长度统计")
        
        stats = content_analysis['basic_stats']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总发布数", stats['total_posts'])
        with col2:
            st.metric("平均长度", f"{stats['avg_length']:.1f}字")
        with col3:
            st.metric("最大长度", f"{stats['max_length']}字")
        with col4:
            st.metric("最小长度", f"{stats['min_length']}字")
        
        # 长度分布
        if 'length_distribution' in content_analysis:
            st.write("**文本长度分布**")
            length_dist = content_analysis['length_distribution']
            
            fig_length = go.Figure(data=[
                go.Bar(
                    x=list(length_dist.keys()),
                    y=list(length_dist.values()),
                    marker_color=analyzer.visualizer.color_palette[0],
                    text=list(length_dist.values()),
                    textposition='auto'
                )
            ])
            fig_length.update_layout(
                title="文本长度分布",
                xaxis_title="长度类别",
                yaxis_title="数量"
            )
            st.plotly_chart(fig_length, use_container_width=True)
    
    # 关键词分析
    if 'keywords' in content_analysis:
        st.subheader("🔑 关键词分析")
        
        keywords = content_analysis['keywords'][:20]  # 取前20个关键词
        
        if keywords:
            col1, col2 = st.columns(2)
            
            with col1:
                # 关键词权重图
                words, weights = zip(*keywords)
                
                fig_keywords = go.Figure(data=[
                    go.Bar(
                        x=list(weights),
                        y=list(words),
                        orientation='h',
                        marker_color=analyzer.visualizer.color_palette[1],
                        text=[f"{w:.3f}" for w in weights],
                        textposition='auto'
                    )
                ])
                fig_keywords.update_layout(
                    title="关键词权重排行",
                    xaxis_title="权重",
                    yaxis_title="关键词",
                    height=500
                )
                st.plotly_chart(fig_keywords, use_container_width=True)
            
            with col2:
                # 关键词表格
                st.write("**关键词详情**")
                keywords_df = pd.DataFrame(keywords, columns=['关键词', '权重'])
                keywords_df['权重'] = keywords_df['权重'].round(4)
                st.dataframe(keywords_df, use_container_width=True)
    
    # 词频统计
    if 'word_frequency' in content_analysis:
        st.subheader("📈 高频词汇")
        
        word_freq = content_analysis['word_frequency']
        
        if word_freq:
            # 词频柱状图
            words = list(word_freq.keys())[:15]  # 取前15个
            freqs = [word_freq[word] for word in words]
            
            fig_freq = go.Figure(data=[
                go.Bar(
                    x=words,
                    y=freqs,
                    marker_color=analyzer.visualizer.color_palette[2],
                    text=freqs,
                    textposition='auto'
                )
            ])
            fig_freq.update_layout(
                title="高频词汇统计",
                xaxis_title="词汇",
                yaxis_title="频次"
            )
            st.plotly_chart(fig_freq, use_container_width=True)
    
    # 情感分析
    if 'sentiment_simple' in content_analysis:
        st.subheader("😊 简单情感分析")
        
        sentiment = content_analysis['sentiment_simple']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("积极词汇提及", sentiment['positive_mentions'])
        with col2:
            st.metric("消极词汇提及", sentiment['negative_mentions'])
        with col3:
            st.metric("情感倾向比例", f"{sentiment['sentiment_ratio']:.2f}")
        
        # 情感分布饼图
        sentiment_data = {
            '积极': sentiment['positive_mentions'],
            '消极': sentiment['negative_mentions'],
            '中性': max(0, content_analysis['basic_stats']['total_posts'] - sentiment['positive_mentions'] - sentiment['negative_mentions'])
        }
        
        fig_sentiment = go.Figure(data=[
            go.Pie(
                labels=list(sentiment_data.keys()),
                values=list(sentiment_data.values()),
                hole=0.3
            )
        ])
        fig_sentiment.update_layout(title="情感分布")
        st.plotly_chart(fig_sentiment, use_container_width=True)
    
    # 特殊元素分析
    if 'special_elements' in content_analysis:
        st.subheader("🎯 特殊元素分析")
        
        special = content_analysis['special_elements']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("表情符号", special['emoji_count'])
        with col2:
            st.metric("链接数量", special['url_count'])
        with col3:
            st.metric("@提及", special['mention_count'])
        with col4:
            st.metric("话题标签", special['hashtag_count'])
        
        # 特殊元素使用率
        total_posts = content_analysis['basic_stats']['total_posts']
        usage_rates = {
            '表情符号使用率': special['posts_with_emoji'] / total_posts * 100,
            '链接使用率': special['posts_with_url'] / total_posts * 100,
            '@提及使用率': special['posts_with_mention'] / total_posts * 100,
            '话题标签使用率': special['posts_with_hashtag'] / total_posts * 100
        }
        
        fig_usage = go.Figure(data=[
            go.Bar(
                x=list(usage_rates.keys()),
                y=list(usage_rates.values()),
                marker_color=analyzer.visualizer.color_palette[3],
                text=[f"{rate:.1f}%" for rate in usage_rates.values()],
                textposition='auto'
            )
        ])
        fig_usage.update_layout(
            title="特殊元素使用率",
            xaxis_title="元素类型",
            yaxis_title="使用率(%)"
        )
        st.plotly_chart(fig_usage, use_container_width=True)

def show_posting_source_analysis(df: pd.DataFrame, analyzer: ContentAnalyzer):
    """显示发布来源分析"""
    st.subheader("📱 发布来源分析")
    
    # 检查是否有发布来源字段
    source_columns = [col for col in df.columns if '来源' in col or 'source' in col.lower()]
    
    if not source_columns:
        st.warning("❌ 数据中没有找到发布来源字段")
        return
    
    source_column = source_columns[0]
    
    # 分析发布来源
    source_analysis = analyzer.analyze_posting_sources(df, source_column)
    
    if not source_analysis:
        st.warning(f"无法分析发布来源，请检查{source_column}字段")
        return
    
    # 来源统计
    if 'source_stats' in source_analysis:
        st.subheader("📊 来源统计概览")
        
        stats = source_analysis['source_stats']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("来源总数", stats['total_sources'])
        with col2:
            st.metric("最主要来源", stats['most_popular_source'] or "未知")
        with col3:
            st.metric("主要来源占比", f"{stats['most_popular_ratio']*100:.1f}%")
        with col4:
            st.metric("来源多样性", f"{stats['source_diversity']:.3f}")
    
    # 来源分布
    if 'source_distribution' in source_analysis:
        st.subheader("📈 来源分布")
        
        source_dist = source_analysis['source_distribution']
        
        # 取前10个来源
        top_sources = dict(list(source_dist.items())[:10])
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 来源柱状图
            fig_source = go.Figure(data=[
                go.Bar(
                    x=list(top_sources.values()),
                    y=list(top_sources.keys()),
                    orientation='h',
                    marker_color=analyzer.visualizer.color_palette[0],
                    text=list(top_sources.values()),
                    textposition='auto'
                )
            ])
            fig_source.update_layout(
                title="主要发布来源(前10)",
                xaxis_title="发布数量",
                yaxis_title="来源",
                height=400
            )
            st.plotly_chart(fig_source, use_container_width=True)
        
        with col2:
            # 来源饼图
            # 合并小来源
            other_count = sum(list(source_dist.values())[5:])
            pie_data = dict(list(source_dist.items())[:5])
            if other_count > 0:
                pie_data['其他'] = other_count
            
            fig_pie = go.Figure(data=[
                go.Pie(
                    labels=list(pie_data.keys()),
                    values=list(pie_data.values()),
                    hole=0.3
                )
            ])
            fig_pie.update_layout(title="来源分布占比")
            st.plotly_chart(fig_pie, use_container_width=True)
    
    # 来源类型分析
    if 'source_categories' in source_analysis:
        st.subheader("📱 来源类型分析")
        
        categories = source_analysis['source_categories']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("移动端", categories['mobile'])
        with col2:
            st.metric("网页端", categories['web'])
        with col3:
            st.metric("应用端", categories['app'])
        with col4:
            st.metric("其他", categories['other'])
        
        # 类型分布图
        category_labels = ['移动端', '网页端', '应用端', '其他']
        category_values = [categories['mobile'], categories['web'], categories['app'], categories['other']]
        
        fig_category = go.Figure(data=[
            go.Bar(
                x=category_labels,
                y=category_values,
                marker_color=analyzer.visualizer.color_palette[:4],
                text=category_values,
                textposition='auto'
            )
        ])
        fig_category.update_layout(
            title="发布来源类型分布",
            xaxis_title="来源类型",
            yaxis_title="发布数量"
        )
        st.plotly_chart(fig_category, use_container_width=True)
        
        # 移动端占比分析
        total_posts = sum(category_values)
        if total_posts > 0:
            mobile_ratio = categories['mobile'] / total_posts * 100
            if mobile_ratio > 70:
                st.success(f"📱 移动端发布占主导地位({mobile_ratio:.1f}%)")
            elif mobile_ratio > 40:
                st.info(f"📊 移动端和其他端并重({mobile_ratio:.1f}%)")
            else:
                st.warning(f"💻 非移动端发布较多({mobile_ratio:.1f}%)")

def show_content_topic_analysis(df: pd.DataFrame, analyzer: ContentAnalyzer, text_column: str):
    """显示内容主题分析"""
    st.subheader("🏷️ 内容主题分析")
    
    # 分析内容主题
    topic_analysis = analyzer.analyze_content_topics(df, text_column)
    
    if not topic_analysis:
        st.warning(f"无法分析内容主题，请检查{text_column}字段")
        return
    
    # 主题统计
    if 'topic_stats' in topic_analysis:
        st.subheader("📊 主题统计概览")
        
        stats = topic_analysis['topic_stats']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("已分类内容", stats['total_classified'])
        with col2:
            st.metric("未分类内容", stats['unclassified'])
        with col3:
            st.metric("分类覆盖率", f"{stats['classification_rate']*100:.1f}%")
        with col4:
            st.metric("主题多样性", stats['topic_diversity'])
        
        if stats['most_popular_topic']:
            st.info(f"🏆 最热门主题：{stats['most_popular_topic']}")
    
    # 主题分布
    if 'topic_distribution' in topic_analysis:
        st.subheader("📈 主题分布")
        
        topic_dist = topic_analysis['topic_distribution']
        
        # 过滤掉计数为0的主题
        active_topics = {k: v for k, v in topic_dist.items() if v > 0}
        
        if active_topics:
            col1, col2 = st.columns(2)
            
            with col1:
                # 主题柱状图
                fig_topic = go.Figure(data=[
                    go.Bar(
                        x=list(active_topics.keys()),
                        y=list(active_topics.values()),
                        marker_color=analyzer.visualizer.color_palette[0],
                        text=list(active_topics.values()),
                        textposition='auto'
                    )
                ])
                fig_topic.update_layout(
                    title="主题分布",
                    xaxis_title="主题",
                    yaxis_title="内容数量",
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig_topic, use_container_width=True)
            
            with col2:
                # 主题饼图
                fig_topic_pie = go.Figure(data=[
                    go.Pie(
                        labels=list(active_topics.keys()),
                        values=list(active_topics.values()),
                        hole=0.3
                    )
                ])
                fig_topic_pie.update_layout(title="主题占比分布")
                st.plotly_chart(fig_topic_pie, use_container_width=True)
            
            # 主题详情表格
            st.subheader("📋 主题详情")
            
            topic_details = []
            total_classified = sum(active_topics.values())
            
            for topic, count in active_topics.items():
                percentage = count / total_classified * 100 if total_classified > 0 else 0
                topic_details.append({
                    '主题': topic,
                    '内容数量': count,
                    '占比(%)': f"{percentage:.1f}%"
                })
            
            topic_df = pd.DataFrame(topic_details)
            topic_df = topic_df.sort_values('内容数量', ascending=False)
            st.dataframe(topic_df, use_container_width=True)
        else:
            st.warning("⚠️ 没有检测到明确的主题分类")

def show_wordcloud_analysis(df: pd.DataFrame, analyzer: ContentAnalyzer, text_column: str):
    """显示词云分析"""
    st.subheader("☁️ 词云分析")
    
    # 分析文本内容获取词频
    content_analysis = analyzer.analyze_text_content(df, text_column)
    
    if not content_analysis or 'word_frequency' not in content_analysis:
        st.warning(f"无法生成词云，请检查{text_column}字段")
        return
    
    word_freq = content_analysis['word_frequency']
    
    if not word_freq:
        st.warning("没有足够的词汇数据生成词云")
        return
    
    # 词云参数设置
    st.subheader("⚙️ 词云设置")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        max_words = st.slider("最大词汇数", 20, 200, 100)
    with col2:
        min_freq = st.slider("最小词频", 1, 10, 2)
    with col3:
        min_word_len = st.slider("最小词长", 2, 5, 2)
    
    # 高级过滤选项
    with st.expander("🔧 高级过滤选项", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            filter_numbers = st.checkbox("过滤纯数字", value=True)
            filter_english = st.checkbox("过滤纯英文", value=False)
        with col2:
            filter_single_char = st.checkbox("过滤单字符", value=True)
            custom_stopwords = st.text_area("自定义停用词（用逗号分隔）", placeholder="例如：微博,转发,评论")
    
    # 应用高级过滤选项
    additional_stopwords = set()
    if custom_stopwords:
        additional_stopwords = set([word.strip() for word in custom_stopwords.split(',') if word.strip()])
    
    # 过滤词频
    filtered_word_freq = {}
    for word, freq in word_freq.items():
        # 基础频率过滤
        if freq < min_freq:
            continue
        
        # 词长过滤
        if len(word) < min_word_len:
            continue
            
        # 自定义停用词过滤
        if word in additional_stopwords:
            continue
            
        # 数字过滤
        if filter_numbers and word.isdigit():
            continue
            
        # 英文过滤
        if filter_english and word.isascii() and word.isalpha():
            continue
            
        # 单字符过滤
        if filter_single_char and len(word) == 1:
            continue
            
        filtered_word_freq[word] = freq
    
    if not filtered_word_freq:
        st.warning(f"应用过滤条件后没有符合要求的词汇")
        return
    
    # 生成词云
    st.subheader("☁️ 词云图")
    
    try:
        # 使用matplotlib生成词云
        wordcloud_fig = analyzer.create_wordcloud(filtered_word_freq, max_words)
        st.pyplot(wordcloud_fig)
        
        # 词频统计表
        st.subheader("📊 词频统计")
        
        # 显示前20个高频词
        top_words = dict(list(filtered_word_freq.items())[:20])
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 词频柱状图
            fig_freq = go.Figure(data=[
                go.Bar(
                    x=list(top_words.keys()),
                    y=list(top_words.values()),
                    marker_color=analyzer.visualizer.color_palette[0],
                    text=list(top_words.values()),
                    textposition='auto'
                )
            ])
            fig_freq.update_layout(
                title="高频词汇(前20)",
                xaxis_title="词汇",
                yaxis_title="频次",
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig_freq, use_container_width=True)
        
        with col2:
            # 词频表格
            freq_data = []
            for word, freq in list(filtered_word_freq.items())[:20]:
                freq_data.append({'词汇': word, '频次': freq})
            
            freq_df = pd.DataFrame(freq_data)
            st.dataframe(freq_df, use_container_width=True)
        
        # 词汇洞察
        st.subheader("💡 词汇洞察")
        
        total_words = sum(filtered_word_freq.values())
        unique_words = len(filtered_word_freq)
        most_freq_word = max(filtered_word_freq, key=filtered_word_freq.get)
        most_freq_count = filtered_word_freq[most_freq_word]
        
        insights = [
            f"📝 共识别出{unique_words}个不同词汇，总词频{total_words}",
            f"🏆 最高频词汇：'{most_freq_word}'，出现{most_freq_count}次",
            f"📊 词汇多样性：平均每个词汇出现{total_words/unique_words:.1f}次",
            f"🎯 词云展示了用户内容的主要关注点和话题倾向"
        ]
        
        for insight in insights:
            st.info(insight)
    
    except Exception as e:
        st.error(f"生成词云时出错：{str(e)}")
        st.info("💡 提示：如果是字体问题，请确保系统中有中文字体文件")

def show_comprehensive_content_report(df: pd.DataFrame, analyzer: ContentAnalyzer, text_column: str):
    """显示综合内容报告"""
    st.subheader("📋 综合内容行为报告")
    
    # 获取所有分析结果
    content_analysis = analyzer.analyze_text_content(df, text_column)
    topic_analysis = analyzer.analyze_content_topics(df, text_column)
    
    # 检查发布来源
    source_columns = [col for col in df.columns if '来源' in col or 'source' in col.lower()]
    source_analysis = {}
    if source_columns:
        source_analysis = analyzer.analyze_posting_sources(df, source_columns[0])
    
    # 关键指标概览
    st.subheader("📊 关键指标概览")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if content_analysis and 'basic_stats' in content_analysis:
            avg_length = content_analysis['basic_stats']['avg_length']
            st.metric("平均文本长度", f"{avg_length:.0f}字")
    
    with col2:
        if content_analysis and 'special_elements' in content_analysis:
            emoji_rate = content_analysis['special_elements']['avg_emoji_per_post']
            st.metric("平均表情使用", f"{emoji_rate:.1f}个/条")
    
    with col3:
        if topic_analysis and 'topic_stats' in topic_analysis:
            classification_rate = topic_analysis['topic_stats']['classification_rate']
            st.metric("主题分类覆盖率", f"{classification_rate*100:.1f}%")
    
    with col4:
        if source_analysis and 'source_stats' in source_analysis:
            source_diversity = source_analysis['source_stats']['source_diversity']
            st.metric("发布来源多样性", f"{source_diversity:.3f}")
    
    # 内容特征总结
    st.subheader("📝 内容特征总结")
    
    content_insights = []
    
    # 文本长度特征
    if content_analysis and 'basic_stats' in content_analysis:
        stats = content_analysis['basic_stats']
        avg_length = stats['avg_length']
        
        if avg_length > 200:
            content_insights.append(f"📏 用户倾向于发布长文本内容，平均{avg_length:.0f}字")
        elif avg_length > 100:
            content_insights.append(f"📄 用户发布中等长度内容，平均{avg_length:.0f}字")
        else:
            content_insights.append(f"📝 用户倾向于发布简短内容，平均{avg_length:.0f}字")
    
    # 情感特征
    if content_analysis and 'sentiment_simple' in content_analysis:
        sentiment = content_analysis['sentiment_simple']
        sentiment_ratio = sentiment['sentiment_ratio']
        
        if sentiment_ratio > 0.6:
            content_insights.append("😊 内容整体情感倾向积极正面")
        elif sentiment_ratio > 0.4:
            content_insights.append("😐 内容情感倾向相对中性")
        else:
            content_insights.append("😔 内容中消极情感表达较多")
    
    # 特殊元素使用
    if content_analysis and 'special_elements' in content_analysis:
        special = content_analysis['special_elements']
        total_posts = content_analysis['basic_stats']['total_posts']
        
        emoji_usage = special['posts_with_emoji'] / total_posts
        if emoji_usage > 0.5:
            content_insights.append(f"😀 用户频繁使用表情符号({emoji_usage*100:.1f}%的内容包含表情)")
        
        url_usage = special['posts_with_url'] / total_posts
        if url_usage > 0.2:
            content_insights.append(f"🔗 用户经常分享链接内容({url_usage*100:.1f}%的内容包含链接)")
        
        mention_usage = special['posts_with_mention'] / total_posts
        if mention_usage > 0.3:
            content_insights.append(f"👥 用户互动性较强({mention_usage*100:.1f}%的内容包含@提及)")
    
    # 主题特征
    if topic_analysis and 'topic_distribution' in topic_analysis:
        topic_dist = topic_analysis['topic_distribution']
        active_topics = {k: v for k, v in topic_dist.items() if v > 0}
        
        if active_topics:
            most_popular_topic = max(active_topics, key=active_topics.get)
            topic_count = active_topics[most_popular_topic]
            total_classified = sum(active_topics.values())
            topic_ratio = topic_count / total_classified if total_classified > 0 else 0
            
            content_insights.append(f"🏷️ 用户最关注'{most_popular_topic}'主题({topic_ratio*100:.1f}%)")
            
            if len(active_topics) > 5:
                content_insights.append(f"🌈 用户内容主题多样化，涉及{len(active_topics)}个不同领域")
    
    # 发布来源特征
    if source_analysis and 'source_categories' in source_analysis:
        categories = source_analysis['source_categories']
        total_posts = sum(categories.values())
        
        if total_posts > 0:
            mobile_ratio = categories['mobile'] / total_posts
            if mobile_ratio > 0.7:
                content_insights.append(f"📱 用户主要通过移动设备发布内容({mobile_ratio*100:.1f}%)")
            elif mobile_ratio > 0.4:
                content_insights.append(f"📊 用户在移动端和其他端发布内容较为均衡")
            else:
                content_insights.append(f"💻 用户更多通过非移动端发布内容")
    
    for insight in content_insights:
        st.info(insight)
    
    # 内容质量评估
    st.subheader("⭐ 内容质量评估")
    
    quality_scores = {}
    
    # 长度质量评分
    if content_analysis and 'basic_stats' in content_analysis:
        avg_length = content_analysis['basic_stats']['avg_length']
        if 50 <= avg_length <= 300:
            quality_scores['长度适中'] = 85
        elif avg_length > 300:
            quality_scores['长度适中'] = 70
        else:
            quality_scores['长度适中'] = 60
    
    # 多样性评分
    if content_analysis and 'word_frequency' in content_analysis:
        word_freq = content_analysis['word_frequency']
        unique_words = len(word_freq)
        total_words = sum(word_freq.values())
        diversity_ratio = unique_words / total_words if total_words > 0 else 0
        
        if diversity_ratio > 0.3:
            quality_scores['词汇多样性'] = 90
        elif diversity_ratio > 0.2:
            quality_scores['词汇多样性'] = 75
        else:
            quality_scores['词汇多样性'] = 60
    
    # 互动性评分
    if content_analysis and 'special_elements' in content_analysis:
        special = content_analysis['special_elements']
        total_posts = content_analysis['basic_stats']['total_posts']
        
        interaction_elements = (
            special['posts_with_mention'] + 
            special['posts_with_hashtag'] + 
            special['posts_with_emoji']
        ) / (total_posts * 3)  # 标准化到0-1
        
        if interaction_elements > 0.4:
            quality_scores['互动性'] = 85
        elif interaction_elements > 0.2:
            quality_scores['互动性'] = 70
        else:
            quality_scores['互动性'] = 55
    
    # 主题聚焦度评分
    if topic_analysis and 'topic_stats' in topic_analysis:
        classification_rate = topic_analysis['topic_stats']['classification_rate']
        
        if classification_rate > 0.7:
            quality_scores['主题聚焦度'] = 80
        elif classification_rate > 0.5:
            quality_scores['主题聚焦度'] = 65
        else:
            quality_scores['主题聚焦度'] = 50
    
    if quality_scores:
        # 质量评分可视化
        fig_quality = go.Figure(data=[
            go.Bar(
                x=list(quality_scores.keys()),
                y=list(quality_scores.values()),
                marker_color=analyzer.visualizer.color_palette[0],
                text=[f"{score}分" for score in quality_scores.values()],
                textposition='auto'
            )
        ])
        fig_quality.update_layout(
            title="内容质量评估",
            xaxis_title="评估维度",
            yaxis_title="得分",
            yaxis=dict(range=[0, 100])
        )
        st.plotly_chart(fig_quality, use_container_width=True)
        
        # 总体质量评分
        overall_score = sum(quality_scores.values()) / len(quality_scores)
        
        if overall_score >= 80:
            st.success(f"🌟 内容质量优秀，总体得分：{overall_score:.1f}分")
        elif overall_score >= 70:
            st.info(f"👍 内容质量良好，总体得分：{overall_score:.1f}分")
        elif overall_score >= 60:
            st.warning(f"⚠️ 内容质量一般，总体得分：{overall_score:.1f}分")
        else:
            st.error(f"📉 内容质量需要改进，总体得分：{overall_score:.1f}分")
    
    # 优化建议
    st.subheader("💡 内容优化建议")
    
    recommendations = []
    
    # 基于分析结果给出建议
    if content_analysis and 'basic_stats' in content_analysis:
        avg_length = content_analysis['basic_stats']['avg_length']
        if avg_length < 50:
            recommendations.append("📏 **增加内容长度**：适当增加内容的详细程度和深度")
        elif avg_length > 500:
            recommendations.append("✂️ **精简内容**：考虑将长内容分段或提炼重点")
    
    if content_analysis and 'special_elements' in content_analysis:
        special = content_analysis['special_elements']
        total_posts = content_analysis['basic_stats']['total_posts']
        
        if special['posts_with_emoji'] / total_posts < 0.3:
            recommendations.append("😊 **增加表情使用**：适当使用表情符号增加内容亲和力")
        
        if special['posts_with_hashtag'] / total_posts < 0.2:
            recommendations.append("🏷️ **使用话题标签**：添加相关话题标签提高内容可发现性")
    
    if topic_analysis and 'topic_stats' in topic_analysis:
        classification_rate = topic_analysis['topic_stats']['classification_rate']
        if classification_rate < 0.5:
            recommendations.append("🎯 **明确内容主题**：让内容主题更加明确和聚焦")
    
    # 通用建议
    general_recommendations = [
        "📅 **定期发布**：保持稳定的内容发布频率",
        "👥 **增强互动**：多与其他用户进行互动和交流",
        "📊 **数据驱动**：根据数据分析结果调整内容策略",
        "🔄 **持续优化**：定期回顾和优化内容质量"
    ]
    
    all_recommendations = recommendations + general_recommendations
    
    for recommendation in all_recommendations:
        st.markdown(recommendation)
    
    # 数据说明
    st.subheader("ℹ️ 分析说明")
    
    analysis_notes = [
        f"📝 分析基于{len(df)}条内容记录",
        "🔤 文本分析采用中文分词和关键词提取技术",
        "🏷️ 主题分类基于关键词匹配方法",
        "😊 情感分析采用简单词典匹配方法",
        "⚠️ 分析结果仅供参考，实际应用需结合具体业务场景"
    ]
    
    for note in analysis_notes:
        st.caption(note)

if __name__ == "__main__":
    main()
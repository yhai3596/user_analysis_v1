# 用户行为分析系统

一个基于 Streamlit 的用户行为数据分析平台，提供全面的用户画像分析、地理行为分析、时间模式分析、内容分析和社交网络分析功能。

## 🌟 功能特性

### 核心分析模块

- **📊 用户画像分析**：基础属性分析、活跃度评估、影响力分析
- **🗺️ 地理行为分析**：热力图展示、轨迹分析、区域偏好分析
- **⏰ 时间行为分析**：发布时间模式、活跃时段分析、时间序列趋势
- **📝 内容行为分析**：文本分析、话题挖掘、情感分析
- **🔗 社交网络分析**：互动模式分析、影响力传播、网络结构分析

### 技术特性

- **🚀 高性能数据处理**：支持大数据量分块加载和内存优化
- **💾 智能缓存系统**：自动缓存计算结果，提升响应速度
- **📱 响应式界面**：现代化的 Web 界面，支持多设备访问
- **🔧 灵活配置**：支持多种数据格式和处理模式

## 🚀 快速开始

### 本地运行

1. **克隆项目**
   ```bash
   git clone https://github.com/your-username/user-behavior-analysis.git
   cd user-behavior-analysis
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **生成示例数据**（可选）
   ```bash
   python generate_sample_data.py
   ```

4. **启动应用**
   ```bash
   streamlit run app.py
   ```

5. **访问应用**
   
   在浏览器中打开 `http://localhost:8501`

### 在线部署

本项目已优化支持 Streamlit Community Cloud 部署。详细部署指南请参考 [DEPLOYMENT.md](DEPLOYMENT.md)。

**一键部署到 Streamlit Cloud：**

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

## 📁 项目结构

```
用户数据分析/
├── app.py                      # 主应用文件
├── requirements.txt            # 依赖包列表
├── generate_sample_data.py     # 示例数据生成脚本
├── 切片.xlsx                   # 示例数据文件
├── DEPLOYMENT.md              # 部署指南
├── README.md                  # 项目说明
├── .gitignore                 # Git 忽略文件
├── config/
│   └── settings.py            # 配置文件
├── utils/
│   ├── data_loader.py         # 数据加载工具
│   ├── cache_manager.py       # 缓存管理
│   └── visualizer.py          # 可视化工具
├── pages/
│   ├── user_profile.py        # 用户画像分析
│   ├── geo_analysis.py        # 地理行为分析
│   ├── time_analysis.py       # 时间行为分析
│   ├── content_analysis.py    # 内容行为分析
│   └── social_network.py      # 社交网络分析
└── cache/                     # 缓存目录
```

## 📊 数据格式

### 支持的数据格式

- **Excel 文件** (`.xlsx`, `.xls`)
- **CSV 文件** (`.csv`)

### 数据字段要求

| 字段名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| 用户ID | 字符串 | ✅ | 唯一用户标识 |
| 发布时间 | 日期时间 | ✅ | 内容发布时间 |
| 城市 | 字符串 | ❌ | 用户所在城市 |
| 经度 | 数值 | ❌ | 地理位置经度 |
| 纬度 | 数值 | ❌ | 地理位置纬度 |
| 内容类型 | 字符串 | ❌ | 内容类型分类 |
| 点赞数 | 整数 | ❌ | 内容点赞数量 |
| 评论数 | 整数 | ❌ | 内容评论数量 |
| 分享数 | 整数 | ❌ | 内容分享数量 |
| 年龄段 | 字符串 | ❌ | 用户年龄段 |
| 性别 | 字符串 | ❌ | 用户性别 |
| 设备类型 | 字符串 | ❌ | 使用设备类型 |
| 话题标签 | 字符串 | ❌ | 内容话题标签 |

### 示例数据

项目包含了通过 `generate_sample_data.py` 生成的示例数据，包含 5000 条模拟用户行为记录，涵盖了所有分析维度。

## 🔧 配置说明

### 环境配置

在 `config/settings.py` 中可以配置：

- 缓存设置
- 数据处理参数
- 可视化样式
- 性能优化选项

### 缓存管理

系统自动缓存计算结果以提升性能：

- 数据加载缓存
- 分析结果缓存
- 可视化图表缓存

可以在应用界面中查看和清理缓存。

## 🎯 使用指南

### 1. 数据加载

1. 在侧边栏选择数据文件路径
2. 选择处理模式（样本模式/完整模式）
3. 点击"加载数据"按钮

### 2. 分析功能

- **用户画像**：查看用户基础属性分布和活跃度分析
- **地理分析**：探索用户地理分布和区域行为模式
- **时间分析**：分析用户活跃时间模式和趋势
- **内容分析**：了解内容类型分布和话题偏好
- **社交网络**：分析用户互动关系和影响力

### 3. 数据导出

分析结果支持多种格式导出：

- 图表下载（PNG, SVG, PDF）
- 数据导出（CSV, Excel）
- 报告生成（HTML, PDF）

## 🛠️ 开发指南

### 环境要求

- Python 3.8+
- Streamlit 1.28+
- Pandas 2.0+
- Plotly 5.0+

### 开发安装

```bash
# 克隆项目
git clone https://github.com/your-username/user-behavior-analysis.git
cd user-behavior-analysis

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -r requirements.txt

# 启动开发服务器
streamlit run app.py
```

### 添加新功能

1. 在 `pages/` 目录下创建新的分析模块
2. 在 `utils/` 目录下添加相关工具函数
3. 更新 `app.py` 中的导航菜单
4. 添加相应的测试文件

### 代码规范

- 使用 Python PEP 8 代码风格
- 添加适当的文档字符串
- 使用类型提示
- 编写单元测试

## 📈 性能优化

### 大数据处理

- **分块加载**：自动将大文件分块处理
- **内存优化**：智能数据类型优化和内存管理
- **缓存策略**：多层缓存提升响应速度
- **异步处理**：后台处理耗时操作

### 部署优化

- **资源压缩**：优化静态资源大小
- **CDN 加速**：使用 CDN 加速资源加载
- **缓存配置**：合理配置浏览器缓存
- **监控告警**：集成性能监控

## 🔒 安全说明

### 数据安全

- 本地数据处理，不上传到外部服务器
- 支持数据脱敏和匿名化处理
- 缓存数据自动加密存储
- 支持访问控制和权限管理

### 隐私保护

- 遵循数据保护法规
- 支持数据删除和清理
- 不收集用户个人信息
- 透明的数据处理流程

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 贡献类型

- 🐛 Bug 修复
- ✨ 新功能开发
- 📚 文档改进
- 🎨 界面优化
- ⚡ 性能提升
- 🧪 测试覆盖

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢以下开源项目：

- [Streamlit](https://streamlit.io/) - Web 应用框架
- [Pandas](https://pandas.pydata.org/) - 数据处理库
- [Plotly](https://plotly.com/) - 交互式可视化
- [NumPy](https://numpy.org/) - 数值计算库

## 📞 联系方式

- 项目主页：[GitHub Repository](https://github.com/your-username/user-behavior-analysis)
- 问题反馈：[Issues](https://github.com/your-username/user-behavior-analysis/issues)
- 功能建议：[Discussions](https://github.com/your-username/user-behavior-analysis/discussions)

---

**⭐ 如果这个项目对你有帮助，请给它一个星标！**
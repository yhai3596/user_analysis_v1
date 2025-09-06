# 部署到 GitHub 和 Streamlit Community Cloud 指南

## 🚀 快速部署步骤

### 第一步：准备 GitHub 仓库

#### 1.1 在 GitHub 上创建新仓库

1. 访问 [GitHub](https://github.com)
2. 点击右上角的 "+" 按钮，选择 "New repository"
3. 填写仓库信息：
   - **Repository name**: `user-behavior-analysis` (或其他名称)
   - **Description**: `用户行为分析系统 - 基于Streamlit的数据分析平台`
   - **Visibility**: Public (推荐，便于部署)
   - **Initialize**: 不要勾选任何初始化选项
4. 点击 "Create repository"

#### 1.2 本地 Git 初始化和推送

在项目目录中打开命令行，执行以下命令：

```bash
# 1. 初始化 Git 仓库
git init

# 2. 添加所有文件
git add .

# 3. 创建初始提交
git commit -m "Initial commit: 用户行为分析系统"

# 4. 添加远程仓库（替换为你的 GitHub 用户名和仓库名）
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git

# 5. 推送到 GitHub
git push -u origin main
```

**注意**: 将 `YOUR_USERNAME` 和 `YOUR_REPOSITORY_NAME` 替换为你的实际 GitHub 用户名和仓库名。

### 第二步：部署到 Streamlit Community Cloud

#### 2.1 访问 Streamlit Community Cloud

1. 访问 [share.streamlit.io](https://share.streamlit.io)
2. 使用 GitHub 账户登录
3. 授权 Streamlit 访问你的 GitHub 仓库

#### 2.2 创建新应用

1. 点击 "New app" 按钮
2. 填写应用信息：
   - **Repository**: 选择你刚创建的仓库
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**: 自定义应用 URL（可选）
3. 点击 "Deploy!" 按钮

#### 2.3 等待部署完成

- 部署过程通常需要 2-5 分钟
- 可以在部署日志中查看进度
- 部署成功后会获得一个公共 URL

## 🔧 部署配置优化

### 环境变量配置（可选）

如果需要配置环境变量，在 Streamlit Community Cloud 应用设置中：

1. 进入应用管理页面
2. 点击 "Settings" 选项卡
3. 在 "Secrets" 部分添加配置：

```toml
# 示例配置
[general]
app_title = "用户行为分析系统"
max_upload_size = 200

[cache]
ttl = 3600
max_entries = 1000
```

### 性能优化配置

在 `.streamlit/config.toml` 文件中（如果需要）：

```toml
[server]
maxUploadSize = 200

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

## 📊 数据文件处理

### 当前解决方案

✅ **已解决**: 项目现在使用相对路径和示例数据文件

- 使用 `切片.xlsx` 作为示例数据
- 所有硬编码的绝对路径已修改为相对路径
- 包含数据生成脚本 `generate_sample_data.py`

### 使用真实数据的选项

#### 选项 1：文件上传功能（推荐）

在应用中添加文件上传：

```python
uploaded_file = st.file_uploader(
    "上传数据文件", 
    type=['xlsx', 'csv'],
    help="支持 Excel 和 CSV 格式，最大 200MB"
)

if uploaded_file is not None:
    # 处理上传的文件
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    st.session_state.current_data = df
    st.success(f"数据上传成功！共 {len(df)} 条记录")
```

#### 选项 2：GitHub LFS（大文件存储）

对于大于 100MB 的数据文件：

```bash
# 安装 Git LFS
git lfs install

# 跟踪大文件
git lfs track "*.xlsx"
git lfs track "*.csv"

# 提交 .gitattributes
git add .gitattributes
git commit -m "Add Git LFS tracking"

# 添加大文件
git add your_large_file.xlsx
git commit -m "Add large data file"
git push
```

#### 选项 3：云存储集成

连接到云存储服务：

```python
# AWS S3 示例
import boto3

def load_from_s3(bucket_name, file_key):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket_name, Key=file_key)
    return pd.read_excel(obj['Body'])
```

## 🐛 常见问题解决

### 问题 1：部署失败

**可能原因**:
- `requirements.txt` 格式错误
- 依赖包版本冲突
- 文件路径错误

**解决方案**:
```bash
# 检查 requirements.txt
cat requirements.txt

# 本地测试
pip install -r requirements.txt
streamlit run app.py
```

### 问题 2：数据加载失败

**可能原因**:
- 文件路径使用绝对路径
- 数据文件未包含在仓库中
- 文件格式不支持

**解决方案**:
- ✅ 已修复：使用相对路径
- ✅ 已包含：示例数据文件
- 确保文件格式为 Excel 或 CSV

### 问题 3：内存不足

**可能原因**:
- 数据文件过大
- 内存使用未优化

**解决方案**:
```python
# 使用分块加载
loader = BigDataLoader()
for chunk in loader.load_data_chunked(file_path, chunk_size=1000):
    # 处理数据块
    process_chunk(chunk)
```

### 问题 4：应用访问慢

**解决方案**:
- 启用缓存功能
- 减少数据加载量
- 优化可视化图表

## 📈 部署后优化

### 监控应用性能

1. **查看应用日志**：
   - 在 Streamlit Community Cloud 管理页面查看日志
   - 监控错误和警告信息

2. **性能指标**：
   - 页面加载时间
   - 内存使用情况
   - 用户访问量

### 持续更新

```bash
# 更新代码
git add .
git commit -m "Update: 添加新功能"
git push

# Streamlit Community Cloud 会自动重新部署
```

### 版本管理

```bash
# 创建版本标签
git tag -a v1.0.0 -m "Version 1.0.0: 初始发布版本"
git push origin v1.0.0

# 创建发布分支
git checkout -b release/v1.0.0
git push origin release/v1.0.0
```

## 🎯 部署检查清单

在部署前，请确认以下项目：

- [ ] ✅ 代码已推送到 GitHub
- [ ] ✅ `requirements.txt` 包含所有依赖
- [ ] ✅ `app.py` 可以正常运行
- [ ] ✅ 数据文件使用相对路径
- [ ] ✅ 示例数据文件已包含
- [ ] ✅ `.gitignore` 配置正确
- [ ] ✅ README.md 文档完整
- [ ] ✅ 本地测试通过

## 🔗 有用链接

- [Streamlit Community Cloud 文档](https://docs.streamlit.io/streamlit-community-cloud)
- [GitHub 使用指南](https://docs.github.com/)
- [Git LFS 文档](https://git-lfs.github.io/)
- [Streamlit 配置文档](https://docs.streamlit.io/library/advanced-features/configuration)

## 📞 获取帮助

如果遇到问题：

1. 查看 Streamlit Community Cloud 部署日志
2. 检查 GitHub 仓库文件结构
3. 验证本地应用是否正常运行
4. 参考 [DEPLOYMENT.md](DEPLOYMENT.md) 详细指南

---

**🎉 恭喜！按照以上步骤，你的用户行为分析系统将成功部署到云端！**
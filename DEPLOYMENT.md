# 用户行为分析系统 - 部署指南

## 概述

本文档详细说明如何将用户行为分析系统部署到 Streamlit Community Cloud，以及如何处理数据文件。

## 🚀 快速部署到 Streamlit Community Cloud

### 前提条件

1. GitHub 账户
2. Streamlit Community Cloud 账户（免费）
3. 项目代码已推送到 GitHub 仓库

### 部署步骤

#### 1. 准备 GitHub 仓库

```bash
# 初始化 git 仓库（如果还没有）
git init

# 添加所有文件
git add .

# 提交代码
git commit -m "Initial commit: 用户行为分析系统"

# 添加远程仓库
git remote add origin https://github.com/your-username/your-repo-name.git

# 推送到 GitHub
git push -u origin main
```

#### 2. 登录 Streamlit Community Cloud

1. 访问 [share.streamlit.io](https://share.streamlit.io)
2. 使用 GitHub 账户登录
3. 授权 Streamlit 访问你的 GitHub 仓库

#### 3. 部署应用

1. 点击 "New app" 按钮
2. 选择你的 GitHub 仓库
3. 选择分支（通常是 `main`）
4. 设置主文件路径：`app.py`
5. 点击 "Deploy!" 按钮

#### 4. 等待部署完成

- 部署过程通常需要 2-5 分钟
- 可以在部署日志中查看进度
- 部署成功后会获得一个公共 URL

## 📊 数据文件处理

### 当前解决方案

项目已经包含了示例数据文件 `切片.xlsx`，这是通过 `generate_sample_data.py` 脚本生成的模拟数据。

### 使用真实数据的选项

#### 选项 1：文件上传功能（推荐）

在应用中添加文件上传组件：

```python
# 在 app.py 中添加
uploaded_file = st.file_uploader(
    "上传数据文件",
    type=['xlsx', 'csv'],
    help="支持 Excel 和 CSV 格式"
)

if uploaded_file is not None:
    # 处理上传的文件
    if uploaded_file.name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)
```

#### 选项 2：云存储集成

将数据文件存储在云服务中：

- **AWS S3**
- **Google Cloud Storage**
- **Azure Blob Storage**
- **GitHub LFS**（大文件存储）

#### 选项 3：数据库连接

连接到云数据库：

- **PostgreSQL**
- **MySQL**
- **MongoDB**
- **Google Sheets API**

### 环境变量配置

在 Streamlit Community Cloud 中设置环境变量：

1. 在应用设置中找到 "Secrets" 部分
2. 添加必要的配置：

```toml
# .streamlit/secrets.toml
[database]
host = "your-db-host"
port = 5432
database = "your-db-name"
username = "your-username"
password = "your-password"

[aws]
access_key_id = "your-access-key"
secret_access_key = "your-secret-key"
bucket_name = "your-bucket-name"
```

## 🔧 配置优化

### 性能优化

1. **缓存配置**：
   ```python
   @st.cache_data
   def load_data(file_path):
       return pd.read_excel(file_path)
   ```

2. **内存管理**：
   - 使用分块加载大文件
   - 及时释放不需要的数据
   - 优化数据类型

3. **资源限制**：
   - Streamlit Community Cloud 有内存限制（1GB）
   - 处理大数据集时需要特别注意

### 安全配置

1. **敏感数据保护**：
   - 不要在代码中硬编码密码或 API 密钥
   - 使用 Streamlit Secrets 管理敏感信息
   - 在 `.gitignore` 中排除敏感文件

2. **访问控制**：
   ```python
   # 简单的密码保护
   def check_password():
       def password_entered():
           if st.session_state["password"] == st.secrets["password"]:
               st.session_state["password_correct"] = True
               del st.session_state["password"]
           else:
               st.session_state["password_correct"] = False

       if "password_correct" not in st.session_state:
           st.text_input("密码", type="password", on_change=password_entered, key="password")
           return False
       elif not st.session_state["password_correct"]:
           st.text_input("密码", type="password", on_change=password_entered, key="password")
           st.error("密码错误")
           return False
       else:
           return True
   ```

## 🐛 故障排除

### 常见问题

1. **文件路径错误**：
   - 确保使用相对路径
   - 检查文件是否存在于仓库中

2. **依赖包问题**：
   - 确保 `requirements.txt` 包含所有必要的包
   - 指定具体的版本号避免兼容性问题

3. **内存不足**：
   - 减少数据加载量
   - 使用数据采样
   - 优化数据处理逻辑

4. **部署失败**：
   - 检查部署日志
   - 确认所有文件都已推送到 GitHub
   - 验证 `requirements.txt` 的格式

### 调试技巧

1. **本地测试**：
   ```bash
   streamlit run app.py
   ```

2. **日志记录**：
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)
   
   logger.info("应用启动")
   ```

3. **错误处理**：
   ```python
   try:
       # 数据加载逻辑
       pass
   except Exception as e:
       st.error(f"数据加载失败: {str(e)}")
       logger.error(f"数据加载错误: {str(e)}")
   ```

## 📈 监控和维护

### 应用监控

1. **使用情况统计**：
   - Streamlit Community Cloud 提供基本的使用统计
   - 可以集成 Google Analytics

2. **性能监控**：
   ```python
   import time
   
   start_time = time.time()
   # 执行操作
   execution_time = time.time() - start_time
   st.sidebar.metric("执行时间", f"{execution_time:.2f}s")
   ```

### 定期维护

1. **依赖更新**：
   - 定期更新 `requirements.txt`
   - 测试新版本的兼容性

2. **数据更新**：
   - 定期更新示例数据
   - 清理过期的缓存文件

3. **功能优化**：
   - 根据用户反馈改进界面
   - 添加新的分析功能

## 🔗 相关链接

- [Streamlit Community Cloud 文档](https://docs.streamlit.io/streamlit-community-cloud)
- [Streamlit 官方文档](https://docs.streamlit.io/)
- [GitHub 使用指南](https://docs.github.com/)
- [Python 数据分析最佳实践](https://pandas.pydata.org/docs/user_guide/)

## 📞 支持

如果在部署过程中遇到问题，可以：

1. 查看 Streamlit Community Cloud 的部署日志
2. 检查 GitHub 仓库的文件结构
3. 验证 `requirements.txt` 的内容
4. 确认数据文件的路径和格式

---

**注意**：本部署指南基于 Streamlit Community Cloud 的免费版本。如需更高的性能和更多功能，可以考虑升级到付费版本或使用其他云平台。
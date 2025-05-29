# LLM问答评估系统

基于Streamlit的问答评估数据库管理系统，用于管理和评估LLM模型的问答性能。

## 功能

- 一键建表：快速创建所有必要的数据库表
- 数据查看：实时查看各个表的内容
- 一键爬取：爬取StackExchange数据（按钮已添加，功能待实现）
- 评估功能：利用LLM评估数据集（按钮已添加，功能待实现）
- 一键导入：自动导入数据（按钮已添加，功能待实现）

## 安装与运行

1. 安装依赖：

```bash
conda create -n db_design python=3.12
conda activate db_design
pip install -r requirements.txt
```


## Config

#### 方法1：环境变量（推荐）
```bash
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=your_password
export DB_NAME=db_design_pj
```

#### 方法2：.env 文件
1. 复制配置示例：
```bash
cp configs/config_example.env .env
```

2. 编辑 `.env` 文件修改你的配置


2. 配置数据库连接：
建立数据库（如database_pj）
使用环境变量或创建 `.env` 文件（参考上面的配置系统）。


4. 启动：

```bash
streamlit run ./src/app.py
```

## 技术栈

- Python
- Streamlit
- MySQL
- 原生SQL（无ORM）
- 原生SQL（无ORM）
- 环境变量配置管理

## 环境变量说明

### 数据库配置
- `DB_HOST`: 数据库主机地址（默认：localhost）
- `DB_USER`: 数据库用户名（默认：root）
- `DB_PASSWORD`: 数据库密码（默认：root）
- `DB_NAME`: 数据库名称（默认：db_design_pj）
- `DB_PORT`: 数据库端口（默认：3306）
- `DB_CHARSET`: 字符集（默认：utf8mb4）

### 应用配置
- `APP_DEBUG`: 调试模式（默认：False）
- `STREAMLIT_PORT`: Streamlit端口（默认：8501）
- `STREAMLIT_HOST`: Streamlit主机（默认：localhost） 
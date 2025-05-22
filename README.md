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

2. 配置数据库连接：

修改 `src/database.py` 中的数据库连接参数。

3. 运行应用：

```bash
streamlit run ./src/app.py
```

## 技术栈

- Python
- Streamlit
- MySQL
- 原生SQL（无ORM） 
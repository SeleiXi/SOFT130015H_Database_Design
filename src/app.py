import streamlit as st
import pandas as pd
import mysql.connector
from database import create_tables, get_connection, get_table_names, get_table_data
from utils import show_success_message, show_error_message, show_table_data, show_table_schema

# 页面配置
st.set_page_config(
    page_title="LLM问答评估系统",
    page_icon="🤖",
    layout="wide"
)

# 应用标题
st.title("LLM问答评估系统")
st.markdown("---")

# 侧边栏
st.sidebar.title("功能菜单")
menu = st.sidebar.radio(
    "选择功能",
    ["数据库管理", "数据爬取", "LLM评估", "数据导入"]
)

# 数据库管理页面
if menu == "数据库管理":
    st.header("数据库管理")
    
    # 创建表
    st.subheader("创建数据库表")
    if st.button("一键建表"):
        results = create_tables()
        all_success = all([result[0] for result in results])
        
        if all_success:
            show_success_message("所有表创建成功！")
        else:
            failed_tables = [f"表 {i+1}: {result[1]}" for i, result in enumerate(results) if not result[0]]
            show_error_message(f"部分表创建失败: {', '.join(failed_tables)}")
    
    st.markdown("---")
    
    # 查看表数据
    st.subheader("查看表数据")
    
    # 获取所有表名
    tables = get_table_names()
    
    if not tables:
        st.info("数据库中没有表或无法连接到数据库")
    else:
        # 表选择器
        selected_table = st.selectbox("选择要查看的表", tables)
        
        # 查看表数据
        if st.button("查看数据"):
            success, data = get_table_data(selected_table)
            
            if success:
                show_table_data(selected_table, data)
            else:
                show_error_message(f"获取表数据失败: {data}")
        
        # 查看表结构
        if st.button("查看表结构"):
            conn = get_connection()
            if conn:
                show_table_schema(selected_table, conn)
                conn.close()
            else:
                show_error_message("无法连接到数据库")

# 数据爬取页面
elif menu == "数据爬取":
    st.header("数据爬取")
    st.subheader("爬取StackExchange数据")
    
    # 爬取设置
    st.markdown("### 爬取设置")
    
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("主题", "database")
        tag = st.text_input("标签", "sql")
    
    with col2:
        min_votes = st.number_input("最少投票数", min_value=1, value=10)
        limit = st.number_input("爬取数量", min_value=1, value=50)
    
    if st.button("开始爬取"):
        st.info("爬取功能尚未实现，此处为界面展示")
        st.markdown("""
        爬取逻辑将实现以下功能：
        1. 从StackExchange API爬取符合条件的问答数据
        2. 将原始问题保存到 ori_qs 表
        3. 将原始答案保存到 original_ans 表
        4. 更新标签信息到 tags 表
        5. 生成初始的更新内容记录到 updated_content 表
        """)

# LLM评估页面
elif menu == "LLM评估":
    st.header("LLM评估")
    st.subheader("使用LLM评估问答质量")
    
    # LLM选择
    st.markdown("### LLM模型选择")
    
    col1, col2 = st.columns(2)
    with col1:
        model = st.selectbox(
            "选择LLM模型",
            ["GPT-4", "Claude 3 Opus", "Llama 3 70B", "Gemini 1.5 Pro"]
        )
    
    with col2:
        eval_method = st.selectbox(
            "评估方法",
            ["内容相关性", "答案准确性", "解释清晰度", "综合评分"]
        )
    
    # 数据选择
    st.markdown("### 评估数据选择")
    
    eval_option = st.radio(
        "选择评估方式",
        ["评估所有标准问答对", "评估特定标签的问答对", "评估特定问题ID"]
    )
    
    if eval_option == "评估特定标签的问答对":
        tag_to_eval = st.text_input("输入标签名称")
    elif eval_option == "评估特定问题ID":
        question_id = st.number_input("输入问题ID", min_value=1, value=1)
    
    if st.button("开始评估"):
        st.info("评估功能尚未实现，此处为界面展示")
        st.markdown("""
        评估逻辑将实现以下功能：
        1. 根据选择条件获取待评估的问答对
        2. 调用选定的LLM模型进行评估
        3. 将评估结果保存到 llm_evaluation 表
        4. 更新问答对关联的评估ID
        5. 生成评估报告
        """)

# 数据导入页面
elif menu == "数据导入":
    st.header("数据导入")
    st.subheader("导入已有数据")
    
    # 导入选项
    import_option = st.radio(
        "选择导入方式",
        ["CSV文件导入", "JSON文件导入", "SQL脚本导入"]
    )
    
    # 上传文件
    uploaded_file = st.file_uploader("上传文件", type=["csv", "json", "sql"])
    
    # 导入设置
    if uploaded_file is not None:
        st.markdown("### 导入设置")
        
        if import_option == "CSV文件导入":
            target_table = st.selectbox("目标表", get_table_names())
            has_header = st.checkbox("包含表头", value=True)
        elif import_option == "JSON文件导入":
            auto_mapping = st.checkbox("自动映射字段", value=True)
        
        if st.button("开始导入"):
            st.info("导入功能尚未实现，此处为界面展示")
            st.markdown("""
            导入逻辑将实现以下功能：
            1. 解析上传的文件
            2. 验证数据格式和完整性
            3. 根据导入设置将数据插入相应的表
            4. 处理外键关系和数据依赖
            5. 生成导入报告
            """)

# 页脚
st.markdown("---")
st.markdown("© 2023 LLM问答评估系统 | 基于Streamlit和MySQL构建") 
import streamlit as st
import pandas as pd
import mysql.connector
from database import create_tables, get_connection, get_table_names, get_table_data
from utils import show_success_message, show_error_message, show_table_data, show_table_schema

# 页面配置
st.set_page_config(
    page_title="LLM问答评估系统",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 应用标题
st.title("LLM问答评估系统")
st.markdown("---")

st.markdown("本系统用于LLM问答数据的管理、爬取和评估，支持多种模型评估比对")

tables_num = 0

    
with st.expander("使用说明"):
    st.markdown("""
    **基本功能介绍：**
    - **数据库管理**：创建和查看表结构，查看表数据
    - **数据爬取**：从StackExchange爬取问答数据
    - **LLM评估**：使用多种LLM模型评估问答质量
    - **数据导入**：导入现有数据到系统
    """)

# 侧边栏设置
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; margin-bottom: 1rem;'>
        <h1>功能菜单</h1>
    </div>
    """, unsafe_allow_html=True)
    
    menu = st.radio(
        "",
        ["📊 数据库管理", "🕷️ 数据爬取", "🔍 LLM评估", "📥 数据导入"]
    )
    
    # 显示系统状态
    st.markdown("---")
    st.markdown("### 系统状态")
    
    # # 数据库连接状态
    # conn = get_connection()
    # if conn:
    #     st.success("✅ 数据库连接正常")
    #     conn.close()
    # else:
    #     st.error("❌ 数据库连接失败")
    
    # 表数量
    # tables = get_table_names()
    # if tables:
    #     st.info(f"📑 当前数据库表数量: {len(tables)}")
    # else:
    #     st.warning("⚠️ 数据库中没有表")


# 数据库管理页面
if menu == "📊 数据库管理":
    st.header("📊 数据库管理")
    
    # 创建选项卡
    tab1, tab2 = st.tabs(["表操作", "数据查看"])
    
    with tab1:
        st.subheader("数据库表操作")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 创建表
            if st.button("🔨 一键建表", key="create_tables"):
                with st.spinner("创建表中..."):
                    results = create_tables()   
                    all_success = all([result[0] for result in results])
                    
                    if all_success:
                        show_success_message("所有表创建成功！")
                    else:
                        failed_tables = [f"表 {i+1}: {result[1]}" for i, result in enumerate(results) if not result[0]]
                        show_error_message(f"部分表创建失败: {', '.join(failed_tables)}")
            if st.button("🔍 一键查询", key="view_table_schema"):
                tables = get_table_names()
                if tables:
                    # 把这一句持久化
                    tables_num = len(tables)
                    st.info(f"📑 当前数据库表数量: {tables_num}")
                else:
                    st.warning("⚠️ 数据库中没有表")
        
        with col2:
            # 表信息统计
            st.metric("数据库表总数", tables_num)
    
    with tab2:
        st.subheader("数据查看")
        
        # 获取所有表名
        if not tables_num:
            st.info("ℹ️ 数据库中没有表或无法连接到数据库")
        else:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # 表选择器
                selected_table = st.selectbox(
                    "选择要查看的表",
                    tables,
                    format_func=lambda x: f"📑 {x}"
                )
            
            with col2:
                view_option = st.radio(
                    "查看选项",
                    ["📋 数据", "📐 结构"]
                )
            
            if view_option == "📋 数据":
                if st.button("加载数据", key="load_data"):
                    with st.spinner("加载数据中..."):
                        success, data = get_table_data(selected_table)
                        
                        if success:
                            show_table_data(selected_table, data)
                        else:
                            show_error_message(f"❌ 获取表数据失败: {data}")
            else:
                if st.button("查看结构", key="view_schema"):
                    with st.spinner("加载表结构..."):
                        conn = get_connection()
                        if conn:
                            show_table_schema(selected_table, conn)
                            conn.close()
                        else:
                            show_error_message("❌ 无法连接到数据库")

# 数据爬取页面
elif menu == "🕷️ 数据爬取":
    st.header("🕷️ 数据爬取")
    
    # 创建选项卡
    tab1, tab2, tab3 = st.tabs(["StackExchange爬取", "自定义爬取", "爬取历史"])
    
    with tab1:
        st.subheader("爬取StackExchange数据")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.markdown("#### 基本设置")
            topic = st.text_input("💭 主题", "database")
            tag = st.text_input("🏷️ 标签", "sql")
        
        with col2:
            st.markdown("#### 筛选条件")
            min_votes = st.number_input("👍 最少投票数", min_value=1, value=10)
            limit = st.number_input("📊 爬取数量", min_value=1, value=50)
            
            advanced = st.checkbox("高级选项")
            if advanced:
                sort_by = st.selectbox(
                    "排序方式",
                    ["votes", "activity", "creation", "relevance"],
                    index=0
                )
        
        with col3:
            st.markdown("#### 操作")
            if st.button("🚀 开始爬取", key="start_crawl"):
                with st.spinner("爬取中..."):
                    st.info("爬取功能尚未实现，此处为界面展示")
    
    with tab2:
        st.subheader("自定义爬取")
        st.info("自定义爬取功能将在下一版本中提供")
    
    with tab3:
        st.subheader("爬取历史")
        st.info("爬取历史功能将在下一版本中提供")

# LLM评估页面
elif menu == "🔍 LLM评估":
    st.header("🔍 LLM评估")
    
    # 创建选项卡
    tab1, tab2, tab3 = st.tabs(["评估配置", "评估结果", "模型比对"])
    
    with tab1:
        st.subheader("配置评估参数")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 模型选择")
            model = st.selectbox(
                "🤖 选择LLM模型",
                ["GPT-4", "Claude 3 Opus", "Llama 3 70B", "Gemini 1.5 Pro"]
            )
            
            api_key = st.text_input("API密钥（如需要）", type="password")
        
        with col2:
            st.markdown("#### 评估方法")
            eval_method = st.selectbox(
                "📊 评估方法",
                ["内容相关性", "答案准确性", "解释清晰度", "综合评分"]
            )
            
            eval_metrics = st.multiselect(
                "评估指标",
                ["正确性", "完整性", "清晰度", "专业性", "创新性"],
                default=["正确性", "完整性", "清晰度"]
            )
        
        st.markdown("### 📌 评估范围")
        
        eval_option = st.radio(
            "",
            ["📑 评估所有标准问答对", "🏷️ 评估特定标签的问答对", "🔍 评估特定问题ID"]
        )
        
        if eval_option == "🏷️ 评估特定标签的问答对":
            tag_to_eval = st.text_input("输入标签名称")
        elif eval_option == "🔍 评估特定问题ID":
            question_id = st.number_input("输入问题ID", min_value=1, value=1)
        
        # 高级设置
        with st.expander("高级设置"):
            st.slider("温度", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
            st.number_input("最大输出长度", min_value=100, value=500)
            st.checkbox("使用流式输出", value=True)
        
        if st.button("🚀 开始评估", key="start_eval"):
            with st.spinner("评估中..."):
                st.info("评估功能尚未实现，此处为界面展示")
    
    with tab2:
        st.subheader("评估结果")
        st.info("请先进行评估...")
    
    with tab3:
        st.subheader("模型比对")
        st.info("模型比对功能将在下一版本中提供")

# 数据导入页面
elif menu == "📥 数据导入":
    st.header("📥 数据导入")
    
    # 创建选项卡
    tab1, tab2, tab3 = st.tabs(["文件导入", "API导入", "导入历史"])
    
    with tab1:
        st.subheader("文件数据导入")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 导入选项
            import_option = st.radio(
                "选择导入方式",
                ["📄 CSV文件导入", "📋 JSON文件导入", "💾 SQL脚本导入"]
            )
            
            # 上传文件
            uploaded_file = st.file_uploader(
                "上传文件",
                type=["csv", "json", "sql"],
                help="选择要导入的文件"
            )
        
        with col2:
            st.markdown("""
            <div style='padding: 1rem; border-radius: 4px;'>
                <h4 style='margin: 0'>导入说明</h4>
                <ul style='margin-top: 1rem; padding-left: 1.5rem;'>
                    <li>支持CSV、JSON和SQL格式</li>
                    <li>文件大小限制：100MB</li>
                    <li>请确保数据格式正确</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        if uploaded_file is not None:
            st.markdown("### ⚙️ 导入设置")
            
            if import_option == "📄 CSV文件导入":
                col1, col2 = st.columns(2)
                with col1:
                    target_table = st.selectbox("📊 目标表", get_table_names())
                with col2:
                    has_header = st.checkbox("✅ 包含表头", value=True)
                
                encoding = st.selectbox("文件编码", ["UTF-8", "GBK", "ISO-8859-1"], index=0)
                delimiter = st.selectbox("分隔符", [",", ";", "\\t", "|"], index=0)
                
            elif import_option == "📋 JSON文件导入":
                auto_mapping = st.checkbox("✅ 自动映射字段", value=True)
                
                if not auto_mapping:
                    st.text_area("字段映射（JSON格式）", "{\"source_field\": \"target_field\"}")
            
            with st.expander("高级选项"):
                st.checkbox("覆盖现有数据", value=False)
                st.checkbox("导入前验证", value=True)
                st.checkbox("失败时继续", value=False)
            
            if st.button("🚀 开始导入", key="start_import"):
                with st.spinner("导入中..."):
                    st.info("导入功能尚未实现，此处为界面展示")
    
    with tab2:
        st.subheader("API数据导入")
        st.info("API导入功能将在下一版本中提供")
    
    with tab3:
        st.subheader("导入历史")
        st.info("导入历史功能将在下一版本中提供")

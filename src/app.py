import streamlit as st
import pandas as pd
import mysql.connector
import json #确保导入json模块
from database import create_tables, get_connection, get_table_names, get_table_data, execute_query, batch_import_json_data # 导入 batch_import_json_data
from utils import show_success_message, show_error_message, show_table_data, show_table_schema, download_sample_json, get_table_schema, show_warning_message

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
        "功能菜单选项",
        ["📊 数据库管理", "🕷️ 数据爬取", "🔍 LLM评估", "📥 数据导入"],
        label_visibility="collapsed"
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
                    st.info(f"📑 当前数据库表数量: {len(tables)}")
                else:
                    st.warning("⚠️ 数据库中没有表")
        
        with col2:
            # 表信息统计
            tables = get_table_names()
            st.metric("数据库表总数", len(tables) if tables else 0)
    
    with tab2:
        st.subheader("数据查看")
        
        # 获取所有表名
        tables = get_table_names()
        tables_count = len(tables) if tables else 0
        
        if not tables_count:
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
            "评估范围选项",
            ["📑 评估所有标准问答对", "🏷️ 评估特定标签的问答对", "🔍 评估特定问题ID"],
            label_visibility="collapsed"
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
                    available_tables = get_table_names()
                    if available_tables:
                        target_table = st.selectbox("📊 目标表", available_tables)
                    else:
                        st.warning("⚠️ 数据库中没有可用的表")
                        target_table = None
                with col2:
                    has_header = st.checkbox("✅ 包含表头", value=True)
                
                encoding = st.selectbox("文件编码", ["UTF-8", "GBK", "ISO-8859-1"], index=0)
                delimiter = st.selectbox("分隔符", [",", ";", "\\t", "|"], index=0)
                
            elif import_option == "📋 JSON文件导入":
                st.write("### JSON导入设置")
                
                # JSON 导入子选项
                json_import_type = st.radio(
                    "选择JSON导入模式",
                    ("单个表导入 (上传包含单个表记录的列表的JSON)", "多个表批量导入 (上传包含表名为键，记录列表为值的JSON)"),
                    key="json_import_type_selector"
                )

                # 根据选择的模式更新示例下载
                sample_format = "single_table_ori_qs" if "单个表导入" in json_import_type else "multi_table"
                sample_file_name = "sample_single_table_ori_qs.json" if sample_format == "single_table_ori_qs" else "sample_multi_table.json"

                sample_json_bytes = download_sample_json(format_type=sample_format)
                st.download_button(
                    label=f"📥 下载{('单个表' if '单个表导入' in json_import_type else '多表批量')}示例JSON",
                    data=sample_json_bytes,
                    file_name=sample_file_name,
                    mime="application/json"
                )
                
                if uploaded_file is not None and uploaded_file.type == "application/json":
                    try:
                        # 为了避免重复读取，先将文件内容读到内存
                        file_content = uploaded_file.getvalue()
                        
                        if "单个表导入" in json_import_type:
                            # 现有单表导入逻辑
                            # 使用 BytesIO 将字节串转换为文件类对象供 pd.read_json 使用
                            from io import BytesIO
                            json_df = pd.read_json(BytesIO(file_content))
                            st.success("✅ JSON文件已加载 (单表模式)")

                            with st.expander("数据预览 (单表)"):
                                st.write(f"总记录数: {len(json_df)}")
                                st.dataframe(json_df.head(3))
                            
                            target_table_single = st.selectbox(
                                "选择目标表 (单表导入)", 
                                get_table_names(),
                                key="json_target_table_single"
                            )
                            
                            if target_table_single:
                                conn = get_connection()
                                if conn:
                                    schema_df_single = get_table_schema(target_table_single, conn)
                                    conn.close()
                                    
                                    st.write("### 字段映射 (单表)")
                                    col1_single, col2_single = st.columns(2)
                                    mapping_single = {}
                                    for _, row_single in schema_df_single.iterrows():
                                        with col1_single:
                                            st.markdown(f"**{row_single['字段名']}** ({row_single['类型']})")
                                        with col2_single:
                                            selected_single = st.selectbox(
                                                f"映射 {row_single['字段名']}",
                                                options=["不映射"] + list(json_df.columns),
                                                key=f"map_single_{target_table_single}_{row_single['字段名']}"
                                            )
                                            mapping_single[row_single['字段名']] = selected_single if selected_single != "不映射" else None
                                    
                                    if st.button("🚀 执行单表导入", key="json_import_btn_single"):
                                        with st.spinner("单表导入中..."):
                                            try:
                                                valid_mapping_single = {k:v for k,v in mapping_single.items() if v is not None}
                                                columns_single = list(valid_mapping_single.keys())
                                                values_to_insert_single = [tuple(row_val) for _, row_val in json_df[list(valid_mapping_single.values())].iterrows()]
                                                
                                                placeholders_single = ", ".join(["%s"] * len(columns_single))
                                                query_single = f"INSERT INTO `{target_table_single}` ({", ".join([f'`{col}`' for col in columns_single])}) VALUES ({placeholders_single})"
                                                
                                                if values_to_insert_single:
                                                    success_single, result_single = execute_query(query_single, params=values_to_insert_single, many=True)
                                                    if success_single:
                                                        show_success_message(f"成功导入 {len(values_to_insert_single)} 条数据到 {target_table_single}")
                                                    else:
                                                        show_error_message(f"单表导入失败: {result_single}")
                                                else:
                                                    show_warning_message("没有有效数据可导入。")
                                            except Exception as e_single:
                                                show_error_message(f"单表导入出错: {str(e_single)}")
                        
                        elif "多个表批量导入" in json_import_type:
                            parsed_json_data = json.loads(file_content.decode('utf-8'))
                            st.success("✅ JSON文件已加载 (多表批量模式)")

                            if not isinstance(parsed_json_data, dict):
                                show_error_message("批量导入模式下，JSON文件顶层应为字典 (表名为键)。")
                            else:
                                st.write("### 检测到的表和记录数：")
                                tables_in_json = list(parsed_json_data.keys())
                                data_preview = {}
                                for table_name_json, records_json in parsed_json_data.items():
                                    if isinstance(records_json, list):
                                        data_preview[table_name_json] = f"{len(records_json)} 条记录"
                                    else:
                                        data_preview[table_name_json] = "数据格式非列表，无法处理"
                                st.json(data_preview)

                                # 允许用户选择要导入的表
                                available_db_tables = get_table_names()
                                st.write("### 选择要导入的表：")
                                tables_to_import_selected = {}
                                for table_name_json in tables_in_json:
                                    if table_name_json in available_db_tables:
                                        tables_to_import_selected[table_name_json] = st.checkbox(f"导入表: {table_name_json} ({data_preview[table_name_json]})", value=True, key=f"cb_import_{table_name_json}")
                                    else:
                                        st.warning(f"JSON中的表 '{table_name_json}' 在数据库中不存在，将跳过。")

                                if st.button("🚀 执行多表批量导入", key="json_import_btn_multi"):
                                    data_for_batch_import = {tbl: parsed_json_data[tbl] for tbl, selected_flag in tables_to_import_selected.items() if selected_flag and tbl in parsed_json_data}
                                    if not data_for_batch_import:
                                        show_warning_message("没有选择任何表进行导入，或者所选表数据为空或格式不正确。")
                                    else:
                                        with st.spinner("多表批量导入中..."):
                                            import_results = batch_import_json_data(data_for_batch_import)
                                            st.write("### 批量导入结果：")
                                            if "error" in import_results:
                                                show_error_message(f"批量导入时发生严重错误: {import_results['error']}")
                                            else:
                                                for table_name_res, res_detail in import_results.items():
                                                    if res_detail.get("skipped"):
                                                        st.info(f"表 {table_name_res}: {res_detail['message']}")
                                                    elif res_detail["success"]:
                                                        show_success_message(f"表 {table_name_res}: {res_detail['message']}")
                                                    else:
                                                        show_error_message(f"表 {table_name_res}: {res_detail['message']} {('错误详情: ' + '; '.join(res_detail.get('errors', []))) if res_detail.get('errors') else ''}")
                                        
                    except Exception as e:
                        show_error_message(f"JSON文件处理失败: {str(e)}. 请确保文件是有效的JSON，并且编码为UTF-8。下载示例文件查看格式。")
            
            with st.expander("高级选项"):
                st.checkbox("覆盖现有数据", value=False)
                st.checkbox("导入前验证", value=True)
                st.checkbox("失败时继续", value=False)

    with tab2:
        st.subheader("API数据导入")
        st.info("API导入功能将在下一版本中提供")
    
    with tab3:
        st.subheader("导入历史")
        st.info("导入历史功能将在下一版本中提供")

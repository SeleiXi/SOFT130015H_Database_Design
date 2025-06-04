import streamlit as st
import pandas as pd
import mysql.connector
import json #确保导入json模块
from database import (create_tables, get_connection, get_table_names, get_table_data, execute_query, batch_import_json_data, 
                     get_all_questions_with_answers, get_questions_with_tags, get_llm_evaluation_results, 
                     get_top_scored_answers, get_question_answer_pairs, get_model_performance_comparison,
                     get_questions_by_tag, get_answers_by_score_range, get_recent_updates, search_content,
                     get_database_statistics, get_tag_distribution, get_model_cost_analysis, 
                     get_evaluation_trends, get_answer_length_analysis, get_question_complexity_analysis,
                     get_orphan_records, get_evaluation_score_distribution) # 导入新的查询函数
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
        ["📊 数据库管理", "🔍 智能查询", "🕷️ 数据爬取", "🎯 LLM评估", "📥 数据导入"],
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

# 智能查询页面
elif menu == "🔍 智能查询":
    st.header("🔍 智能查询")
    
    # 分页控制函数
    def show_pagination_controls(key_prefix, total_pages, current_page):
        """显示分页控制组件"""
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⏮️ 首页", key=f"{key_prefix}_first") and current_page > 1:
                st.session_state[f"{key_prefix}_page"] = 1
                st.rerun()
        
        with col2:
            if st.button("◀️ 上页", key=f"{key_prefix}_prev") and current_page > 1:
                st.session_state[f"{key_prefix}_page"] = current_page - 1
                st.rerun()
        
        with col3:
            new_page = st.number_input(
                f"页码 (共 {total_pages} 页)", 
                min_value=1, 
                max_value=total_pages, 
                value=current_page,
                key=f"{key_prefix}_page_input"
            )
            if new_page != current_page:
                st.session_state[f"{key_prefix}_page"] = new_page
                st.rerun()
        
        with col4:
            if st.button("▶️ 下页", key=f"{key_prefix}_next") and current_page < total_pages:
                st.session_state[f"{key_prefix}_page"] = current_page + 1
                st.rerun()
        
        with col5:
            if st.button("⏭️ 末页", key=f"{key_prefix}_last") and current_page < total_pages:
                st.session_state[f"{key_prefix}_page"] = total_pages
                st.rerun()
    
    def display_query_results(results, columns, key_prefix, total_count, total_pages, current_page):
        """显示查询结果"""
        if results:
            df = pd.DataFrame(results, columns=columns)
            st.dataframe(df, use_container_width=True)
            
            # 显示统计信息
            st.info(f"📊 总记录数: {total_count} | 当前页: {current_page}/{total_pages} | 当前显示: {len(results)} 条")
            
            # 分页控制
            show_pagination_controls(key_prefix, total_pages, current_page)
        else:
            st.warning("🔍 未找到相关数据")
    
    # 创建选项卡
    tab1, tab2, tab3, tab4 = st.tabs(["📋 基础查询", "🔗 关联查询", "📊 统计分析", "🔎 高级搜索"])
    
    with tab1:
        st.subheader("📋 基础查询功能")
        
        # 设置每页显示条数
        page_size = st.selectbox("每页显示条数", [5, 10, 20, 50], index=1, key="basic_page_size")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📝 查看所有问题答案", key="all_qa"):
                if "all_qa_page" not in st.session_state:
                    st.session_state.all_qa_page = 1
                
                with st.spinner("查询中..."):
                    success, message, total_count, results, total_pages = get_all_questions_with_answers(
                        st.session_state.all_qa_page, page_size
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        columns = ["问题内容", "原答案内容",  "标准答案内容"]
                        display_query_results(results, columns, "all_qa", total_count, total_pages, st.session_state.all_qa_page)
                    else:
                        show_error_message(f"❌ 查询失败: {message}")
        
        with col2:
            if st.button("🏷️ 查看标签问题", key="tagged_questions"):
                if "tagged_q_page" not in st.session_state:
                    st.session_state.tagged_q_page = 1
                
                with st.spinner("查询中..."):
                    success, message, total_count, results, total_pages = get_questions_with_tags(
                        st.session_state.tagged_q_page, page_size
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        columns = ["标准问题ID", "问题内容", "标签名称", "原始问题"]
                        display_query_results(results, columns, "tagged_q", total_count, total_pages, st.session_state.tagged_q_page)
                    else:
                        show_error_message(f"❌ 查询失败: {message}")
        
        with col3:
            if st.button("📊 查看问答配对", key="qa_pairs"):
                if "qa_pairs_page" not in st.session_state:
                    st.session_state.qa_pairs_page = 1
                
                with st.spinner("查询中..."):
                    success, message, total_count, results, total_pages = get_question_answer_pairs(
                        st.session_state.qa_pairs_page, page_size
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        columns = ["配对ID", "问题", "答案", "标签", "最后操作", "更新信息"]
                        display_query_results(results, columns, "qa_pairs", total_count, total_pages, st.session_state.qa_pairs_page)
                    else:
                        show_error_message(f"❌ 查询失败: {message}")
    
    with tab2:
        st.subheader("🔗 关联查询功能")
        
        page_size = st.selectbox("每页显示条数", [5, 10, 20, 50], index=1, key="relation_page_size")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎯 LLM评估结果", key="llm_eval"):
                if "llm_eval_page" not in st.session_state:
                    st.session_state.llm_eval_page = 1
                
                with st.spinner("查询中..."):
                    success, message, total_count, results, total_pages = get_llm_evaluation_results(
                        st.session_state.llm_eval_page, page_size
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        columns = ["评估ID", "LLM模型", "模型参数", "评分", "标准答案", "LLM答案", "问题内容"]
                        display_query_results(results, columns, "llm_eval", total_count, total_pages, st.session_state.llm_eval_page)
                    else:
                        show_error_message(f"❌ 查询失败: {message}")
        
        with col2:
            if st.button("🏆 高分答案排行", key="top_answers"):
                if "top_ans_page" not in st.session_state:
                    st.session_state.top_ans_page = 1
                
                with st.spinner("查询中..."):
                    success, message, total_count, results, total_pages = get_top_scored_answers(
                        st.session_state.top_ans_page, page_size
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        columns = ["答案ID", "答案内容", "平均分", "评估次数", "问题内容"]
                        display_query_results(results, columns, "top_ans", total_count, total_pages, st.session_state.top_ans_page)
                    else:
                        show_error_message(f"❌ 查询失败: {message}")
        
        if st.button("🔄 最近更新", key="recent_updates"):
            if "recent_up_page" not in st.session_state:
                st.session_state.recent_up_page = 1
            
            with st.spinner("查询中..."):
                success, message, total_count, results, total_pages = get_recent_updates(
                    st.session_state.recent_up_page, page_size
                )
                
                if success:
                    st.success(f"✅ {message}")
                    columns = ["版本号", "操作类型", "更新描述", "影响问题数", "影响答案数"]
                    display_query_results(results, columns, "recent_up", total_count, total_pages, st.session_state.recent_up_page)
                else:
                    show_error_message(f"❌ 查询失败: {message}")
    
    with tab3:
        st.subheader("📊 统计分析功能")
        
        page_size = st.selectbox("每页显示条数", [5, 10, 20, 50], index=1, key="stats_page_size")
        
        # 添加数据库总览
        st.markdown("### 📈 数据库总览")
        if st.button("📊 获取数据库统计", key="db_stats"):
            with st.spinner("统计中..."):
                stats = get_database_statistics()
                
                # 使用列显示统计信息
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("总问题数", stats.get("总问题数", 0))
                    st.metric("标准问题数", stats.get("标准问题数", 0))
                    st.metric("标签数量", stats.get("标签数量", 0))
                
                with col2:
                    st.metric("总答案数", stats.get("总答案数", 0))
                    st.metric("标准答案数", stats.get("标准答案数", 0))
                    st.metric("LLM模型数", stats.get("LLM模型数", 0))
                
                with col3:
                    st.metric("评估记录数", stats.get("评估记录数", 0))
                    st.metric("问答配对数", stats.get("问答配对数", 0))
                    st.metric("更新记录数", stats.get("更新记录数", 0))
        
        st.markdown("---")
        
        # 分析功能按钮组
        st.markdown("### 🔍 详细分析")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📈 模型性能比较", key="model_performance"):
                if "model_perf_page" not in st.session_state:
                    st.session_state.model_perf_page = 1
                
                with st.spinner("查询中..."):
                    success, message, total_count, results, total_pages = get_model_performance_comparison(
                        st.session_state.model_perf_page, page_size
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        columns = ["模型名称", "参数量", "总评估数", "平均分", "最高分", "最低分", "成本(每百万token)"]
                        display_query_results(results, columns, "model_perf", total_count, total_pages, st.session_state.model_perf_page)
                    else:
                        show_error_message(f"❌ 查询失败: {message}")
            
            if st.button("🏷️ 标签分布统计", key="tag_dist"):
                if "tag_dist_page" not in st.session_state:
                    st.session_state.tag_dist_page = 1
                
                with st.spinner("统计中..."):
                    success, message, total_count, results, total_pages = get_tag_distribution(
                        st.session_state.tag_dist_page, page_size
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        columns = ["标签名称", "问题数量", "答案数量"]
                        display_query_results(results, columns, "tag_dist", total_count, total_pages, st.session_state.tag_dist_page)
                    else:
                        show_error_message(f"❌ 统计失败: {message}")
        
        with col2:
            if st.button("💰 模型成本分析", key="cost_analysis"):
                if "cost_page" not in st.session_state:
                    st.session_state.cost_page = 1
                
                with st.spinner("分析中..."):
                    success, message, total_count, results, total_pages = get_model_cost_analysis(
                        st.session_state.cost_page, page_size
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        columns = ["模型名称", "参数量", "单价(/百万token)", "总评估数", "平均分", "预估总成本"]
                        display_query_results(results, columns, "cost", total_count, total_pages, st.session_state.cost_page)
                    else:
                        show_error_message(f"❌ 分析失败: {message}")
            
            if st.button("📏 答案长度分析", key="length_analysis"):
                if "length_page" not in st.session_state:
                    st.session_state.length_page = 1
                
                with st.spinner("分析中..."):
                    success, message, total_count, results, total_pages = get_answer_length_analysis(
                        st.session_state.length_page, page_size
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        columns = ["答案ID", "答案长度", "平均分", "评估次数", "长度类别", "答案预览"]
                        display_query_results(results, columns, "length", total_count, total_pages, st.session_state.length_page)
                    else:
                        show_error_message(f"❌ 分析失败: {message}")
        
        with col3:
            if st.button("📊 评估趋势分析", key="eval_trends"):
                if "trends_page" not in st.session_state:
                    st.session_state.trends_page = 1
                
                with st.spinner("分析中..."):
                    success, message, total_count, results, total_pages = get_evaluation_trends(
                        st.session_state.trends_page, page_size
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        columns = ["评估ID", "模型名称", "评分", "评分等级", "答案预览"]
                        display_query_results(results, columns, "trends", total_count, total_pages, st.session_state.trends_page)
                    else:
                        show_error_message(f"❌ 分析失败: {message}")
            
            if st.button("🔧 问题复杂度分析", key="complexity_analysis"):
                if "complex_page" not in st.session_state:
                    st.session_state.complex_page = 1
                
                with st.spinner("分析中..."):
                    success, message, total_count, results, total_pages = get_question_complexity_analysis(
                        st.session_state.complex_page, page_size
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        columns = ["问题ID", "问题内容", "问题长度", "标签", "答案数", "平均分", "复杂度"]
                        display_query_results(results, columns, "complex", total_count, total_pages, st.session_state.complex_page)
                    else:
                        show_error_message(f"❌ 分析失败: {message}")
        
        st.markdown("---")
        
        # 数据质量检查
        st.markdown("### 🔍 数据质量检查")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚨 查找孤立记录", key="orphan_records"):
                if "orphan_page" not in st.session_state:
                    st.session_state.orphan_page = 1
                
                with st.spinner("检查中..."):
                    success, message, total_count, results, total_pages = get_orphan_records(
                        st.session_state.orphan_page, page_size
                    )
                    
                    if success:
                        if total_count > 0:
                            st.warning(f"⚠️ 发现 {total_count} 条孤立记录")
                            columns = ["记录类型", "ID", "内容", "问题描述"]
                            display_query_results(results, columns, "orphan", total_count, total_pages, st.session_state.orphan_page)
                        else:
                            st.success("✅ 未发现孤立记录，数据完整性良好")
                    else:
                        show_error_message(f"❌ 检查失败: {message}")
        
        with col2:
            if st.button("📊 评分分布图", key="score_distribution"):
                with st.spinner("生成分布图..."):
                    success, message, results = get_evaluation_score_distribution()
                    
                    if success and results:
                        st.success("✅ 评分分布统计")
                        
                        # 创建分布图
                        df_dist = pd.DataFrame(results, columns=["分数区间", "数量", "百分比"])
                        
                        col_chart1, col_chart2 = st.columns(2)
                        
                        with col_chart1:
                            st.bar_chart(df_dist.set_index("分数区间")["数量"])
                            st.caption("📊 评分区间分布 - 数量")
                        
                        with col_chart2:
                            st.bar_chart(df_dist.set_index("分数区间")["百分比"])
                            st.caption("📊 评分区间分布 - 百分比")
                        
                        # 显示详细数据
                        with st.expander("📋 详细分布数据"):
                            st.dataframe(df_dist, use_container_width=True)
                    else:
                        show_error_message(f"❌ 生成失败: {message if not success else '暂无评估数据'}")

    with tab4:
        st.subheader("🔎 高级搜索功能")
        
        page_size = st.selectbox("每页显示条数", [5, 10, 20, 50], index=1, key="search_page_size")
        
        # 按标签搜索
        st.markdown("### 🏷️ 按标签搜索")
        col1, col2 = st.columns([3, 1])
        with col1:
            tag_search = st.text_input("输入标签名称", key="tag_search_input")
        with col2:
            search_by_tag = st.button("🔍 搜索", key="search_by_tag")
        
        if search_by_tag and tag_search:
            if "tag_search_page" not in st.session_state:
                st.session_state.tag_search_page = 1
            
            with st.spinner("搜索中..."):
                success, message, total_count, results, total_pages = get_questions_by_tag(
                    tag_search, st.session_state.tag_search_page, page_size
                )
                
                if success:
                    st.success(f"✅ {message}")
                    columns = ["标准问题ID", "问题", "答案", "标签"]
                    display_query_results(results, columns, "tag_search", total_count, total_pages, st.session_state.tag_search_page)
                else:
                    show_error_message(f"❌ 搜索失败: {message}")
        
        # 按评分范围搜索
        st.markdown("### 📊 按评分范围搜索")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            min_score = st.number_input("最低分", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
        with col2:
            max_score = st.number_input("最高分", min_value=0.0, max_value=100.0, value=100.0, step=0.1)
        with col3:
            search_by_score = st.button("🔍 搜索", key="search_by_score")
        
        if search_by_score:
            if "score_search_page" not in st.session_state:
                st.session_state.score_search_page = 1
            
            with st.spinner("搜索中..."):
                success, message, total_count, results, total_pages = get_answers_by_score_range(
                    min_score, max_score, st.session_state.score_search_page, page_size
                )
                
                if success:
                    st.success(f"✅ {message}")
                    columns = ["答案ID", "答案内容", "评分", "问题", "模型名称"]
                    display_query_results(results, columns, "score_search", total_count, total_pages, st.session_state.score_search_page)
                else:
                    show_error_message(f"❌ 搜索失败: {message}")
        
        # 内容搜索
        st.markdown("### 📝 内容搜索")
        col1, col2 = st.columns([3, 1])
        with col1:
            content_search = st.text_input("输入搜索关键词", key="content_search_input")
        with col2:
            search_content_btn = st.button("🔍 搜索", key="search_content")
        
        if search_content_btn and content_search:
            if "content_search_page" not in st.session_state:
                st.session_state.content_search_page = 1
            
            with st.spinner("搜索中..."):
                success, message, total_count, results, total_pages = search_content(
                    content_search, st.session_state.content_search_page, page_size
                )
                
                if success:
                    st.success(f"✅ {message}")
                    columns = ["内容类型", "ID", "内容", "标签"]
                    display_query_results(results, columns, "content_search", total_count, total_pages, st.session_state.content_search_page)
                else:
                    show_error_message(f"❌ 搜索失败: {message}")

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
elif menu == "🎯 LLM评估":
    st.header("🎯 LLM评估")
    
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

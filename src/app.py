import streamlit as st
import pandas as pd
import mysql.connector
import json #确保导入json模块
import os
from database import (create_tables, get_connection, get_table_names, get_table_data, execute_query, batch_import_json_data, 
                     get_all_questions_with_answers, get_questions_with_tags, get_llm_evaluation_results, 
                     get_top_scored_answers, get_question_answer_pairs, get_model_performance_comparison,
                     get_questions_by_tag, get_answers_by_score_range, get_recent_updates, search_content,
                     get_database_statistics, get_tag_distribution, get_model_cost_analysis, 
                     get_evaluation_trends, get_answer_length_analysis, get_question_complexity_analysis,
                     get_orphan_records, get_evaluation_score_distribution) # 导入新的查询函数
from utils import (show_success_message, show_error_message, show_table_data, show_table_schema, 
                   download_sample_json, get_table_schema, show_warning_message, safe_string, safe_text_preview)

# 导入认证相关模块
from auth import require_login, require_admin
from components.auth_ui import (
    show_login_form, show_register_form, show_user_info, 
    show_change_password_form, show_admin_panel, show_auth_sidebar,
    initialize_auth_system
)

# 导入答案标注模块
from components.answer_annotation import create_answer_annotation_ui

# 导入LLM评估模块
try:
    from llm_evaluator import (
        evaluator, 
        evaluate_standard_pairs, 
        get_model_statistics
    )
    LLM_EVALUATOR_AVAILABLE = True
except ImportError as e:
    print(f"LLM评估模块导入失败: {e}")
    LLM_EVALUATOR_AVAILABLE = False

# 页面配置
st.set_page_config(
    page_title="LLM问答评估系统",
    page_icon="Q",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化认证系统
# if not initialize_auth_system():
#     st.error("❌ 认证系统初始化失败，请检查数据库连接")
#     st.stop()

# 检查登录状态
# if not require_login():
#     # 显示登录页面
#     col1, col2, col3 = st.columns([1, 2, 1])
    
#     with col2:
#         st.title("🔐 LLM问答评估系统")
#         st.markdown("---")
#         st.markdown("**请登录以继续使用系统**")
        
#         # 显示注册表单或登录表单
#         if st.session_state.get('show_register', False):
#             show_register_form()
#         else:
#             user_info = show_login_form()
#             if user_info:
#                 st.session_state.user_info = user_info
#                 st.rerun()
    
#     st.stop()

# 用户已登录，显示主界面
# user_info = st.session_state.user_info

# 测试用
user_info = {
    'user_id': 1,
    'username': 'admin',
    'role': 'admin'
}

# 应用标题
col1, col2 = st.columns([3, 1])
with col1:
    st.title("LLM问答评估系统")
    st.markdown("本系统用于LLM问答数据的管理、标注和评估，支持多种模型评估比对")

with col2:
    # 显示用户信息
    if st.button("👤 个人中心", use_container_width=True):
        st.session_state.show_user_center = True

st.markdown("---")

# 检查是否显示个人中心
if st.session_state.get('show_user_center', False):
    show_user_info(user_info)
    
    if st.session_state.get('show_change_password', False):
        show_change_password_form(user_info['user_id'])
    
    if st.button("返回主页"):
        for key in ['show_user_center', 'show_change_password']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    st.stop()

# 检查是否显示管理员面板
if st.session_state.get('show_admin_panel', False):
    show_admin_panel()
    
    if st.button("返回主页"):
        if 'show_admin_panel' in st.session_state:
            del st.session_state.show_admin_panel
        st.rerun()
    
    st.stop()

tables_num = 0

    
with st.expander("使用说明"):
    st.markdown("""
    **基本功能介绍：**
    - **数据库管理**：创建和查看表结构，查看表数据
    - **LLM评估**：使用多种LLM模型评估问答质量
    - **数据导入**：导入现有数据到系统
    - **答案标注**：标注原始问题和答案为标准问答
    """)

# 侧边栏设置
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; margin-bottom: 1rem;'>
        <h1>功能菜单</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # 根据用户角色显示不同的功能选项
    if user_info['role'] == 'admin':
        menu_options = ["数据库管理", "LLM评估", "数据导入", "答案标注", "用户管理"]
    else:
        menu_options = ["LLM评估", "数据导入", "答案标注"]
    
    menu = st.radio(
        "功能菜单选项",
        menu_options,
        label_visibility="collapsed"
    )
    
    # 添加权限检查说明
    if user_info['role'] != 'admin' and menu in ["数据库管理", "数据导入"]:
        st.warning("⚠️ 部分功能需要管理员权限")
    
    # 显示系统状态和查询菜单
    st.markdown("---")
    st.markdown("### 查询功能")
    
    # 基础查询下拉菜单
    basic_query = st.selectbox(
        "基础查询",
        ["请选择查询类型", "查看所有问题答案", "查看标签问题", "查看问答配对"],
        key="basic_query_select"
    )
    
    # 关联查询下拉菜单
    relation_query = st.selectbox(
        "关联查询", 
        ["请选择查询类型", "LLM评估结果", "高分答案排行", "最近更新"],
        key="relation_query_select"
    )
    
    # 统计分析下拉菜单
    stats_query = st.selectbox(
        "统计分析",
        ["请选择分析类型", "数据库总览", "模型性能比较", "标签分布统计", "模型成本分析", 
         "答案长度分析", "评估趋势分析", "问题复杂度分析", "查找孤立记录", "评分分布图"],
        key="stats_query_select"
    )
    
    # 高级搜索下拉菜单
    search_query = st.selectbox(
        "高级搜索",
        ["请选择搜索类型", "按标签搜索", "按评分范围搜索", "内容搜索"],
        key="search_query_select"
    )

    # 显示认证状态
    show_auth_sidebar()
    
    

# 查询功能处理 - 检查是否有查询选择
query_selected = (basic_query != "请选择查询类型" or 
                 relation_query != "请选择查询类型" or 
                 stats_query != "请选择分析类型" or 
                 search_query != "请选择搜索类型")

if query_selected:
    # 分页控制函数
    def show_pagination_controls(key_prefix, total_pages, current_page):
        """显示分页控制组件"""
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("首页", key=f"{key_prefix}_first") and current_page > 1:
                st.session_state[f"{key_prefix}_page"] = 1
                st.rerun()
        
        with col2:
            if st.button("上页", key=f"{key_prefix}_prev") and current_page > 1:
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
            if st.button("下页", key=f"{key_prefix}_next") and current_page < total_pages:
                st.session_state[f"{key_prefix}_page"] = current_page + 1
                st.rerun()
        
        with col5:
            if st.button("末页", key=f"{key_prefix}_last") and current_page < total_pages:
                st.session_state[f"{key_prefix}_page"] = total_pages
                st.rerun()
    
    def display_query_results(results, columns, key_prefix, total_count, total_pages, current_page):
        """显示查询结果"""
        if results:
            df = pd.DataFrame(results, columns=columns)
            st.dataframe(df, use_container_width=True)
            
            # 显示统计信息
            st.info(f"总记录数: {total_count} | 当前页: {current_page}/{total_pages} | 当前显示: {len(results)} 条")
            
            # 分页控制
            show_pagination_controls(key_prefix, total_pages, current_page)
        else:
            st.warning("未找到相关数据")
    
    # 设置每页显示条数
    page_size = st.selectbox("每页显示条数", [5, 10, 20, 50], index=1, key="query_page_size")
    
    # 基础查询内容
    if basic_query == "查看所有问题答案":
        st.header("查看所有问题答案")
        st.markdown("*查询原始问题及其对应的原始答案和标准答案*")
        
        # 初始化或重置查询状态
        if st.button("开始查询", key="all_qa", use_container_width=True):
            st.session_state.all_qa_queried = True
            st.session_state.all_qa_page = 1
        
        # 执行查询逻辑
        if st.session_state.get('all_qa_queried', False):
            # 初始化页码
            if "all_qa_page" not in st.session_state:
                st.session_state.all_qa_page = 1
            
            with st.spinner("正在查询问题和答案..."):
                success, message, total_count, results, total_pages = get_all_questions_with_answers(
                    st.session_state.all_qa_page, page_size
                )
                
                if success:
                    st.success(f"{message} - 找到 {total_count} 条记录")
                    
                    if results:
                        columns = ["问题内容",  "标准答案内容"]
                        
                        # 美化数据展示
                        st.markdown("#### 查询结果")
                        with st.container():
                            df = pd.DataFrame(results, columns=columns)
                            
                            # 添加序号
                            df.index = df.index + 1 + (st.session_state.all_qa_page - 1) * page_size
                            df.index.name = "序号"
                            
                            # 使用expander展示每条记录
                            for idx, row in df.iterrows():
                                # 使用安全函数处理内容，避免None值错误
                                question_preview = safe_text_preview(row['问题内容'], 50, "暂无问题内容")
                                
                                with st.expander(f"记录 #{idx}: {question_preview}"):
                                    col1, col2, col3 = st.columns([1, 1, 1])
                                    
                                    with col1:
                                        st.markdown("**问题内容:**")
                                        question_content = safe_string(row['问题内容'], "暂无问题内容")
                                        st.info(question_content)
                                    
                                    with col2:
                                        st.markdown("**标准答案内容:**")
                                        std_answer_content = safe_string(row['标准答案内容'], "暂无标准答案")
                                        if std_answer_content != "暂无标准答案":
                                            st.success(std_answer_content)
                                        else:
                                            st.warning(std_answer_content)
                            
                            # 分页信息和控制
                            st.info(f"总记录数: {total_count} | 当前页: {st.session_state.all_qa_page}/{total_pages} | 当前显示: {len(results)} 条")
                            show_pagination_controls("all_qa", total_pages, st.session_state.all_qa_page)
                    else:
                        st.warning("未找到相关数据")
                else:
                    st.error(f"查询失败: {message}")
    
    elif basic_query == "查看标签问题":
        st.header("查看标签问题")
        st.markdown("*查询带有标签分类的标准问题*")
        
        # 初始化或重置查询状态
        if st.button("开始查询", key="tagged_questions", use_container_width=True):
            st.session_state.tagged_q_queried = True
            st.session_state.tagged_q_page = 1
        
        # 执行查询逻辑
        if st.session_state.get('tagged_q_queried', False):
            # 初始化页码
            if "tagged_q_page" not in st.session_state:
                st.session_state.tagged_q_page = 1
            
            with st.spinner("正在查询标签问题..."):
                success, message, total_count, results, total_pages = get_questions_with_tags(
                    st.session_state.tagged_q_page, page_size
                )
                
                if success:
                    st.success(f"{message} - 找到 {total_count} 条记录")
                    
                    if results:
                        columns = ["标准问题ID", "问题内容", "标签名称", "原始问题"]
                        
                        # 美化数据展示
                        st.markdown("#### 查询结果")
                        with st.container():
                            df = pd.DataFrame(results, columns=columns)
                            df.index = df.index + 1 + (st.session_state.tagged_q_page - 1) * page_size
                            df.index.name = "序号"
                            
                            # 按标签分组显示
                            if not df.empty:
                                tags = df['标签名称'].unique()
                                for tag in tags:
                                    tag_data = df[df['标签名称'] == tag]
                                    
                                    with st.expander(f"标签: {tag} ({len(tag_data)} 条记录)", expanded=True):
                                        for idx, row in tag_data.iterrows():
                                            st.markdown(f"**问题 #{row['标准问题ID']}:**")
                                            
                                            col1, col2 = st.columns([2, 1])
                                            with col1:
                                                st.write(f"**标准问题:** {row['问题内容']}")
                                                if row['原始问题'] and row['原始问题'] != row['问题内容']:
                                                    st.write(f"**原始问题:** {row['原始问题']}")
                                            with col2:
                                                st.markdown(f"**{tag}**")
                                            
                                            st.markdown("---")
                            
                            # 分页信息和控制
                            st.info(f"总记录数: {total_count} | 当前页: {st.session_state.tagged_q_page}/{total_pages} | 当前显示: {len(results)} 条")
                            show_pagination_controls("tagged_q", total_pages, st.session_state.tagged_q_page)
                    else:
                        st.warning("未找到相关数据")
                else:
                    st.error(f"查询失败: {message}")
    
    elif basic_query == "查看问答配对":
        st.header("查看问答配对")
        st.markdown("*查询完整的标准问答配对信息，包含标签和更新历史*")
        
        # 初始化或重置查询状态
        if st.button("开始查询", key="qa_pairs", use_container_width=True):
            st.session_state.qa_pairs_queried = True
            st.session_state.qa_pairs_page = 1
        
        # 执行查询逻辑
        if st.session_state.get('qa_pairs_queried', False):
            # 初始化页码
            if "qa_pairs_page" not in st.session_state:
                st.session_state.qa_pairs_page = 1
            
            with st.spinner("正在查询问答配对..."):
                success, message, total_count, results, total_pages = get_question_answer_pairs(
                    st.session_state.qa_pairs_page, page_size
                )
                
                if success:
                    st.success(f"{message} - 找到 {total_count} 条记录")
                    
                    if results:
                        columns = ["配对ID", "问题", "答案", "标签", "最后操作", "更新信息"]
                        
                        # 美化数据展示
                        st.markdown("#### 查询结果")
                        with st.container():
                            df = pd.DataFrame(results, columns=columns)
                            df.index = df.index + 1 + (st.session_state.qa_pairs_page - 1) * page_size
                            df.index.name = "序号"
                            
                            # 卡片式展示每个问答配对
                            for idx, row in df.iterrows():
                                with st.container():
                                    st.markdown(f"""
                                    <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin: 10px 0; background-color: black;">
                                        <h4>Pair #{row['配对ID']}</h4>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    col1, col2 = st.columns([1, 1])
                                    
                                    with col1:
                                        st.markdown("**问题:**")
                                        st.info(row['问题'] if row['问题'] else "暂无问题")
                                        
                                        st.markdown("**标签:**")
                                        if row['标签']:
                                            st.success(f"#{row['标签']}")
                                        else:
                                            st.warning("无标签")
                                    
                                    with col2:
                                        st.markdown("**答案:**")
                                        st.success(row['答案'] if row['答案'] else "暂无答案")
                                        
                                        st.markdown("**更新信息:**")
                                        if row['最后操作']:
                                            st.info(f"操作: {row['最后操作']}")
                                        if row['更新信息']:
                                            st.caption(f"详情: {row['更新信息']}")
                                    
                                    st.markdown("---")
                            
                            # 分页信息和控制
                            st.info(f"总记录数: {total_count} | 当前页: {st.session_state.qa_pairs_page}/{total_pages} | 当前显示: {len(results)} 条")
                            show_pagination_controls("qa_pairs", total_pages, st.session_state.qa_pairs_page)
                    else:
                        st.warning("未找到相关数据")
                else:
                    st.error(f"查询失败: {message}")
    
    # 关联查询内容
    elif relation_query == "LLM评估结果":
        st.header("LLM评估结果")
        st.markdown("*查看各种LLM模型对答案的评估分数和详细结果*")
        
        # 初始化或重置查询状态
        if st.button("开始查询", key="llm_eval", use_container_width=True):
            st.session_state.llm_eval_queried = True
            st.session_state.llm_eval_page = 1
        
        # 执行查询逻辑
        if st.session_state.get('llm_eval_queried', False):
            # 初始化页码
            if "llm_eval_page" not in st.session_state:
                st.session_state.llm_eval_page = 1
            
            with st.spinner("正在查询LLM评估结果..."):
                success, message, total_count, results, total_pages = get_llm_evaluation_results(
                    st.session_state.llm_eval_page, page_size
                )
                
                if success:
                    st.success(f"{message} - 找到 {total_count} 条评估记录")
                    
                    if results:
                        columns = ["评估ID", "LLM模型", "模型参数", "评分", "标准答案", "LLM答案", "问题内容", "问题ID"]
                        
                        # 美化数据展示
                        st.markdown("#### 评估结果")
                        with st.container():
                            df = pd.DataFrame(results, columns=columns)
                            df.index = df.index + 1 + (st.session_state.llm_eval_page - 1) * page_size
                            df.index.name = "序号"
                            
                            # 按评分排序显示
                            for idx, row in df.iterrows():
                                # 根据评分设置颜色
                                score = float(row['评分']) if row['评分'] else 0
                                if score >= 80:
                                    score_color = "[高分]"  # 绿色
                                elif score >= 60:
                                    score_color = "[中等]"  # 黄色
                                else:
                                    score_color = "[低分]"  # 红色
                                
                                with st.expander(f"{score_color} [问题#{row['问题ID']}] 评估 #{row['评估ID']} - {row['LLM模型']} - 评分: {score:.1f}"):
                                    col1, col2 = st.columns([1, 1])
                                    
                                    with col1:
                                        st.markdown("**模型信息:**")
                                        st.info(f"模型: {row['LLM模型']}")
                                        st.info(f"参数量: {row['模型参数']}")
                                        
                                        st.markdown("**评估分数:**")
                                        st.metric("分数", f"{score:.1f}")
                                        
                                        # 现在所有记录都有真实的问题内容
                                        st.markdown("**问题:**")
                                        st.write(row['问题内容'])
                                    
                                    with col2:
                                        st.markdown("**标准答案:**")
                                        if row['标准答案']:
                                            st.success(row['标准答案'])
                                        else:
                                            st.warning("无标准答案")
                                        
                                        st.markdown("**LLM答案:**")
                                        if row['LLM答案']:
                                            st.info(row['LLM答案'])
                                        else:
                                            st.warning("无LLM答案")
                            
                            # 分页信息和控制
                            st.info(f"总记录数: {total_count} | 当前页: {st.session_state.llm_eval_page}/{total_pages} | 当前显示: {len(results)} 条")
                            show_pagination_controls("llm_eval", total_pages, st.session_state.llm_eval_page)
                    else:
                        st.warning("未找到评估数据")
                else:
                    st.error(f"查询失败: {message}")
    
    elif relation_query == "高分答案排行":
        st.header("高分答案排行")
        st.markdown("*查看评分最高的答案排行榜*")
        
        # 初始化或重置查询状态
        if st.button("开始查询", key="top_answers", use_container_width=True):
            st.session_state.top_ans_queried = True
            st.session_state.top_ans_page = 1
        
        # 执行查询逻辑
        if st.session_state.get('top_ans_queried', False):
            # 初始化页码
            if "top_ans_page" not in st.session_state:
                st.session_state.top_ans_page = 1
            
            with st.spinner("正在查询高分答案..."):
                success, message, total_count, results, total_pages = get_top_scored_answers(
                    st.session_state.top_ans_page, page_size
                )
                
                if success:
                    st.success(f"{message} - 找到 {total_count} 条高分答案")
                    
                    if results:
                        columns = ["答案ID", "答案内容", "平均分", "评估次数", "问题内容"]
                        
                        # 美化数据展示
                        st.markdown("#### 排行榜")
                        with st.container():
                            df = pd.DataFrame(results, columns=columns)
                            
                            # 添加排名
                            for rank, (idx, row) in enumerate(df.iterrows(), 1):
                                # 排名徽章
                                if rank == 1:
                                    rank_badge = "[第1名]"
                                elif rank == 2:
                                    rank_badge = "[第2名]" 
                                elif rank == 3:
                                    rank_badge = "[第3名]"
                                else:
                                    rank_badge = f"[第{rank}名]"
                                
                                avg_score = float(row['平均分']) if row['平均分'] else 0
                                eval_count = int(row['评估次数']) if row['评估次数'] else 0
                                
                                with st.container():
                                    st.markdown(f"""
                                    <div style="border: 2px solid #gold; border-radius: 10px; padding: 15px; margin: 10px 0; background: linear-gradient(45deg, #fff3cd, #f8f9fa);">
                                        <h4>{rank_badge} 答案 #{row['答案ID']}</h4>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    col1, col2, col3 = st.columns([1, 1, 1])
                                    
                                    with col1:
                                        st.metric("平均评分", f"{avg_score:.1f}", delta=f"{avg_score-75:.1f}")
                                        st.metric("评估次数", eval_count)
                                    
                                    with col2:
                                        st.markdown("**答案内容:**")
                                        st.success(row['答案内容'] if row['答案内容'] else "无答案内容")
                                    
                                    with col3:
                                        st.markdown("**对应问题:**")
                                        # 只显示真实的问题内容，过滤掉占位符文本
                                        if (row['问题内容'] and 
                                            not ('暂无关联问题' in str(row['问题内容']) or 
                                                 '数据缺失' in str(row['问题内容']))):
                                            st.info(row['问题内容'])
                                        else:
                                            st.warning("无关联问题")
                                    
                                    st.markdown("---")
                            
                            # 分页信息和控制
                            st.info(f"总记录数: {total_count} | 当前页: {st.session_state.top_ans_page}/{total_pages} | 当前显示: {len(results)} 条")
                            show_pagination_controls("top_ans", total_pages, st.session_state.top_ans_page)
                    else:
                        st.warning("未找到高分答案")
                else:
                    st.error(f"查询失败: {message}")
    
    elif relation_query == "最近更新":
        st.header("最近更新")
        st.markdown("*查看最近的数据更新记录和操作历史*")
        
        # 初始化或重置查询状态
        if st.button("开始查询", key="recent_updates", use_container_width=True):
            st.session_state.recent_up_queried = True
            st.session_state.recent_up_page = 1
        
        # 执行查询逻辑
        if st.session_state.get('recent_up_queried', False):
            # 初始化页码
            if "recent_up_page" not in st.session_state:
                st.session_state.recent_up_page = 1
            
            with st.spinner("正在查询更新记录..."):
                success, message, total_count, results, total_pages = get_recent_updates(
                    st.session_state.recent_up_page, page_size
                )
                
                if success:
                    st.success(f"{message} - 找到 {total_count} 条更新记录")
                    
                    if results:
                        columns = ["版本号", "操作类型", "更新描述", "影响问题数", "影响答案数"]
                        
                        # 美化数据展示
                        st.markdown("#### 更新历史")
                        with st.container():
                            df = pd.DataFrame(results, columns=columns)
                            
                            # 时间线式展示
                            for idx, row in df.iterrows():
                                operation_type = row['操作类型']
                                
                                # 根据操作类型设置图标和颜色
                                if operation_type in ['CREATE', 'INSERT', '创建', '新增']:
                                    op_icon = "[新增]"
                                    op_color = "#d4edda"
                                elif operation_type in ['UPDATE', 'MODIFY', '更新', '修改']:
                                    op_icon = "[更新]"
                                    op_color = "#d1ecf1"
                                elif operation_type in ['DELETE', 'REMOVE', '删除']:
                                    op_icon = "[删除]"
                                    op_color = "#f8d7da"
                                else:
                                    op_icon = "[操作]"
                                    op_color = "#f3f3f3"
                                
                                with st.container():
                                    st.markdown(f"""
                                    <div style="border-left: 4px solid #007bff; background-color: {op_color}; padding: 15px; margin: 10px 0; border-radius: 5px;">
                                        <h5>{op_icon} 版本 {row['版本号']} - {operation_type}</h5>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    col1, col2 = st.columns([2, 1])
                                    
                                    with col1:
                                        st.markdown("**更新描述:**")
                                        st.write(row['更新描述'] if row['更新描述'] else "无描述")
                                    
                                    with col2:
                                        st.markdown("**影响范围:**")
                                        if row['影响问题数']:
                                            st.info(f"问题: {row['影响问题数']} 条")
                                        if row['影响答案数']:
                                            st.info(f"答案: {row['影响答案数']} 条")
                                    
                                    st.markdown("---")
                            
                            # 分页信息和控制
                            st.info(f"总记录数: {total_count} | 当前页: {st.session_state.recent_up_page}/{total_pages} | 当前显示: {len(results)} 条")
                            show_pagination_controls("recent_up", total_pages, st.session_state.recent_up_page)
                    else:
                        st.warning("未找到更新记录")
                else:
                    st.error(f"查询失败: {message}")
    
    # 统计分析内容
    elif stats_query == "数据库总览":
        st.header("数据库总览")
        if st.button("获取数据库统计", key="db_stats"):
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
    
    elif stats_query == "模型性能比较":
        st.header("模型性能比较")
        
        # 初始化或重置查询状态
        if st.button("开始分析", key="model_performance"):
            st.session_state.model_perf_queried = True
            st.session_state.model_perf_page = 1
        
        # 执行查询逻辑
        if st.session_state.get('model_perf_queried', False):
            if "model_perf_page" not in st.session_state:
                st.session_state.model_perf_page = 1
            
            with st.spinner("查询中..."):
                success, message, total_count, results, total_pages = get_model_performance_comparison(
                    st.session_state.model_perf_page, page_size
                )
                
                if success:
                    st.success(f"{message}")
                    columns = ["模型名称", "参数量", "总评估数", "平均分", "最高分", "最低分", "成本(每百万token)"]
                    display_query_results(results, columns, "model_perf", total_count, total_pages, st.session_state.model_perf_page)
                else:
                    show_error_message(f"查询失败: {message}")
    
    elif stats_query == "标签分布统计":
        st.header("标签分布统计")
        
        # 初始化或重置查询状态
        if st.button("开始统计", key="tag_dist"):
            st.session_state.tag_dist_queried = True
            st.session_state.tag_dist_page = 1
        
        # 执行查询逻辑
        if st.session_state.get('tag_dist_queried', False):
            if "tag_dist_page" not in st.session_state:
                st.session_state.tag_dist_page = 1
            
            with st.spinner("统计中..."):
                success, message, total_count, results, total_pages = get_tag_distribution(
                    st.session_state.tag_dist_page, page_size
                )
                
                if success:
                    st.success(f"{message}")
                    columns = ["标签名称", "问题数量", "答案数量"]
                    display_query_results(results, columns, "tag_dist", total_count, total_pages, st.session_state.tag_dist_page)
                else:
                    show_error_message(f"统计失败: {message}")
    
    elif stats_query == "模型成本分析":
        st.header("模型成本分析")
        
        # 初始化或重置查询状态
        if st.button("开始分析", key="cost_analysis"):
            st.session_state.cost_queried = True
            st.session_state.cost_page = 1
        
        # 执行查询逻辑
        if st.session_state.get('cost_queried', False):
            if "cost_page" not in st.session_state:
                st.session_state.cost_page = 1
            
            with st.spinner("分析中..."):
                success, message, total_count, results, total_pages = get_model_cost_analysis(
                    st.session_state.cost_page, page_size
                )
                
                if success:
                    st.success(f"{message}")
                    columns = ["模型名称", "参数量", "单价(/百万token)", "总评估数", "平均分", "预估总成本"]
                    display_query_results(results, columns, "cost", total_count, total_pages, st.session_state.cost_page)
                else:
                    show_error_message(f"分析失败: {message}")
    
    elif stats_query == "答案长度分析":
        st.header("答案长度分析")
        
        # 初始化或重置查询状态
        if st.button("开始分析", key="length_analysis"):
            st.session_state.length_queried = True
            st.session_state.length_page = 1
        
        # 执行查询逻辑
        if st.session_state.get('length_queried', False):
            if "length_page" not in st.session_state:
                st.session_state.length_page = 1
            
            with st.spinner("分析中..."):
                success, message, total_count, results, total_pages = get_answer_length_analysis(
                    st.session_state.length_page, page_size
                )
                
                if success:
                    st.success(f"{message}")
                    columns = ["答案ID", "答案长度", "平均分", "评估次数", "长度类别", "答案预览"]
                    display_query_results(results, columns, "length", total_count, total_pages, st.session_state.length_page)
                else:
                    show_error_message(f"分析失败: {message}")
    
    elif stats_query == "评估趋势分析":
        st.header("评估趋势分析")
        
        # 初始化或重置查询状态
        if st.button("开始分析", key="eval_trends"):
            st.session_state.trends_queried = True
            st.session_state.trends_page = 1
        
        # 执行查询逻辑
        if st.session_state.get('trends_queried', False):
            if "trends_page" not in st.session_state:
                st.session_state.trends_page = 1
            
            with st.spinner("分析中..."):
                success, message, total_count, results, total_pages = get_evaluation_trends(
                    st.session_state.trends_page, page_size
                )
                
                if success:
                    st.success(f"{message}")
                    columns = ["评估ID", "模型名称", "评分", "评分等级", "答案预览"]
                    display_query_results(results, columns, "trends", total_count, total_pages, st.session_state.trends_page)
                else:
                    show_error_message(f"分析失败: {message}")
    
    elif stats_query == "问题复杂度分析":
        st.header("问题复杂度分析")
        
        # 初始化或重置查询状态
        if st.button("开始分析", key="complexity_analysis"):
            st.session_state.complex_queried = True
            st.session_state.complex_page = 1
        
        # 执行查询逻辑
        if st.session_state.get('complex_queried', False):
            if "complex_page" not in st.session_state:
                st.session_state.complex_page = 1
            
            with st.spinner("分析中..."):
                success, message, total_count, results, total_pages = get_question_complexity_analysis(
                    st.session_state.complex_page, page_size
                )
                
                if success:
                    st.success(f"{message}")
                    columns = ["问题ID", "问题内容", "问题长度", "标签", "答案数", "平均分", "复杂度"]
                    display_query_results(results, columns, "complex", total_count, total_pages, st.session_state.complex_page)
                else:
                    show_error_message(f"分析失败: {message}")
    
    elif stats_query == "查找孤立记录":
        st.header("查找孤立记录")
        
        # 初始化或重置查询状态
        if st.button("开始检查", key="orphan_records"):
            st.session_state.orphan_queried = True
            st.session_state.orphan_page = 1
        
        # 执行查询逻辑
        if st.session_state.get('orphan_queried', False):
            if "orphan_page" not in st.session_state:
                st.session_state.orphan_page = 1
            
            with st.spinner("检查中..."):
                success, message, total_count, results, total_pages = get_orphan_records(
                    st.session_state.orphan_page, page_size
                )
                
                if success:
                    if total_count > 0:
                        st.warning(f"发现 {total_count} 条孤立记录")
                        columns = ["记录类型", "ID", "内容", "问题描述"]
                        display_query_results(results, columns, "orphan", total_count, total_pages, st.session_state.orphan_page)
                    else:
                        st.success("未发现孤立记录，数据完整性良好")
                else:
                    show_error_message(f"检查失败: {message}")
    
    elif stats_query == "评分分布图":
        st.header("评分分布图")
        if st.button("生成分布图", key="score_distribution"):
            with st.spinner("生成分布图..."):
                success, message, results = get_evaluation_score_distribution()
                
                if success and results:
                    st.success("评分分布统计")
                    
                    # 创建分布图
                    df_dist = pd.DataFrame(results, columns=["分数区间", "数量", "百分比"])
                    
                    col_chart1, col_chart2 = st.columns(2)
                    
                    with col_chart1:
                        st.bar_chart(df_dist.set_index("分数区间")["数量"])
                        st.caption("评分区间分布 - 数量")
                    
                    with col_chart2:
                        st.bar_chart(df_dist.set_index("分数区间")["百分比"])
                        st.caption("评分区间分布 - 百分比")
                    
                    # 显示详细数据
                    with st.expander("详细分布数据"):
                        st.dataframe(df_dist, use_container_width=True)
                else:
                    show_error_message(f"生成失败: {message if not success else '暂无评估数据'}")
    
    # 高级搜索内容
    elif search_query == "按标签搜索":
        st.header("按标签搜索")
        col1, col2 = st.columns([3, 1])
        with col1:
            tag_search = st.text_input("输入标签名称", key="tag_search_input")
        with col2:
            search_by_tag = st.button("搜索", key="search_by_tag")
        
        # 初始化或重置搜索状态
        if search_by_tag and tag_search:
            st.session_state.tag_search_queried = True
            st.session_state.tag_search_term = tag_search
            st.session_state.tag_search_page = 1
        
        # 执行搜索逻辑
        if (st.session_state.get('tag_search_queried', False) and 
            st.session_state.get('tag_search_term')):
            if "tag_search_page" not in st.session_state:
                st.session_state.tag_search_page = 1
            
            with st.spinner("搜索中..."):
                success, message, total_count, results, total_pages = get_questions_by_tag(
                    st.session_state.tag_search_term, st.session_state.tag_search_page, page_size
                )
                
                if success:
                    st.success(f"{message}")
                    columns = ["标准问题ID", "问题", "答案", "标签"]
                    display_query_results(results, columns, "tag_search", total_count, total_pages, st.session_state.tag_search_page)
                else:
                    show_error_message(f"搜索失败: {message}")
    
    elif search_query == "按评分范围搜索":
        st.header("按评分范围搜索")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            min_score = st.number_input("最低分", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
        with col2:
            max_score = st.number_input("最高分", min_value=0.0, max_value=100.0, value=100.0, step=0.1)
        with col3:
            search_by_score = st.button("搜索", key="search_by_score")
        
        # 初始化或重置搜索状态
        if search_by_score:
            st.session_state.score_search_queried = True
            st.session_state.score_search_min = min_score
            st.session_state.score_search_max = max_score
            st.session_state.score_search_page = 1
        
        # 执行搜索逻辑
        if st.session_state.get('score_search_queried', False):
            if "score_search_page" not in st.session_state:
                st.session_state.score_search_page = 1
            
            with st.spinner("搜索中..."):
                success, message, total_count, results, total_pages = get_answers_by_score_range(
                    st.session_state.get('score_search_min', 0.0), 
                    st.session_state.get('score_search_max', 100.0), 
                    st.session_state.score_search_page, page_size
                )
                
                if success:
                    st.success(f"{message}")
                    columns = ["答案ID", "答案内容", "评分", "问题", "模型名称"]
                    display_query_results(results, columns, "score_search", total_count, total_pages, st.session_state.score_search_page)
                else:
                    show_error_message(f"搜索失败: {message}")
    
    elif search_query == "内容搜索":
        st.header("内容搜索")
        col1, col2 = st.columns([3, 1])
        with col1:
            content_search = st.text_input("输入搜索关键词", key="content_search_input")
        with col2:
            search_content_btn = st.button("搜索", key="search_content")
        
        # 初始化或重置搜索状态
        if search_content_btn and content_search:
            st.session_state.content_search_queried = True
            st.session_state.content_search_term = content_search
            st.session_state.content_search_page = 1
        
        # 执行搜索逻辑
        if (st.session_state.get('content_search_queried', False) and 
            st.session_state.get('content_search_term')):
            if "content_search_page" not in st.session_state:
                st.session_state.content_search_page = 1
            
            with st.spinner("搜索中..."):
                success, message, total_count, results, total_pages = search_content(
                    st.session_state.content_search_term, st.session_state.content_search_page, page_size
                )
                
                if success:
                    st.success(f"{message}")
                    columns = ["内容类型", "ID", "内容", "标签"]
                    display_query_results(results, columns, "content_search", total_count, total_pages, st.session_state.content_search_page)
                else:
                    show_error_message(f"搜索失败: {message}")
    
    # 默认显示
    else:
        st.header("智能查询系统")
        st.markdown("*请使用左侧的下拉菜单选择您需要的查询功能*")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 基础查询")
            st.markdown("""
            - **查看所有问题答案**: 展示原始问题与对应的答案关系
            - **查看标签问题**: 按标签分类展示标准化问题
            - **查看问答配对**: 展示完整的问答配对信息
            """)
            
            st.markdown("#### 关联查询")
            st.markdown("""
            - **LLM评估结果**: 查看各种LLM模型的评估分数
            - **高分答案排行**: 查看评分最高的答案排行榜
            - **最近更新**: 查看最近的数据更新记录
            """)
        
        with col2:
            st.markdown("#### 统计分析")
            st.markdown("""
            - **数据库总览**: 查看数据库整体统计信息
            - **模型性能比较**: 对比不同LLM模型的性能
            - **标签分布统计**: 分析标签的分布情况
            - **各种专项分析**: 成本、长度、趋势等分析
            """)
            
            st.markdown("#### 高级搜索")
            st.markdown("""
            - **按标签搜索**: 根据标签名称搜索相关内容
            - **按评分范围搜索**: 在指定评分范围内搜索
            - **内容搜索**: 在问题和答案内容中搜索关键词
            """)
        
        st.markdown("---")
        
        with st.expander("使用说明"):
            st.markdown("""
            **如何使用:**
            
            1. **选择查询类型**: 在左侧侧边栏的下拉菜单中选择您需要的查询功能
            2. **设置参数**: 在主界面中设置每页显示条数等参数
            3. **执行查询**: 点击"开始查询"或相应的操作按钮
            4. **查看结果**: 结果将以美化的格式展示，支持分页浏览
            
            **注意事项:**
            - 确保数据库中有相关数据才能查询到结果
            - 某些分析功能需要大量数据才能产生有意义的结果
            - 如遇到问题，请先检查数据库连接状态
            """)

# 数据库管理页面
elif menu == "数据库管理":
    st.header("数据库管理")
    
    # 权限检查 - MAY NEED REVIEW
    if user_info['role'] != 'admin':
        st.warning("⚠️ 数据库管理功能需要管理员权限")
        st.info("您可以查看数据，但无法进行表操作")
        admin_tabs = ["数据查看"]
    else:
        admin_tabs = ["表操作", "数据查看"]
    
    # 创建选项卡
    if len(admin_tabs) == 1:
        tab2 = st.container()
    else:
        tab1, tab2 = st.tabs(admin_tabs)
    
    # 只在管理员模式下显示表操作
    if user_info['role'] == 'admin':
        with tab1:
            st.subheader("数据库表操作")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # 创建表
                if st.button("一键建表", key="create_tables"):
                    with st.spinner("创建表中..."):
                        results = create_tables()   
                        all_success = all([result[0] for result in results])
                        
                        if all_success:
                            show_success_message("所有表创建成功！")
                        else:
                            failed_tables = [f"表 {i+1}: {result[1]}" for i, result in enumerate(results) if not result[0]]
                            show_error_message(f"部分表创建失败: {', '.join(failed_tables)}")
                if st.button("一键查询", key="view_table_schema"):
                    tables = get_table_names()
                    if tables:
                        st.info(f"当前数据库表数量: {len(tables)}")
                    else:
                        st.warning("数据库中没有表")
            
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
            st.info("数据库中没有表或无法连接到数据库")
        else:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # 表选择器
                selected_table = st.selectbox(
                    "选择要查看的表",
                    tables,
                    format_func=lambda x: f"{x}"
                )
            
            with col2:
                view_option = st.radio(
                    "查看选项",
                    ["数据", "结构"]
                )
            
            if view_option == "数据":
                if st.button("加载数据", key="load_data"):
                    with st.spinner("加载数据中..."):
                        success, data = get_table_data(selected_table)
                        
                        if success:
                            show_table_data(selected_table, data)
                        else:
                            show_error_message(f"获取表数据失败: {data}")
            else:
                if st.button("查看结构", key="view_schema"):
                    with st.spinner("加载表结构..."):
                        conn = get_connection()
                        if conn:
                            show_table_schema(selected_table, conn)
                            conn.close()
                        else:
                            show_error_message("无法连接到数据库")

# LLM评估页面
elif menu == "LLM评估":
    st.header("LLM评估")
    
    if not LLM_EVALUATOR_AVAILABLE:
        st.error("❌ LLM评估模块不可用，请检查依赖安装和API密钥配置")
        st.info("请确保已安装：pip install langchain langchain-openai langchain-anthropic")
        st.info("并在根目录创建.env文件配置API密钥（参考env_example.txt）")
    else:
        # 创建选项卡
        tab1, tab2, tab3 = st.tabs(["评估配置", "评估结果", "模型比对"])
        
        with tab1:
            st.subheader("配置评估参数")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 模型选择")
                
                # 获取可用模型
                available_models = evaluator.get_available_models()
                model = st.selectbox(
                    "选择LLM模型",
                    available_models,
                    help="选择用于评估的LLM模型"
                )
                
                # API密钥状态检查
                if model.startswith("gpt"):
                    api_status = "✅ OpenAI" if os.getenv("OPENAI_API_KEY") else "❌ 需要OPENAI_API_KEY"
                elif model.startswith("claude"):
                    api_status = "✅ Anthropic" if os.getenv("ANTHROPIC_API_KEY") else "❌ 需要ANTHROPIC_API_KEY"
                else:
                    api_status = "未知"
                
                st.info(f"API状态: {api_status}")
            
            with col2:
                st.markdown("#### 评估方法")
                eval_method = st.selectbox(
                    "评估方法",
                    ["综合评分", "内容相关性", "答案准确性", "解释清晰度"],
                    help="选择评估的方法和标准"
                )
                
                eval_metrics = st.multiselect(
                    "关注指标",
                    ["正确性", "完整性", "清晰度", "专业性", "相关性"],
                    default=["正确性", "完整性", "清晰度"],
                    help="选择重点关注的评估指标"
                )
            
            st.markdown("### 评估范围")
            
            eval_option = st.radio(
                "评估范围选项",
                ["评估所有标准问答对", "评估特定标签的问答对", "评估特定问题ID"],
                help="选择要评估的问答对范围"
            )
            
            # 根据选择显示不同的配置选项
            tag_to_eval = None
            question_id = None
            eval_limit = None
            
            if eval_option == "评估特定标签的问答对":
                col1, col2 = st.columns([2, 1])
                with col1:
                    tag_to_eval = st.text_input("输入标签名称", placeholder="例如: database, sql")
                with col2:
                    eval_limit = st.number_input("限制数量", min_value=1, value=10, help="限制评估的问答对数量")
            
            elif eval_option == "评估特定问题ID":
                question_id = st.number_input("输入问题Pair ID", min_value=1, value=1)
            
            else:  # 评估所有
                eval_limit = st.number_input("限制数量（可选）", min_value=1, value=50, help="限制评估数量以避免过多API调用")
            
            # 高级设置
            with st.expander("高级设置"):
                criteria = st.text_area(
                    "自定义评估标准", 
                    value="标准问答评估",
                    help="输入自定义的评估标准和要求"
                )
                
                show_progress = st.checkbox("显示详细进度", value=True)
                
            # 预估成本显示
            if eval_option == "评估所有标准问答对":
                # 获取总数
                pairs = evaluator.get_standard_pairs(limit=1)  # 获取一条来测试连接
                if pairs:
                    st.info("⚠️ 注意：评估所有问答对可能消耗大量API额度，建议先进行小范围测试")
            
            # 开始评估按钮
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                start_eval = st.button(
                    "🚀 开始评估", 
                    key="start_eval",
                    use_container_width=True,
                    help="点击开始LLM评估过程"
                )
            
            if start_eval:
                # 参数验证
                can_proceed = True
                
                if model.startswith("gpt") and not os.getenv("OPENAI_API_KEY"):
                    st.error("❌ 请配置OPENAI_API_KEY环境变量")
                    can_proceed = False
                elif model.startswith("claude") and not os.getenv("ANTHROPIC_API_KEY"):
                    st.error("❌ 请配置ANTHROPIC_API_KEY环境变量")
                    can_proceed = False
                
                # 确定评估参数
                if can_proceed:
                    if eval_option == "评估特定标签的问答对":
                        if not tag_to_eval:
                            st.error("❌ 请输入标签名称")
                            can_proceed = False
                        else:
                            eval_params = {
                                'tag_filter': tag_to_eval,
                                'limit': eval_limit
                            }
                    elif eval_option == "评估特定问题ID":
                        eval_params = {
                            'pair_id': question_id
                        }
                    else:
                        eval_params = {
                            'limit': eval_limit
                        }
                
                # 开始评估
                if can_proceed:
                    with st.spinner(f"正在使用 {model} 进行评估..."):
                        progress_container = st.container()
                        
                        try:
                            # 执行评估
                            result = evaluate_standard_pairs(
                                model_name=model,
                                **eval_params
                            )
                            
                            if result['success']:
                                st.success(f"✅ {result['message']}")
                                
                                # 显示评估统计
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("总问答对", result['total_pairs'])
                                with col2:
                                    st.metric("成功评估", result['success_count'])
                                with col3:
                                    st.metric("失败数量", result['fail_count'])
                                
                                # 显示详细结果
                                if result['results']:
                                    st.markdown("#### 评估结果详情")
                                    
                                    results_df = pd.DataFrame(result['results'])
                                    
                                    # 按成功/失败分组显示
                                    success_results = results_df[results_df['success'] == True]
                                    fail_results = results_df[results_df['success'] == False]
                                    
                                    if len(success_results) > 0:
                                        st.markdown("**成功评估的问答对:**")
                                        st.dataframe(
                                            success_results[['pair_id', 'question', 'score']],
                                            use_container_width=True
                                        )
                                    
                                    if len(fail_results) > 0:
                                        with st.expander(f"失败的评估 ({len(fail_results)}条)"):
                                            st.dataframe(
                                                fail_results[['pair_id', 'question', 'error']],
                                                use_container_width=True
                                            )
                            else:
                                st.error(f"❌ 评估失败: {result['message']}")
                                
                        except Exception as e:
                            st.error(f"❌ 评估过程出错: {str(e)}")
                            if 'logger' in globals():
                                logger.error(f"LLM评估错误: {e}", exc_info=True)
        
        with tab2:
            st.subheader("评估结果查看")
            
            # 刷新数据按钮
            if st.button("🔄 刷新数据", key="refresh_eval_results"):
                st.rerun()
            
            # 获取评估统计
            try:
                stats_result = get_model_statistics()
                
                if stats_result['success'] and stats_result['statistics']:
                    st.markdown("#### 模型评估统计")
                    
                    stats_df = pd.DataFrame(stats_result['statistics'])
                    
                    # 显示统计表格
                    st.dataframe(
                        stats_df.round(2),
                        use_container_width=True,
                        column_config={
                            "model_name": "模型名称",
                            "total_evaluations": "评估次数",
                            "avg_score": "平均分数",
                            "min_score": "最低分数",
                            "max_score": "最高分数",
                            "score_stddev": "分数标准差"
                        }
                    )
                    
                    # 可视化
                    if len(stats_df) > 0:
                        st.markdown("#### 模型性能对比图")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # 平均分数对比
                            import plotly.express as px
                            fig_avg = px.bar(
                                stats_df, 
                                x='model_name', 
                                y='avg_score',
                                title="各模型平均评分对比",
                                labels={'model_name': '模型', 'avg_score': '平均分数'}
                            )
                            st.plotly_chart(fig_avg, use_container_width=True)
                        
                        with col2:
                            # 评估次数对比
                            fig_count = px.pie(
                                stats_df,
                                values='total_evaluations',
                                names='model_name',
                                title="评估次数分布"
                            )
                            st.plotly_chart(fig_count, use_container_width=True)
                else:
                    st.info("📊 暂无评估数据，请先进行评估")
                    
            except Exception as e:
                st.error(f"❌ 获取评估统计失败: {str(e)}")
        
        with tab3:
            st.subheader("模型性能对比")
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.markdown("#### 对比选项")
                
                # 模型选择
                models_to_compare = st.multiselect(
                    "选择要对比的模型",
                    available_models,
                    default=available_models[:2] if len(available_models) >= 2 else available_models
                )
                
                # 对比维度
                comparison_metrics = st.multiselect(
                    "对比维度", 
                    ["平均分数", "最高分数", "最低分数", "评估次数", "分数稳定性"],
                    default=["平均分数", "评估次数"]
                )
                
                if st.button("生成对比报告"):
                    if len(models_to_compare) < 2:
                        st.warning("⚠️ 请至少选择两个模型进行对比")
                    else:
                        st.session_state.show_comparison = True
            
            with col2:
                if st.session_state.get('show_comparison', False):
                    st.markdown("#### 对比结果")
                    
                    try:
                        # 获取选中模型的统计数据
                        comparison_data = []
                        for model_name in models_to_compare:
                            model_stats = get_model_statistics(model_name)
                            if model_stats['success'] and model_stats['statistics']:
                                comparison_data.extend(model_stats['statistics'])
                        
                        if comparison_data:
                            comp_df = pd.DataFrame(comparison_data)
                            comp_df = comp_df[comp_df['model_name'].isin(models_to_compare)]
                            
                            # 生成对比图表
                            if "平均分数" in comparison_metrics and len(comp_df) > 0:
                                fig_comparison = px.radar(
                                    comp_df,
                                    r='avg_score',
                                    theta='model_name',
                                    title="模型平均分数雷达图",
                                    range_r=[0, 100]
                                )
                                st.plotly_chart(fig_comparison, use_container_width=True)
                            
                            # 显示详细对比表
                            st.markdown("**详细对比数据:**")
                            display_columns = ['model_name', 'total_evaluations', 'avg_score']
                            if 'min_score' in comp_df.columns:
                                display_columns.extend(['min_score', 'max_score', 'score_stddev'])
                            
                            st.dataframe(
                                comp_df[display_columns].round(2),
                                use_container_width=True
                            )
                            
                            # 生成结论
                            if len(comp_df) > 0:
                                best_model = comp_df.loc[comp_df['avg_score'].idxmax(), 'model_name']
                                most_stable = comp_df.loc[comp_df['score_stddev'].idxmin(), 'model_name'] if 'score_stddev' in comp_df.columns else "未知"
                                
                                st.markdown("#### 🎯 对比结论")
                                st.success(f"**最高平均分:** {best_model}")
                                if most_stable != "未知":
                                    st.info(f"**最稳定模型:** {most_stable}")
                        else:
                            st.warning("⚠️ 没有找到所选模型的评估数据")
                            
                    except Exception as e:
                        st.error(f"❌ 生成对比报告失败: {str(e)}")

# 答案标注页面
elif menu == "答案标注":
    st.header("📝 问题答案标注管理")
    st.markdown("*查看所有原始问题及其对应的原始答案，并将其标注为标准问题*")
    
    # 分页设置
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("搜索问题内容", placeholder="输入问题关键词进行搜索...", key="annotation_search")
    with col2:
        page_size = st.selectbox("每页显示数量", [5, 10, 20, 30], index=1, key="annotation_page_size")
    
    # 初始化页码和搜索状态
    if 'annotation_page' not in st.session_state:
        st.session_state.annotation_page = 1
    if 'annotation_search_term' not in st.session_state:
        st.session_state.annotation_search_term = ""
    if 'annotation_prev_page_size' not in st.session_state:
        st.session_state.annotation_prev_page_size = page_size
    
    # 检查搜索条件或页面大小变化，重置页码
    if (search_term != st.session_state.annotation_search_term or 
        page_size != st.session_state.annotation_prev_page_size):
        st.session_state.annotation_page = 1
        st.session_state.annotation_search_term = search_term
        st.session_state.annotation_prev_page_size = page_size
    
    # 构建查询
    search_condition = ""
    search_params = []
    
    if search_term:
        search_condition = "WHERE oq.content LIKE %s"
        search_params.append(f"%{search_term}%")
    
    # 获取总数
    count_query = f"""
    SELECT COUNT(DISTINCT oq.ori_qs_id)
    FROM ori_qs oq
    {search_condition}
    """
    
    success, count_result = execute_query(count_query, search_params, True)
    total_count = count_result[0][0] if success and count_result else 0
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
    
    # 获取问题和答案数据
    offset = (st.session_state.annotation_page - 1) * page_size
    
    data_query = f"""
    SELECT 
        oq.ori_qs_id,
        oq.content AS question_content,
        oq.created_at AS question_created,
        COUNT(oa.ori_ans_id) AS answer_count,
        CASE 
            WHEN EXISTS (SELECT 1 FROM standard_QS sq WHERE sq.ori_qs_id = oq.ori_qs_id) THEN '已标注'
            ELSE '未标注'
        END AS annotation_status
    FROM ori_qs oq
    LEFT JOIN ori_ans oa ON oq.ori_qs_id = oa.ori_qs_id
    {search_condition}
    GROUP BY oq.ori_qs_id, oq.content, oq.created_at
    ORDER BY oq.created_at DESC
    LIMIT %s OFFSET %s
    """
    
    query_params = search_params + [page_size, offset]
    success, questions_data = execute_query(data_query, query_params, True)
    
    if not success:
        st.error(f"数据获取失败: {questions_data}")
    elif not questions_data:
        st.info("暂无问题数据")
    else:
        # 分页控件
        if total_pages > 1:
            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
            
            with col1:
                if st.button("首页", key="annotation_first_page") and st.session_state.annotation_page > 1:
                    st.session_state.annotation_page = 1
                    st.rerun()
            
            with col2:
                if st.button("上页", key="annotation_prev_page") and st.session_state.annotation_page > 1:
                    st.session_state.annotation_page -= 1
                    st.rerun()
            
            with col3:
                new_page = st.number_input(
                    f"页码 (共 {total_pages} 页)", 
                    min_value=1, 
                    max_value=total_pages, 
                    value=st.session_state.annotation_page,
                    key="annotation_page_input"
                )
                if new_page != st.session_state.annotation_page:
                    st.session_state.annotation_page = new_page
                    st.rerun()
            
            with col4:
                if st.button("下页", key="annotation_next_page") and st.session_state.annotation_page < total_pages:
                    st.session_state.annotation_page += 1
                    st.rerun()
            
            with col5:
                if st.button("末页", key="annotation_last_page") and st.session_state.annotation_page < total_pages:
                    st.session_state.annotation_page = total_pages
                    st.rerun()
        
        st.markdown(f"### 📋 问题列表 (共 {total_count} 条记录，第 {st.session_state.annotation_page}/{total_pages} 页)")
        
        # 显示问题和答案数据
        for question_row in questions_data:
            ori_qs_id, question_content, question_created, answer_count, annotation_status = question_row
            
            # 获取该问题对应的所有答案
            answers_query = """
            SELECT 
                oa.ori_ans_id,
                oa.content AS answer_content,
                oa.created_at AS answer_created,
                CASE 
                    WHEN sa.ans_id IS NOT NULL THEN '已标注'
                    ELSE '未标注'
                END AS answer_annotation_status
            FROM ori_ans oa
            LEFT JOIN standard_ans sa ON oa.ori_ans_id = sa.ori_ans_id
            WHERE oa.ori_qs_id = %s
            ORDER BY oa.created_at DESC
            """
            
            success, answers_data = execute_query(answers_query, [ori_qs_id], True)
            
            status_color = "🟢" if annotation_status == "已标注" else "🔴"
            
            with st.expander(f"{status_color} 问题 #{ori_qs_id} - {annotation_status} (包含 {answer_count} 个答案)", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("**原始问题内容:**")
                    st.info(question_content)
                    st.caption(f"创建时间: {question_created}")
                    
                    if success and answers_data:
                        st.markdown("**对应的原始答案:**")
                        for i, answer_row in enumerate(answers_data):
                            ori_ans_id, answer_content, answer_created, answer_annotation_status = answer_row
                            
                            answer_status_color = "🟢" if answer_annotation_status == "已标注" else "🔴"
                            
                            # 为每个答案创建独立的容器和操作区域
                            answer_col1, answer_col2 = st.columns([3, 1])
                            
                            with answer_col1:
                                st.markdown(f"**{answer_status_color} 答案 #{ori_ans_id} ({answer_annotation_status})**")
                                st.success(answer_content)
                                st.caption(f"答案创建时间: {answer_created}")
                            
                            with answer_col2:
                                if answer_annotation_status == "未标注":
                                    # 标注该答案按钮
                                    # 首先检查该问题是否已有其他答案被标注为标准答案
                                    check_existing_query = """
                                    SELECT sa.ans_id, sa.ori_ans_id, oa2.content
                                    FROM standard_ans sa
                                    JOIN ori_ans oa ON sa.ori_ans_id = oa.ori_ans_id
                                    JOIN ori_ans oa2 ON sa.ori_ans_id = oa2.ori_ans_id
                                    WHERE oa.ori_qs_id = %s AND sa.status != 'archived'
                                    """
                                    
                                    success_check, existing_standards = execute_query(check_existing_query, [ori_qs_id], True)
                                    
                                    has_existing_standard = success_check and existing_standards
                                    
                                    if has_existing_standard:
                                        existing_count = len(existing_standards)
                                        existing_preview = existing_standards[0][2][:50] + "..." if len(existing_standards[0][2]) > 50 else existing_standards[0][2]
                                        st.warning(f"⚠️ 该问题已有 {existing_count} 个标准答案: {existing_preview}")
                                        st.caption("标注新答案将替换原有的标准答案")
                                    
                                    button_text = f"🔄 替换为标准答案" if has_existing_standard else f"🏷️ 标注为标准答案"
                                    
                                    if st.button(button_text, key=f"annotate_answer_{ori_ans_id}", use_container_width=True):
                                        if has_existing_standard:
                                            # 如果已有标准答案，先删除它们
                                            delete_query = """
                                            DELETE sa FROM standard_ans sa
                                            JOIN ori_ans oa ON sa.ori_ans_id = oa.ori_ans_id
                                            WHERE oa.ori_qs_id = %s AND sa.status != 'archived'
                                            """
                                            
                                            success_delete, result_delete = execute_query(delete_query, [ori_qs_id])
                                            
                                            if not success_delete:
                                                st.error(f"❌ 删除原有标准答案失败: {result_delete}")
                                                st.stop()
                                        
                                        # 执行新的答案标注
                                        insert_answer_query = """
                                        INSERT INTO standard_ans (ori_ans_id, ans_content, created_by, updated_content_version, status)
                                        VALUES (%s, %s, %s, 1, 'draft')
                                        """
                                        
                                        insert_answer_params = [ori_ans_id, answer_content, user_info['user_id']]
                                        
                                        success_ans, result_ans = execute_query(insert_answer_query, insert_answer_params)
                                        
                                        if success_ans:
                                            if has_existing_standard:
                                                st.success(f"✅ 答案 #{ori_ans_id} 已成功标注为标准答案！原有标准答案已被替换")
                                            else:
                                                st.success(f"✅ 答案 #{ori_ans_id} 已成功标注为标准答案！")
                                            st.rerun()
                                        else:
                                            st.error(f"❌ 答案标注失败: {result_ans}")
                                else:
                                    st.success("✅ 已标注")
                            
                            if i < len(answers_data) - 1:  # 不是最后一个答案时添加分隔线
                                st.markdown("---")
                    else:
                        st.warning("该问题暂无对应的答案")
                
                with col2:
                    st.markdown("**标注操作**")
                    
                    if annotation_status == "未标注":
                        # 标注按钮
                        if st.button(f"🏷️ 标注为标准问题", key=f"annotate_{ori_qs_id}", use_container_width=True):
                            # 执行标注
                            insert_query = """
                            INSERT INTO standard_QS (ori_qs_id, content, created_by, tag_id, updated_content_version, status)
                            VALUES (%s, %s, %s, 1, 1, 'draft')
                            """
                            
                            insert_params = [ori_qs_id, question_content, user_info['user_id']]
                            
                            success, result = execute_query(insert_query, insert_params)
                            
                            if success:
                                st.success(f"✅ 问题 #{ori_qs_id} 已成功标注为标准问题！")
                                st.rerun()
                            else:
                                st.error(f"❌ 标注失败: {result}")
                    else:
                        st.success("✅ 此问题已被标注为标准问题")

# 数据导入页面
elif menu == "数据导入":
    st.header("数据导入")
    
    # 权限检查 - MAY NEED REVIEW
    if user_info['role'] != 'admin':
        st.warning("⚠️ 数据导入功能需要管理员权限")
        st.info("您可以查看导入说明，但无法执行实际导入操作")
        import_allowed = False
    else:
        import_allowed = True
    
    # 创建选项卡
    tab1, tab2, tab3 = st.tabs(["文件导入", "API导入", "导入历史"])
    
    with tab1:
        st.subheader("文件数据导入")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 导入选项
            import_option = st.radio(
                "选择导入方式",
                ["CSV文件导入", "JSON文件导入", "SQL脚本导入"]
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
            st.markdown("### 导入设置")
            
            if not import_allowed:
                st.error("❌ 需要管理员权限才能执行导入操作")
                st.stop()
            
            if import_option == "CSV文件导入":
                col1, col2 = st.columns(2)
                with col1:
                    available_tables = get_table_names()
                    if available_tables:
                        target_table = st.selectbox("目标表", available_tables)
                    else:
                        st.warning("数据库中没有可用的表")
                        target_table = None
                with col2:
                    has_header = st.checkbox("包含表头", value=True)
                
                encoding = st.selectbox("文件编码", ["UTF-8", "GBK", "ISO-8859-1"], index=0)
                delimiter = st.selectbox("分隔符", [",", ";", "\\t", "|"], index=0)
                
            elif import_option == "JSON文件导入":
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
                    label=f"下载{('单个表' if '单个表导入' in json_import_type else '多表批量')}示例JSON",
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
                                    
                                    if st.button("执行单表导入", key="json_import_btn_single"):
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

                                if st.button("执行多表批量导入", key="json_import_btn_multi"):
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

# 用户管理页面
elif menu == "用户管理":
    # 权限检查 - MAY NEED REVIEW
    if user_info['role'] != 'admin':
        st.error("❌ 权限不足：用户管理功能需要管理员权限")
        st.info("请联系系统管理员获取相关权限")
    else:
        show_admin_panel()

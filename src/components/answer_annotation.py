"""
答案标注模块 - 展示原始答案并支持标注为标准答案
Author: Database Project Team
Date: 2024

功能说明：
- 显示原始答案列表，包含对应的问题内容
- 支持搜索和分页浏览答案
- 将原始答案标注为标准答案
- 支持编辑答案内容后再标注
- 管理标准答案的状态（draft, review, approved, archived）
- 提供答案标注统计信息
- 具备缓存机制，优化性能

性能优化：
- 使用缓存减少重复数据库查询
- 合并SQL查询提升响应速度
- 分页显示避免加载大量数据
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional, Tuple
import sys
import os

# 添加父目录到路径以导入数据库模块
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database import execute_query, get_paginated_query

class AnswerAnnotationManager:
    """答案标注管理器"""
    
    def __init__(self):
        """初始化答案标注管理器"""
        self.current_page = 1
        self.page_size = 10
        

    
    def get_original_answers(self, page: int = 1, page_size: int = 10) -> Tuple[bool, str, int, List, int]:
        """
        获取原始答案数据
        
        Args:
            page: 页码
            page_size: 每页大小
            
        Returns:
            Tuple[success, message, total_count, data, total_pages]
        """
        query = """
        SELECT 
            oa.ori_ans_id,
            oa.content AS answer_content,
            oa.ori_qs_id,
            oq.content AS question_content,
            oa.created_at AS answer_created,
            CASE 
                WHEN sa.ans_id IS NOT NULL THEN '已标注'
                ELSE '未标注'
            END AS annotation_status,
            sa.ans_id AS standard_ans_id,
            sa.status AS standard_status
        FROM ori_ans oa
        INNER JOIN ori_qs oq ON oa.ori_qs_id = oq.ori_qs_id
        LEFT JOIN standard_ans sa ON oa.ori_ans_id = sa.ori_ans_id
        ORDER BY oa.created_at DESC
        """
        
        return get_paginated_query(query, None, page, page_size)
    

    
    def get_available_users(self) -> List[Dict]:
        """获取可用的用户列表（用于标注者）"""
        query = """
        SELECT user_id, username, name 
        FROM User 
        WHERE is_active = TRUE 
        ORDER BY username
        """
        success, result = execute_query(query, None, True)
        
        if success and result:
            return [{"user_id": row[0], "username": row[1], "name": row[2]} for row in result]
        return []
    


    def create_standard_answer(self, ori_ans_id: int, created_by: int, 
                             edited_content: str = None, quality_score: Optional[float] = None) -> Tuple[bool, str]:
        """
        将原始答案标注为标准答案
        
        Args:
            ori_ans_id: 原始答案ID
            created_by: 创建者用户ID
            edited_content: 编辑后的答案内容（如果为None则使用原始内容）
            quality_score: 质量评分（可选）
            
        Returns:
            Tuple[success, message]
        """
        try:
            # 首先检查是否已经存在标准答案
            check_query = "SELECT ans_id FROM standard_ans WHERE ori_ans_id = %s"
            success, existing = execute_query(check_query, (ori_ans_id,), True)
            
            if success and existing:
                return False, "该原始答案已经被标注为标准答案"
            
            # 创建更新内容记录
            update_content_query = """
            INSERT INTO updated_content (content, operation, created_by) 
            VALUES (%s, %s, %s)
            """
            content_desc = f"标注原始答案 {ori_ans_id} 为标准答案"
            success, result = execute_query(
                update_content_query, 
                (content_desc, 'CREATE', created_by)
            )
            
            if not success:
                return False, f"创建更新记录失败: {result}"
            
            # 获取刚创建的更新版本ID
            get_version_query = "SELECT LAST_INSERT_ID()"
            success, version_result = execute_query(get_version_query, None, True)
            
            if not success or not version_result:
                return False, "获取更新版本ID失败"
                
            updated_content_version = version_result[0][0]
            
            # 获取答案内容（使用编辑后的内容或原始内容）
            if edited_content is None:
                get_ans_query = "SELECT content FROM ori_ans WHERE ori_ans_id = %s"
                success, ans_result = execute_query(get_ans_query, (ori_ans_id,), True)
                
                if not success or not ans_result:
                    return False, "获取原始答案内容失败"
                    
                answer_content = ans_result[0][0]
            else:
                answer_content = edited_content
            
            # 创建标准答案
            insert_query = """
            INSERT INTO standard_ans (
                ans_content, ori_ans_id, updated_content_version, 
                created_by, status, quality_score
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            params = (
                answer_content, ori_ans_id, updated_content_version,
                created_by, 'draft', quality_score
            )
            
            success, message = execute_query(insert_query, params)
            
            if success:
                return True, "成功标注为标准答案"
            else:
                return False, f"标注失败: {message}"
                
        except Exception as e:
            return False, f"标注过程中发生错误: {str(e)}"
    
    def update_standard_answer_status(self, ans_id: int, new_status: str, 
                                    updated_by: int) -> Tuple[bool, str]:
        """
        更新标准答案状态
        
        Args:
            ans_id: 标准答案ID
            new_status: 新状态 ('draft', 'review', 'approved', 'archived')
            updated_by: 更新者用户ID
            
        Returns:
            Tuple[success, message]
        """
        valid_statuses = ['draft', 'review', 'approved', 'archived']
        if new_status not in valid_statuses:
            return False, f"无效的状态值，必须是: {', '.join(valid_statuses)}"
        
        update_query = """
        UPDATE standard_ans 
        SET status = %s, approved_by = %s, updated_at = CURRENT_TIMESTAMP
        WHERE ans_id = %s
        """
        
        approved_by = updated_by if new_status == 'approved' else None
        success, message = execute_query(update_query, (new_status, approved_by, ans_id))
        
        if success:
            return True, f"成功更新状态为: {new_status}"
        else:
            return False, f"状态更新失败: {message}"
    

    
    def search_answers(self, search_term: str, page: int = 1, 
                      page_size: int = 10) -> Tuple[bool, str, int, List, int]:
        """
        搜索原始答案
        
        Args:
            search_term: 搜索关键词
            page: 页码
            page_size: 每页大小
            
        Returns:
            Tuple[success, message, total_count, data, total_pages]
        """
        query = """
        SELECT 
            oa.ori_ans_id,
            oa.content AS answer_content,
            oa.ori_qs_id,
            oq.content AS question_content,
            oa.created_at AS answer_created,
            CASE 
                WHEN sa.ans_id IS NOT NULL THEN '已标注'
                ELSE '未标注'
            END AS annotation_status,
            sa.ans_id AS standard_ans_id,
            sa.status AS standard_status
        FROM ori_ans oa
        INNER JOIN ori_qs oq ON oa.ori_qs_id = oq.ori_qs_id
        LEFT JOIN standard_ans sa ON oa.ori_ans_id = sa.ori_ans_id
        WHERE oa.content LIKE %s OR oq.content LIKE %s
        ORDER BY oa.created_at DESC
        """
        
        search_pattern = f"%{search_term}%"
        return get_paginated_query(query, (search_pattern, search_pattern), page, page_size)
    
    def get_annotation_statistics(self) -> Dict[str, int]:
        """获取标注统计信息 - 只关注答案标注"""
        stats = {}
        
        # 使用简化的查询，只获取答案相关统计
        combined_query = """
        SELECT 
            (SELECT COUNT(*) FROM ori_ans) as total_answers,
            (SELECT COUNT(*) FROM standard_ans) as annotated_answers
        """
        
        success, result = execute_query(combined_query, None, True)
        if success and result:
            total_answers, annotated_answers = result[0]
            
            stats['总原始答案数'] = total_answers
            stats['已标注答案数'] = annotated_answers
            stats['未标注答案数'] = total_answers - annotated_answers
            
            # 计算完成率
            if total_answers > 0:
                stats['答案标注完成率'] = round((annotated_answers / total_answers) * 100, 2)
            else:
                stats['答案标注完成率'] = 0
        else:
            # 如果查询失败，返回默认值
            for key in ['总原始答案数', '已标注答案数', '未标注答案数', '答案标注完成率']:
                stats[key] = 0
        
        # 获取答案状态分布
        try:
            status_query = "SELECT status, COUNT(*) FROM standard_ans GROUP BY status"
            success, result = execute_query(status_query, None, True)
            if success and result:
                for status, count in result:
                    stats[f'答案{status}状态数'] = count
        except:
            pass  # 状态信息是可选的，失败时跳过
            
        return stats


def create_answer_annotation_ui():
    """创建答案标注界面"""
    st.header("📝 答案标注管理")
    
    # 初始化管理器
    if 'annotation_manager' not in st.session_state:
        st.session_state.annotation_manager = AnswerAnnotationManager()
    
    manager = st.session_state.annotation_manager
    
    # 缓存机制 - 避免重复查询
    cache_timeout = 30  # 缓存30秒
    current_time = pd.Timestamp.now().timestamp()
    
    # 缓存统计数据
    if ('cached_stats' not in st.session_state or 
        'stats_cache_time' not in st.session_state or 
        current_time - st.session_state.stats_cache_time > cache_timeout):
        st.session_state.cached_stats = manager.get_annotation_statistics()
        st.session_state.stats_cache_time = current_time
    
    # 缓存用户数据
    if ('cached_users' not in st.session_state or 
        'users_cache_time' not in st.session_state or 
        current_time - st.session_state.users_cache_time > cache_timeout):
        st.session_state.cached_users = manager.get_available_users()
        st.session_state.users_cache_time = current_time
    
    # 侧边栏 - 统计信息
    with st.sidebar:
        st.subheader("📊 标注统计")
        
        # 添加刷新按钮
        if st.button("🔄 刷新统计", key="refresh_stats"):
            st.session_state.cached_stats = manager.get_annotation_statistics()
            st.session_state.stats_cache_time = current_time
            st.rerun()
        
        stats = st.session_state.cached_stats
        
        # 只显示答案相关的统计信息
        key_stats = ['总原始答案数', '已标注答案数', '答案标注完成率']
        
        for stat_name in key_stats:
            if stat_name in stats:
                value = stats[stat_name]
                if '完成率' in stat_name:
                    st.metric(stat_name, f"{value}%")
                else:
                    st.metric(stat_name, value)
        
        # 详细统计信息放在expander中
        with st.expander("详细统计", expanded=False):
            for stat_name, value in stats.items():
                if stat_name not in key_stats:
                    st.caption(f"{stat_name}: {value}")
    
    # 答案标注内容
    st.subheader("原始答案标注")
    
    # 搜索和设置
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term_a = st.text_input("搜索答案", placeholder="输入答案内容关键词...", key="search_answers")
    
    with col2:
        page_size_a = st.selectbox("每页显示数量", [5, 10, 20, 50], index=1, key="page_size_answers")
    
    # 初始化页码
    if 'current_page_a' not in st.session_state:
        st.session_state.current_page_a = 1
    
    # 检查搜索条件变化，重置页码
    if 'prev_search_a' not in st.session_state:
        st.session_state.prev_search_a = ""
    if 'prev_page_size_a' not in st.session_state:
        st.session_state.prev_page_size_a = page_size_a
        
    if (search_term_a != st.session_state.prev_search_a or 
        page_size_a != st.session_state.prev_page_size_a):
        st.session_state.current_page_a = 1
        st.session_state.prev_search_a = search_term_a
        st.session_state.prev_page_size_a = page_size_a
    
    # 获取答案数据
    if search_term_a:
        success, message, total_count, data, total_pages = manager.search_answers(
            search_term_a, st.session_state.current_page_a, page_size_a
        )
    else:
        success, message, total_count, data, total_pages = manager.get_original_answers(
            st.session_state.current_page_a, page_size_a
        )
    
    if not success:
        st.error(f"数据获取失败: {message}")
    elif not data:
        st.info("暂无答案数据")
    else:
        # 分页控件
        if total_pages > 1:
            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
            
            with col1:
                if st.button("首页", key="a_first_page") and st.session_state.current_page_a > 1:
                    st.session_state.current_page_a = 1
                    st.rerun()
            
            with col2:
                if st.button("上页", key="a_prev_page") and st.session_state.current_page_a > 1:
                    st.session_state.current_page_a -= 1
                    st.rerun()
            
            with col3:
                new_page_a = st.number_input(
                    f"页码 (共 {total_pages} 页)", 
                    min_value=1, 
                    max_value=total_pages, 
                    value=st.session_state.current_page_a,
                    key="page_input_a"
                )
                if new_page_a != st.session_state.current_page_a:
                    st.session_state.current_page_a = new_page_a
                    st.rerun()
            
            with col4:
                if st.button("下页", key="a_next_page") and st.session_state.current_page_a < total_pages:
                    st.session_state.current_page_a += 1
                    st.rerun()
            
            with col5:
                if st.button("末页", key="a_last_page") and st.session_state.current_page_a < total_pages:
                    st.session_state.current_page_a = total_pages
                    st.rerun()
        
        st.subheader(f"💡 答案列表 (共 {total_count} 条)")
        
        # 使用缓存的用户选项
        users = st.session_state.cached_users
        user_options = {f"{user['username']} ({user['name']})": user['user_id'] for user in users}
        
        # 优化：添加状态图标，减少字符串操作
        for i, row in enumerate(data):
            (ori_ans_id, answer_content, ori_qs_id, question_content, 
             answer_created, annotation_status, standard_ans_id, standard_status) = row
            
            status_icon = "✅" if annotation_status == "已标注" else "📝"
            
            with st.expander(f"{status_icon} 答案 #{ori_ans_id} - {annotation_status}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("**对应问题:**")
                    st.text_area(
                        f"问题内容 (ID: {ori_qs_id})", 
                        value=question_content, 
                        height=80, 
                        disabled=True,
                        key=f"related_question_{ori_ans_id}"
                    )
                    
                    st.markdown("**原始答案内容:**")
                    
                    # 可编辑的答案内容
                    edited_answer = st.text_area(
                        f"答案内容 (ID: {ori_ans_id})", 
                        value=answer_content, 
                        height=200,
                        key=f"edit_answer_{ori_ans_id}",
                        help="您可以编辑答案内容后再标注"
                    )
                    
                    st.caption(f"创建时间: {answer_created}")
                
                with col2:
                    st.markdown("**标注操作**")
                    
                    if annotation_status == "未标注":
                        st.info("📌 此答案尚未标注")
                        
                        if users:
                            selected_user = st.selectbox(
                                "标注者", 
                                list(user_options.keys()),
                                key=f"user_a_{ori_ans_id}"
                            )
                            
                            quality_score = st.slider(
                                "质量评分", 
                                0.0, 5.0, 3.0, 0.1,
                                key=f"score_a_{ori_ans_id}"
                            )
                            
                            # 简化编辑检查逻辑
                            content_changed = len(edited_answer.strip()) != len(answer_content.strip())
                            use_edited = st.checkbox(
                                "使用编辑后的内容",
                                value=content_changed,
                                key=f"use_edited_a_{ori_ans_id}"
                            )
                            
                            if st.button(f"标注为标准答案", key=f"annotate_a_{ori_ans_id}"):
                                user_id = user_options[selected_user]
                                content_to_use = edited_answer if use_edited else None
                                
                                success, message = manager.create_standard_answer(
                                    ori_ans_id, user_id, content_to_use, quality_score
                                )
                                
                                if success:
                                    # 清除缓存，因为数据已更新
                                    if 'cached_stats' in st.session_state:
                                        del st.session_state.cached_stats
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                        else:
                            st.warning("请先添加用户数据")
                            
                    else:
                        st.success("✅ 已标注为标准答案")
                        st.info(f"标准答案ID: {standard_ans_id}")
                        st.info(f"当前状态: {standard_status}")
                        
                        # 状态更新
                        if users:
                            new_status = st.selectbox(
                                "更新状态",
                                ['draft', 'review', 'approved', 'archived'],
                                index=['draft', 'review', 'approved', 'archived'].index(standard_status),
                                key=f"status_a_{ori_ans_id}"
                            )
                            
                            updater = st.selectbox(
                                "更新者",
                                list(user_options.keys()),
                                key=f"updater_a_{ori_ans_id}"
                            )
                            
                            if st.button(f"更新状态", key=f"update_a_{ori_ans_id}"):
                                user_id = user_options[updater]
                                success, message = manager.update_standard_answer_status(
                                    standard_ans_id, new_status, user_id
                                )
                                
                                if success:
                                    # 清除缓存，因为数据已更新
                                    if 'cached_stats' in st.session_state:
                                        del st.session_state.cached_stats
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)


if __name__ == "__main__":
    create_answer_annotation_ui() 
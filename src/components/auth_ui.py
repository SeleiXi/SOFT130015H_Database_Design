"""
认证界面组件
包含登录、注册表单和用户管理界面
"""

import streamlit as st
import sys
import os

# 添加父目录到路径以导入auth模块
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth import auth_manager, create_default_admin
from database import get_users_list, get_user_activity_stats, get_user_login_history

class AuthUI:
    """认证界面管理器"""
    
    def __init__(self):
        # 确保初始化会话状态
        self._init_session_state()
    
    def _init_session_state(self):
        """初始化会话状态"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
        if 'auth_page' not in st.session_state:
            st.session_state.auth_page = 'login'
    
    def check_authentication(self) -> bool:
        """
        检查用户是否已认证
        
        Returns:
            bool: 是否已认证
        """
        self._init_session_state()
        return st.session_state.get('authenticated', False)
    
    def get_current_user(self):
        """
        获取当前用户信息
        
        Returns:
            dict: 用户信息或None
        """
        return st.session_state.get('user_info')
    
    def logout(self):
        """用户登出"""
        st.session_state.authenticated = False
        st.session_state.user_info = None
        auth_manager.current_user = None
        st.success("已成功登出！")
        st.rerun()
    
    def show_login_form(self):
        """显示登录表单"""
        st.markdown("### 🔐 用户登录")
        
        with st.form("login_form"):
            username = st.text_input("用户名或邮箱", placeholder="请输入用户名或邮箱")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                login_submit = st.form_submit_button("登录", use_container_width=True)
            
            with col2:
                if st.form_submit_button("注册", use_container_width=True):
                    self._init_session_state()
                    st.session_state.auth_page = 'register'
                    st.rerun()
            
            with col3:
                if st.form_submit_button("管理员设置", use_container_width=True):
                    self._init_session_state()
                    st.session_state.auth_page = 'admin_setup'
                    st.rerun()
        
        if login_submit:
            if not username or not password:
                st.error("请填写用户名和密码")
                return
            
            with st.spinner("正在登录..."):
                success, message, user_info = auth_manager.login_user(username, password)
                
                if success:
                    st.session_state.authenticated = True
                    st.session_state.user_info = user_info
                    auth_manager.current_user = user_info
                    st.success(f"欢迎回来，{user_info['name']}！")
                    st.rerun()
                else:
                    st.error(f"登录失败：{message}")
    
    def show_register_form(self):
        """显示注册表单"""
        st.markdown("### 📝 用户注册")
        
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input("用户名", placeholder="至少3位字符")
                email = st.text_input("邮箱", placeholder="请输入有效邮箱")
            
            with col2:
                name = st.text_input("姓名", placeholder="请输入真实姓名")
                role = st.selectbox("用户类型", ["guest", "evaluator"], 
                                  format_func=lambda x: {"guest": "访客", "evaluator": "评估员"}[x])
            
            password = st.text_input("密码", type="password", placeholder="至少8位，包含字母和数字")
            confirm_password = st.text_input("确认密码", type="password", placeholder="请再次输入密码")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                register_submit = st.form_submit_button("注册", use_container_width=True)
            
            with col2:
                if st.form_submit_button("返回登录", use_container_width=True):
                    self._init_session_state()
                    st.session_state.auth_page = 'login'
                    st.rerun()
        
        if register_submit:
            # 验证输入
            if not all([username, name, email, password, confirm_password]):
                st.error("请填写所有必填字段")
                return
            
            if password != confirm_password:
                st.error("两次输入的密码不一致")
                return
            
            with st.spinner("正在注册..."):
                success, message = auth_manager.register_user(username, name, email, password, role)
                
                if success:
                    st.success(f"注册成功！{message}")
                    st.info("请返回登录页面使用新账户登录")
                    self._init_session_state()
                    st.session_state.auth_page = 'login'
                    st.rerun()
                else:
                    st.error(f"注册失败：{message}")
    
    def show_admin_setup(self):
        """显示管理员设置页面"""
        st.markdown("### ⚙️ 管理员账户设置")
        
        st.info("如果这是首次使用系统，可以创建默认管理员账户")
        
        if st.button("创建默认管理员", use_container_width=True):
            with st.spinner("正在创建管理员账户..."):
                success, message = create_default_admin()
                
                if success:
                    if "已存在" in message:
                        st.warning(message)
                    else:
                        st.success(message)
                        st.info("默认管理员账户信息：")
                        st.code("""
用户名: admin
邮箱: admin@example.com
密码: admin123
                        """)
                        st.warning("⚠️ 请尽快登录并修改默认密码！")
                else:
                    st.error(f"创建失败：{message}")
        
        st.markdown("---")
        if st.button("返回登录", use_container_width=True):
            self._init_session_state()
            st.session_state.auth_page = 'login'
            st.rerun()
    
    def show_user_profile(self):
        """显示用户资料"""
        user = self.get_current_user()
        if not user:
            return
        
        st.markdown("### 👤 个人资料")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("用户名", value=user['username'], disabled=True)
            st.text_input("姓名", value=user['name'], disabled=True)
        
        with col2:
            st.text_input("邮箱", value=user['email'], disabled=True)
            role_map = {"admin": "管理员", "evaluator": "评估员", "guest": "访客"}
            st.text_input("用户类型", value=role_map.get(user['role'], user['role']), disabled=True)
        
        st.markdown("---")
        
        # 修改密码
        st.markdown("#### 🔒 修改密码")
        with st.form("change_password_form"):
            old_password = st.text_input("当前密码", type="password")
            new_password = st.text_input("新密码", type="password")
            confirm_new_password = st.text_input("确认新密码", type="password")
            
            if st.form_submit_button("修改密码"):
                if not all([old_password, new_password, confirm_new_password]):
                    st.error("请填写所有密码字段")
                elif new_password != confirm_new_password:
                    st.error("两次输入的新密码不一致")
                else:
                    success, message = auth_manager.change_password(
                        user['user_id'], old_password, new_password
                    )
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
    
    def show_user_management(self):
        """显示用户管理界面（仅管理员）"""
        user = self.get_current_user()
        if not user or user['role'] != 'admin':
            st.error("权限不足：仅管理员可访问")
            return
        
        st.markdown("### 👥 用户管理")
        
        # 用户统计
        st.markdown("#### 📊 用户统计")
        stats = get_user_activity_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总用户数", stats.get("总用户数", 0))
        with col2:
            st.metric("活跃用户", stats.get("活跃用户数", 0))
        with col3:
            st.metric("管理员", stats.get("管理员数", 0))
        with col4:
            st.metric("今日登录", stats.get("今日登录", 0))
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("评估员", stats.get("评估员数", 0))
        with col2:
            st.metric("访客", stats.get("访客数", 0))
        with col3:
            st.metric("本周登录", stats.get("本周登录", 0))
        with col4:
            st.metric("本月登录", stats.get("本月登录", 0))
        
        st.markdown("---")
        
        # 用户列表
        st.markdown("#### 📋 用户列表")
        
        # 分页设置
        page_size = st.selectbox("每页显示", [10, 20, 50], index=0, key="user_mgmt_page_size")
        
        if 'user_mgmt_page' not in st.session_state:
            st.session_state.user_mgmt_page = 1
        
        success, message, total_count, users, total_pages = get_users_list(
            st.session_state.user_mgmt_page, page_size
        )
        
        if success and users:
            # 显示用户表格
            user_data = []
            for user_row in users:
                user_id, username, name, email, role, created_at, last_login, is_active = user_row
                role_map = {"admin": "管理员", "evaluator": "评估员", "guest": "访客"}
                status = "启用" if is_active else "禁用"
                
                user_data.append({
                    "用户ID": user_id,
                    "用户名": username,
                    "姓名": name,
                    "邮箱": email,
                    "角色": role_map.get(role, role),
                    "创建时间": created_at,
                    "最后登录": last_login or "从未登录",
                    "状态": status
                })
            
            import pandas as pd
            df = pd.DataFrame(user_data)
            st.dataframe(df, use_container_width=True)
            
            # 分页控制
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("上一页", disabled=st.session_state.user_mgmt_page <= 1):
                    st.session_state.user_mgmt_page -= 1
                    st.rerun()
            
            with col2:
                st.write(f"第 {st.session_state.user_mgmt_page} 页，共 {total_pages} 页（共 {total_count} 条记录）")
            
            with col3:
                if st.button("下一页", disabled=st.session_state.user_mgmt_page >= total_pages):
                    st.session_state.user_mgmt_page += 1
                    st.rerun()
        
        else:
            st.warning("暂无用户数据")
    
    def show_auth_page(self):
        """显示认证页面"""
        # 确保会话状态已初始化
        self._init_session_state()
        
        if self.check_authentication():
            return True
        
        # 未认证时显示认证界面
        st.markdown("<h1 style='text-align: center;'>🔐 LLM问答评估系统</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>请登录或注册以继续</p>", unsafe_allow_html=True)
        
        # 根据当前页面状态显示对应表单
        auth_page = st.session_state.get('auth_page', 'login')
        if auth_page == 'login':
            self.show_login_form()
        elif auth_page == 'register':
            self.show_register_form()
        elif auth_page == 'admin_setup':
            self.show_admin_setup()
        
        return False
    
    def show_user_info_sidebar(self):
        """在侧边栏显示用户信息"""
        user = self.get_current_user()
        if user:
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 👤 当前用户")
            st.sidebar.write(f"**姓名:** {user['name']}")
            st.sidebar.write(f"**用户名:** {user['username']}")
            role_map = {"admin": "管理员", "evaluator": "评估员", "guest": "访客"}
            st.sidebar.write(f"**角色:** {role_map.get(user['role'], user['role'])}")
            
            if st.sidebar.button("个人资料", use_container_width=True):
                st.session_state.show_profile = True
                st.rerun()
            
            if user['role'] == 'admin':
                if st.sidebar.button("用户管理", use_container_width=True):
                    st.session_state.show_user_mgmt = True
                    st.rerun()
            
            if st.sidebar.button("登出", use_container_width=True):
                self.logout()

# 全局认证UI实例
auth_ui = AuthUI() 
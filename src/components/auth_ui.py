import streamlit as st
import pandas as pd
from typing import Optional, Dict
import sys
import os

# 添加src目录到路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth import (
    authenticate_user, register_user, logout, require_login, require_admin,
    get_user_list, update_user_status, update_user_role, change_password,
    create_user_table, create_admin_user
)


def show_login_form() -> Optional[Dict]:
    """
    显示登录表单
    
    Returns:
        Optional[Dict]: 登录成功返回用户信息，否则返回None
    """
    st.markdown("### 🔐 用户登录")
    
    with st.form("login_form"):
        username = st.text_input("用户名", placeholder="请输入用户名")
        password = st.text_input("密码", type="password", placeholder="请输入密码")
        
        col1, col2 = st.columns(2)
        with col1:
            login_button = st.form_submit_button("登录", use_container_width=True)
        with col2:
            if st.form_submit_button("注册新用户", use_container_width=True):
                st.session_state.show_register = True
                st.rerun()
    
    if login_button:
        if not username or not password:
            st.error("请输入用户名和密码")
            return None
        
        success, user_info = authenticate_user(username, password)
        
        if success:
            st.success(f"欢迎回来，{user_info['name']}！")
            return user_info
        else:
            st.error("用户名或密码错误")
            return None
    
    return None


def show_register_form() -> bool:
    """
    显示注册表单
    
    Returns:
        bool: 注册是否成功
    """
    st.markdown("### 📝 用户注册")
    
    with st.form("register_form"):
        username = st.text_input("用户名", placeholder="请输入用户名（用于登录）")
        name = st.text_input("姓名", placeholder="请输入真实姓名")
        password = st.text_input("密码", type="password", placeholder="请输入密码")
        confirm_password = st.text_input("确认密码", type="password", placeholder="请再次输入密码")
        
        st.info("📝 注册的用户默认为普通用户，如需管理员权限请联系系统管理员")
        
        col1, col2 = st.columns(2)
        with col1:
            register_button = st.form_submit_button("注册", use_container_width=True)
        with col2:
            if st.form_submit_button("返回登录", use_container_width=True):
                if 'show_register' in st.session_state:
                    del st.session_state.show_register
                st.rerun()
    
    if register_button:
        # 验证输入
        if not username or not name or not password:
            st.error("请填写所有必填字段")
            return False
        
        if password != confirm_password:
            st.error("两次输入的密码不一致")
            return False
        
        if len(password) < 6:
            st.error("密码长度至少为6位")
            return False
        
        # 注册用户
        success, message = register_user(username, name, password, 'user')
        
        if success:
            st.success(message)
            st.info("注册成功！请返回登录页面使用新账户登录")
            if 'show_register' in st.session_state:
                del st.session_state.show_register
            return True
        else:
            st.error(message)
            return False
    
    return False


def show_user_info(user_info: Dict):
    """
    显示用户信息面板
    
    Args:
        user_info (Dict): 用户信息
    """
    st.markdown("### 👤 用户信息")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info(f"""
        **用户名**: {user_info['username']}  
        **姓名**: {user_info['name']}  
        **角色**: {'管理员' if user_info['role'] == 'admin' else '普通用户'}  
        **状态**: {'活跃' if user_info['is_active'] else '禁用'}
        """)
    
    with col2:
        if st.button("修改密码", use_container_width=True):
            st.session_state.show_change_password = True
        
        if st.button("登出", use_container_width=True):
            logout()


def show_change_password_form(user_id: int):
    """
    显示修改密码表单
    
    Args:
        user_id (int): 用户ID
    """
    st.markdown("### 🔑 修改密码")
    
    with st.form("change_password_form"):
        old_password = st.text_input("当前密码", type="password")
        new_password = st.text_input("新密码", type="password")
        confirm_password = st.text_input("确认新密码", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            change_button = st.form_submit_button("修改密码", use_container_width=True)
        with col2:
            if st.form_submit_button("取消", use_container_width=True):
                if 'show_change_password' in st.session_state:
                    del st.session_state.show_change_password
                st.rerun()
    
    if change_button:
        if not old_password or not new_password:
            st.error("请填写所有字段")
            return
        
        if new_password != confirm_password:
            st.error("两次输入的新密码不一致")
            return
        
        if len(new_password) < 6:
            st.error("新密码长度至少为6位")
            return
        
        success, message = change_password(user_id, old_password, new_password)
        
        if success:
            st.success(message)
            if 'show_change_password' in st.session_state:
                del st.session_state.show_change_password
            st.rerun()
        else:
            st.error(message)


def show_admin_panel():
    """
    显示管理员面板 - 用户管理
    """
    if not require_admin():
        st.error("❌ 权限不足：需要管理员权限")
        return
    
    st.markdown("### 👥 用户管理")
    
    # 分页控制
    if "admin_user_page" not in st.session_state:
        st.session_state.admin_user_page = 1
    
    page_size = st.selectbox("每页显示条数", [5, 10, 20], index=1, key="admin_user_page_size")
    
    # 获取用户列表
    success, message, total_count, users, total_pages = get_user_list(
        st.session_state.admin_user_page, page_size
    )
    
    if not success:
        st.error(f"获取用户列表失败: {message}")
        return
    
    if not users:
        st.warning("暂无用户数据")
        return
    
    # 用户列表表格
    df = pd.DataFrame(users, columns=[
        "用户ID", "用户名", "姓名", "角色", "状态", "创建时间", "最后登录"
    ])
    
    # 转换显示格式
    df["角色"] = df["角色"].map({"admin": "管理员", "user": "普通用户"})
    df["状态"] = df["状态"].map({True: "活跃", False: "禁用", 1: "活跃", 0: "禁用"})
    
    st.dataframe(df, use_container_width=True)
    st.info(f"总用户数: {total_count} | 当前页: {st.session_state.admin_user_page}/{total_pages}")
    
    # 分页控制按钮
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("首页", disabled=st.session_state.admin_user_page <= 1):
            st.session_state.admin_user_page = 1
            st.rerun()
    
    with col2:
        if st.button("上页", disabled=st.session_state.admin_user_page <= 1):
            st.session_state.admin_user_page -= 1
            st.rerun()
    
    with col3:
        new_page = st.number_input(
            "跳转到页码", 
            min_value=1, 
            max_value=total_pages, 
            value=st.session_state.admin_user_page,
            key="admin_user_goto_page"
        )
        if new_page != st.session_state.admin_user_page:
            st.session_state.admin_user_page = new_page
            st.rerun()
    
    with col4:
        if st.button("下页", disabled=st.session_state.admin_user_page >= total_pages):
            st.session_state.admin_user_page += 1
            st.rerun()
    
    with col5:
        if st.button("末页", disabled=st.session_state.admin_user_page >= total_pages):
            st.session_state.admin_user_page = total_pages
            st.rerun()
    
    # 用户操作
    st.markdown("---")
    st.markdown("#### 用户操作")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 修改用户状态")
        with st.form("user_status_form"):
            user_id = st.number_input("用户ID", min_value=1, step=1)
            action = st.selectbox("操作", ["启用", "禁用"])
            
            if st.form_submit_button("执行操作"):
                is_active = (action == "启用")
                success, message = update_user_status(user_id, is_active)
                
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    with col2:
        st.markdown("##### 修改用户角色")
        with st.form("user_role_form"):
            user_id = st.number_input("用户ID", min_value=1, step=1, key="role_user_id")
            role = st.selectbox("角色", ["admin", "user"], 
                              format_func=lambda x: "管理员" if x == "admin" else "普通用户")
            
            if st.form_submit_button("修改角色"):
                success, message = update_user_role(user_id, role)
                
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    # 创建管理员按钮
    st.markdown("---")
    if st.button("创建默认管理员账户", help="用户名: admin, 密码: admin123"):
        success, message = create_admin_user()
        if success:
            st.success(f"{message} - 用户名: admin, 密码: admin123")
        else:
            st.warning(message)


def show_auth_sidebar():
    """
    在侧边栏显示认证状态和操作
    """
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 👤 用户状态")
        
        if require_login():
            user_info = st.session_state.user_info
            st.success(f"已登录: {user_info['name']}")
            st.caption(f"角色: {'管理员' if user_info['role'] == 'admin' else '普通用户'}")
            
            if st.button("登出", use_container_width=True):
                logout()
            
            if user_info['role'] == 'admin':
                st.markdown("---")
                if st.button("用户管理", use_container_width=True):
                    st.session_state.show_admin_panel = True
        else:
            st.warning("未登录")


def initialize_auth_system():
    """
    初始化认证系统
    
    Returns:
        bool: 初始化是否成功
    """
    try:
        # 创建用户表
        success, message = create_user_table()
        if not success:
            st.error(f"创建用户表失败: {message}")
            return False
        
        return True
    except Exception as e:
        st.error(f"初始化认证系统失败: {str(e)}")
        return False 
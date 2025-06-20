import hashlib
import streamlit as st
from typing import Dict, Optional, Tuple
from database import execute_query, get_connection


def hash_password(password: str) -> str:
    """
    对密码进行哈希加密
    
    Args:
        password (str): 原始密码
        
    Returns:
        str: 哈希后的密码
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """
    验证密码是否正确
    
    Args:
        password (str): 输入的密码
        hashed_password (str): 存储的哈希密码
        
    Returns:
        bool: 密码是否正确
    """
    return hash_password(password) == hashed_password


def create_user_table():
    """
    创建用户表（更新版本，包含密码字段）
    
    Returns:
        Tuple[bool, str]: 执行结果和消息
    """
    query = """
    CREATE TABLE IF NOT EXISTS User (
        user_id INT PRIMARY KEY AUTO_INCREMENT,
        username VARCHAR(50) NOT NULL UNIQUE,
        name VARCHAR(100) NOT NULL,
        password_hash VARCHAR(64) NOT NULL,
        role VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user')),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP NULL,
        UNIQUE KEY unique_username (username)
    )
    """
    return execute_query(query)


def register_user(username: str, name: str, password: str, role: str = 'user') -> Tuple[bool, str]:
    """
    注册新用户
    
    Args:
        username (str): 用户名
        name (str): 姓名
        password (str): 密码
        role (str): 用户角色 (admin/user)
        
    Returns:
        Tuple[bool, str]: 注册是否成功和消息
    """
    # 检查用户名是否已存在
    check_query = "SELECT user_id FROM User WHERE username = %s"
    success, result = execute_query(check_query, (username,), fetch=True)
    
    if not success:
        return False, f"检查用户名时出错: {result}"
    
    if result:
        return False, "用户名已存在"
    
    # 创建新用户
    password_hash = hash_password(password)
    insert_query = """
    INSERT INTO User (username, name, password_hash, role) 
    VALUES (%s, %s, %s, %s)
    """
    success, message = execute_query(insert_query, (username, name, password_hash, role))
    
    if success:
        return True, "用户注册成功"
    else:
        return False, f"注册失败: {message}"


def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[Dict]]:
    """
    用户登录验证
    
    Args:
        username (str): 用户名
        password (str): 密码
        
    Returns:
        Tuple[bool, Optional[Dict]]: 认证是否成功和用户信息
    """
    query = """
    SELECT user_id, username, name, password_hash, role, is_active 
    FROM User 
    WHERE username = %s AND is_active = TRUE
    """
    
    success, result = execute_query(query, (username,), fetch=True)
    
    if not success:
        return False, None
    
    if not result:
        return False, None
    
    user_data = result[0]
    stored_password_hash = user_data[3]
    
    if verify_password(password, stored_password_hash):
        # 更新最后登录时间
        update_query = "UPDATE User SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s"
        execute_query(update_query, (user_data[0],))
        
        return True, {
            'user_id': user_data[0],
            'username': user_data[1],
            'name': user_data[2],
            'role': user_data[4],
            'is_active': user_data[5]
        }
    
    return False, None


def get_user_list(page: int = 1, page_size: int = 10) -> Tuple[bool, str, int, list, int]:
    """
    获取用户列表（管理员功能）
    
    Args:
        page (int): 页码
        page_size (int): 每页数量
        
    Returns:
        Tuple[bool, str, int, list, int]: 成功状态，消息，总数，结果列表，总页数
    """
    count_query = "SELECT COUNT(*) FROM User"
    success, count_result = execute_query(count_query, fetch=True)
    
    if not success:
        return False, f"查询用户总数失败: {count_result}", 0, [], 0
    
    total_count = count_result[0][0]
    total_pages = (total_count + page_size - 1) // page_size
    
    offset = (page - 1) * page_size
    
    query = """
    SELECT user_id, username, name, role, is_active, created_at, last_login
    FROM User 
    ORDER BY created_at DESC
    LIMIT %s OFFSET %s
    """
    
    success, result = execute_query(query, (page_size, offset), fetch=True)
    
    if success:
        return True, "查询成功", total_count, result or [], total_pages
    else:
        return False, f"查询失败: {result}", 0, [], 0


def update_user_status(user_id: int, is_active: bool) -> Tuple[bool, str]:
    """
    更新用户状态（启用/禁用）
    
    Args:
        user_id (int): 用户ID
        is_active (bool): 是否激活
        
    Returns:
        Tuple[bool, str]: 操作是否成功和消息
    """
    query = "UPDATE User SET is_active = %s WHERE user_id = %s"
    success, message = execute_query(query, (is_active, user_id))
    
    if success:
        status_text = "启用" if is_active else "禁用"
        return True, f"用户{status_text}成功"
    else:
        return False, f"更新用户状态失败: {message}"


def update_user_role(user_id: int, role: str) -> Tuple[bool, str]:
    """
    更新用户角色
    
    Args:
        user_id (int): 用户ID
        role (str): 新角色
        
    Returns:
        Tuple[bool, str]: 操作是否成功和消息
    """
    if role not in ['admin', 'user']:
        return False, "无效的角色类型"
    
    query = "UPDATE User SET role = %s WHERE user_id = %s"
    success, message = execute_query(query, (role, user_id))
    
    if success:
        return True, f"用户角色更新为{role}成功"
    else:
        return False, f"更新用户角色失败: {message}"


def delete_user(user_id: int) -> Tuple[bool, str]:
    """
    删除用户（软删除，设置为不活跃）
    
    Args:
        user_id (int): 用户ID
        
    Returns:
        Tuple[bool, str]: 操作是否成功和消息
    """
    # 软删除，设置为不活跃而不是真正删除
    return update_user_status(user_id, False)


def change_password(user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
    """
    修改用户密码
    
    Args:
        user_id (int): 用户ID
        old_password (str): 旧密码
        new_password (str): 新密码
        
    Returns:
        Tuple[bool, str]: 操作是否成功和消息
    """
    # 验证旧密码
    query = "SELECT password_hash FROM User WHERE user_id = %s"
    success, result = execute_query(query, (user_id,), fetch=True)
    
    if not success:
        return False, f"查询用户密码失败: {result}"
    
    if not result:
        return False, "用户不存在"
    
    stored_password_hash = result[0][0]
    
    if not verify_password(old_password, stored_password_hash):
        return False, "旧密码不正确"
    
    # 更新密码
    new_password_hash = hash_password(new_password)
    update_query = "UPDATE User SET password_hash = %s WHERE user_id = %s"
    success, message = execute_query(update_query, (new_password_hash, user_id))
    
    if success:
        return True, "密码修改成功"
    else:
        return False, f"密码修改失败: {message}"


def check_admin_role(user_info: Optional[Dict]) -> bool:
    """
    检查用户是否为管理员
    
    Args:
        user_info (Optional[Dict]): 用户信息
        
    Returns:
        bool: 是否为管理员
    """
    return user_info is not None and user_info.get('role') == 'admin'


def require_login() -> bool:
    """
    检查用户是否已登录
    
    Returns:
        bool: 是否已登录
    """
    return 'user_info' in st.session_state and st.session_state.user_info is not None


def require_admin() -> bool:
    """
    检查用户是否为管理员
    
    Returns:
        bool: 是否为管理员且已登录
    """
    return require_login() and check_admin_role(st.session_state.user_info)


def logout():
    """用户登出"""
    if 'user_info' in st.session_state:
        del st.session_state.user_info
    if 'login_status' in st.session_state:
        del st.session_state.login_status
    st.success("已成功登出")
    st.rerun()


def create_admin_user() -> Tuple[bool, str]:
    """
    创建默认管理员用户
    
    Returns:
        Tuple[bool, str]: 创建是否成功和消息
    """
    # 检查是否已有管理员
    check_query = "SELECT user_id FROM User WHERE role = 'admin'"
    success, result = execute_query(check_query, fetch=True)
    
    if success and result:
        return False, "管理员账户已存在"
    
    # 创建默认管理员 (username: admin, password: admin123)
    return register_user("admin", "系统管理员", "admin123", "admin") 
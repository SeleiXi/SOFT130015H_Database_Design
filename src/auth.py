"""
用户认证模块
包含用户注册、登录、密码验证和权限管理功能
"""

import bcrypt
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from database import execute_query, get_connection

# 正确导入PyJWT
try:
    import jwt
except ImportError:
    raise ImportError("请安装PyJWT: pip install PyJWT==2.8.0")

# JWT配置
JWT_SECRET = "your-secret-key-here-change-in-production"  # 在生产环境中应该使用环境变量
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

class AuthManager:
    """用户认证管理器"""
    
    def __init__(self):
        self.current_user = None
    
    def validate_email(self, email: str) -> bool:
        """
        验证邮箱格式
        
        Args:
            email: 邮箱地址
            
        Returns:
            bool: 是否有效
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password: str) -> Tuple[bool, str]:
        """
        验证密码强度
        
        Args:
            password: 密码
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if len(password) < 8:
            return False, "密码长度至少8位"
        
        if not re.search(r'[A-Za-z]', password):
            return False, "密码必须包含字母"
        
        if not re.search(r'\d', password):
            return False, "密码必须包含数字"
        
        return True, ""
    
    def hash_password(self, password: str) -> str:
        """
        哈希密码
        
        Args:
            password: 原始密码
            
        Returns:
            str: 哈希后的密码
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            password: 原始密码
            hashed_password: 哈希后的密码
            
        Returns:
            bool: 密码是否正确
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def generate_token(self, user_id: int, username: str, role: str) -> str:
        """
        生成JWT令牌
        
        Args:
            user_id: 用户ID
            username: 用户名
            role: 用户角色
            
        Returns:
            str: JWT令牌
        """
        payload = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            Optional[Dict]: 用户信息或None
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def register_user(self, username: str, name: str, email: str, password: str, role: str = 'guest') -> Tuple[bool, str]:
        """
        用户注册
        
        Args:
            username: 用户名
            name: 姓名
            email: 邮箱
            password: 密码
            role: 用户角色
            
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        # 验证输入
        if not username or len(username) < 3:
            return False, "用户名长度至少3位"
        
        if not name:
            return False, "姓名不能为空"
        
        if not self.validate_email(email):
            return False, "邮箱格式不正确"
        
        is_valid_password, password_error = self.validate_password(password)
        if not is_valid_password:
            return False, password_error
        
        if role not in ['admin', 'evaluator', 'guest']:
            return False, "用户角色不正确"
        
        # 检查用户名和邮箱是否已存在
        check_query = """
        SELECT user_id FROM User 
        WHERE username = %s OR email = %s
        """
        success, result = execute_query(check_query, (username, email), fetch=True)
        
        if not success:
            return False, f"检查用户信息时出错: {result}"
        
        if result:
            return False, "用户名或邮箱已存在"
        
        # 哈希密码
        password_hash = self.hash_password(password)
        
        # 插入用户
        insert_query = """
        INSERT INTO User (username, name, email, password_hash, role)
        VALUES (%s, %s, %s, %s, %s)
        """
        success, message = execute_query(insert_query, (username, name, email, password_hash, role))
        
        if success:
            return True, "用户注册成功"
        else:
            return False, f"注册失败: {message}"
    
    def login_user(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        用户登录
        
        Args:
            username: 用户名或邮箱
            password: 密码
            
        Returns:
            Tuple[bool, str, Optional[Dict]]: (是否成功, 消息, 用户信息)
        """
        # 查询用户（支持用户名或邮箱登录）
        query = """
        SELECT user_id, username, name, email, password_hash, role, is_active
        FROM User 
        WHERE (username = %s OR email = %s) AND is_active = TRUE
        """
        success, result = execute_query(query, (username, username), fetch=True)
        
        if not success:
            return False, f"查询用户信息时出错: {result}", None
        
        if not result:
            return False, "用户不存在或已被禁用", None
        
        user_data = result[0]
        user_id, db_username, name, email, password_hash, role, is_active = user_data
        
        # 验证密码
        if not self.verify_password(password, password_hash):
            return False, "密码错误", None
        
        # 更新最后登录时间
        update_query = "UPDATE User SET last_login = NOW() WHERE user_id = %s"
        execute_query(update_query, (user_id,))
        
        # 生成令牌
        token = self.generate_token(user_id, db_username, role)
        
        user_info = {
            'user_id': user_id,
            'username': db_username,
            'name': name,
            'email': email,
            'role': role,
            'token': token
        }
        
        return True, "登录成功", user_info
    
    def check_permission(self, user_role: str, required_permission: str) -> bool:
        """
        检查用户权限
        
        Args:
            user_role: 用户角色
            required_permission: 所需权限
            
        Returns:
            bool: 是否有权限
        """
        permissions = {
            'admin': ['manage_users', 'manage_data', 'view_all', 'export_data', 'llm_evaluation'],
            'evaluator': ['manage_data', 'view_all', 'llm_evaluation'],
            'guest': ['view_basic']
        }
        
        return required_permission in permissions.get(user_role, [])

# 全局认证管理器实例
auth_manager = AuthManager()

def create_default_admin() -> Tuple[bool, str]:
    """
    创建默认管理员账户
    
    Returns:
        Tuple[bool, str]: (是否成功, 消息)
    """
    # 检查是否已存在管理员账户
    query = "SELECT user_id FROM User WHERE role = 'admin' LIMIT 1"
    success, result = execute_query(query, None, fetch=True)
    
    if success and result:
        return True, "管理员账户已存在"
    
    # 创建默认管理员
    return auth_manager.register_user(
        username='admin',
        name='系统管理员',
        email='admin@example.com',
        password='admin123',  # 应该提示用户尽快修改
        role='admin'
    ) 
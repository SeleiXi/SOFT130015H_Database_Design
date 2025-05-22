import mysql.connector
from mysql.connector import Error
import pandas as pd

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',  # 请修改为你的实际密码
    'database': 'llm_qa_eval',  # 请修改为你的实际数据库名
}

def get_connection():
    """建立数据库连接"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"数据库连接错误: {e}")
        return None

def execute_query(query, params=None, fetch=False):
    """执行SQL查询"""
    conn = get_connection()
    result = None
    
    if conn is None:
        return False, "数据库连接失败"
    
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
        
        return True, result if fetch else "操作成功"
    except Error as e:
        return False, f"查询执行错误: {e}"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def create_tables():
    """创建所有数据库表"""
    create_tables_queries = [
        """
        CREATE TABLE IF NOT EXISTS ori_qs (
            ori_qs_id INT PRIMARY KEY AUTO_INCREMENT,
            content TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS updated_content (
            updated_content_version INT PRIMARY KEY AUTO_INCREMENT,
            content TEXT NOT NULL,
            operation VARCHAR(50) NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS llm_type (
            llm_type_id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL,
            params BIGINT NOT NULL,
            costs_per_million_token DECIMAL(10,2) NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS tags (
            tag_id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(50) NOT NULL UNIQUE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS User (
            user_id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL,
            role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'evaluator', 'guest'))
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS original_ans (
            ori_ans_id INT PRIMARY KEY AUTO_INCREMENT,
            content TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS standard_ans (
            ans_id INT PRIMARY KEY AUTO_INCREMENT,
            ans_content TEXT NOT NULL,
            ori_ans_id INT NOT NULL,
            eval_id INT,
            std_ans_id INT,
            std_qs_id INT,
            updated_content_version INT NOT NULL,
            FOREIGN KEY (ori_ans_id) REFERENCES original_ans(ori_ans_id),
            FOREIGN KEY (updated_content_version) REFERENCES updated_content(updated_content_version)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS llm_evaluation (
            eval_id INT PRIMARY KEY AUTO_INCREMENT,
            llm_answer TEXT NOT NULL,
            llm_type_id INT NOT NULL,
            std_ans_id INT NOT NULL,
            llm_score DECIMAL(5,2) NOT NULL,
            FOREIGN KEY (llm_type_id) REFERENCES llm_type(llm_type_id),
            FOREIGN KEY (std_ans_id) REFERENCES standard_ans(ans_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS standard_QS (
            std_qs_id INT PRIMARY KEY AUTO_INCREMENT,
            content TEXT NOT NULL,
            ori_qs_id INT NOT NULL,
            tag_id INT NOT NULL,
            std_ans_id INT,
            updated_content_version INT NOT NULL,
            FOREIGN KEY (ori_qs_id) REFERENCES ori_qs(ori_qs_id),
            FOREIGN KEY (tag_id) REFERENCES tags(tag_id),
            FOREIGN KEY (updated_content_version) REFERENCES updated_content(updated_content_version)
        )
        """,
        """
        ALTER TABLE standard_ans 
        ADD CONSTRAINT fk_std_ans_eval
        FOREIGN KEY (eval_id) REFERENCES llm_evaluation(eval_id)
        """,
        """
        ALTER TABLE standard_ans 
        ADD CONSTRAINT fk_std_ans_self
        FOREIGN KEY (std_ans_id) REFERENCES standard_ans(ans_id)
        """,
        """
        ALTER TABLE standard_ans 
        ADD CONSTRAINT fk_std_ans_qs
        FOREIGN KEY (std_qs_id) REFERENCES standard_QS(std_qs_id)
        """,
        """
        ALTER TABLE standard_QS 
        ADD CONSTRAINT fk_std_qs_ans
        FOREIGN KEY (std_ans_id) REFERENCES standard_ans(ans_id)
        """,
        """
        CREATE TABLE IF NOT EXISTS standard_pair (
            pair_id INT PRIMARY KEY AUTO_INCREMENT,
            std_qs_id INT NOT NULL,
            std_ans_id INT NOT NULL,
            eval_id INT NOT NULL,
            updated_content_version INT NOT NULL,
            FOREIGN KEY (std_qs_id) REFERENCES standard_QS(std_qs_id),
            FOREIGN KEY (std_ans_id) REFERENCES standard_ans(ans_id),
            FOREIGN KEY (eval_id) REFERENCES llm_evaluation(eval_id),
            FOREIGN KEY (updated_content_version) REFERENCES updated_content(updated_content_version)
        )
        """
    ]
    
    results = []
    for query in create_tables_queries:
        success, message = execute_query(query)
        results.append((success, message))
    
    return results

def get_table_names():
    """获取数据库中所有表名"""
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = %s
    """
    success, result = execute_query(query, (DB_CONFIG['database'],), True)
    
    if success and result:
        return [table[0] for table in result]
    return []

def get_table_data(table_name):
    """获取指定表的所有数据"""
    query = f"SELECT * FROM {table_name}"
    success, result = execute_query(query, fetch=True)
    
    if success:
        # 获取列名
        conn = get_connection()
        if conn is None:
            return False, "数据库连接失败"
        
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        cursor.close()
        conn.close()
        
        # 创建DataFrame
        df = pd.DataFrame(result, columns=columns)
        return True, df
    
    return False, result 
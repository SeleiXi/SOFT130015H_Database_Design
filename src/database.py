import mysql.connector
from mysql.connector import Error
import pandas as pd
import sys
import os

# 添加 configs 目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'configs'))

try:
    from database_config import DB_CONFIG, validate_config, print_config_info
except ImportError as e:
    print(f"❌ 无法导入配置文件: {e}")
    print("请确保 configs/database_config.py 文件存在")

def get_connection():
    """建立数据库连接"""
    try:
        # 验证配置
        if 'validate_config' in globals() and not validate_config():
            print("❌ 配置验证失败")
            return None
        
        # 创建连接，只使用 mysql.connector.connect 支持的参数
        connect_config = {
            'host': DB_CONFIG['host'],
            'user': DB_CONFIG['user'],
            'password': DB_CONFIG['password'],
            'database': DB_CONFIG['database'],
            'port': DB_CONFIG.get('port', 3306),
            'charset': DB_CONFIG.get('charset', 'utf8mb4'),
            'autocommit': DB_CONFIG.get('autocommit', True)
        }
        
        conn = mysql.connector.connect(**connect_config)
        return conn
    except Error as e:
        print(f"❌ 数据库连接错误: {e}")
        return None

def execute_query(query, params=None, fetch=False, many=False):
    """执行SQL查询"""
    conn = get_connection()
    result = None
    
    if conn is None:
        return False, "数据库连接失败"
    
    try:
        cursor = conn.cursor(buffered=True)  # 使用buffered=True避免"Unread result found"错误
        if many:  # 新增批量操作分支
            cursor.executemany(query, params)
        elif params:
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
    conn = get_connection()
    if conn is None:
        return False, "数据库连接失败"
    
    try:
        cursor = conn.cursor(buffered=True)  # 使用buffered=True避免"Unread result found"报错
        query = f"SELECT * FROM {table_name}"
        cursor.execute(query)
        
        columns = [column[0] for column in cursor.description]
        
        result = cursor.fetchall()
        
        # 不管有没有数据都能正确创建
        df = pd.DataFrame(result, columns=columns)
        
        return True, df
        
    except Error as e:
        return False, f"查询执行错误: {e}"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close() 

def batch_import_json_data(json_data_dict):
    """
    从解析后的JSON数据字典批量导入数据到多个表。
    json_data_dict: 格式为 {"table_name": [list_of_records]} 的字典。
                    每个 record 是一个字段名:值的字典。
    返回: 一个包含各表导入结果的字典。
    """
    results = {}
    conn = None 
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return {"error": "数据库连接失败"}

        cursor = conn.cursor(buffered=True)
        # It's better to get table names once if this function is called multiple times
        # or pass them if already available to avoid repeated DB calls.
        # For now, fetching them inside for atomicity of this function.
        db_name = DB_CONFIG.get('database')
        if not db_name:
            return {"error": "数据库名称未在配置中找到"}

        query_tables = "SELECT table_name FROM information_schema.tables WHERE table_schema = %s"
        cursor.execute(query_tables, (db_name,))
        available_tables_rows = cursor.fetchall()
        available_tables = [row[0] for row in available_tables_rows]

        for table_name, records in json_data_dict.items():
            if table_name not in available_tables:
                results[table_name] = {"success": False, "message": f"表 {table_name} 在数据库中不存在，跳过。", "inserted_count": 0, "skipped": True}
                continue
            
            if not isinstance(records, list) or not records:
                results[table_name] = {"success": True, "message": f"表 {table_name} 没有数据或数据格式不正确，跳过。", "inserted_count": 0, "skipped": True}
                continue

            # 获取目标表结构以确定有效列
            cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 0") # Use backticks for table name
            table_columns = [desc[0] for desc in cursor.description]
            
            rows_to_insert = []
            valid_columns_for_insert = []

            # Determine columns for INSERT from the first record, ensuring they exist in the table
            if records and isinstance(records[0], dict):
                first_record_keys = [key for key in records[0].keys() if key in table_columns]
                if not first_record_keys:
                    results[table_name] = {"success": False, "message": f"表 {table_name} 的JSON数据中没有与表列匹配的字段。", "inserted_count": 0}
                    continue
                valid_columns_for_insert = first_record_keys
            else:
                results[table_name] = {"success": False, "message": f"表 {table_name} 的记录不是字典格式或为空。", "inserted_count": 0}
                continue
                
            placeholders = ", ".join(["%s"] * len(valid_columns_for_insert))
            # Use backticks for table and column names to handle special characters or reserved words
            sql_query = f"INSERT INTO `{table_name}` ({', '.join([f'`{col}`' for col in valid_columns_for_insert])}) VALUES ({placeholders})"

            for record in records:
                if isinstance(record, dict):
                    row_values = [record.get(col) for col in valid_columns_for_insert]
                    rows_to_insert.append(tuple(row_values))
                else:
                    # Skip non-dict records or log them
                    pass # Or add to a list of skipped records for this table
            
            if not rows_to_insert:
                results[table_name] = {"success": True, "message": f"表 {table_name} 的JSON数据处理后没有可导入的行。", "inserted_count": 0, "skipped": False}
                continue

            try:
                # MySQL autocommits executemany by default if autocommit is True for the connection
                cursor.executemany(sql_query, rows_to_insert)
                # No explicit conn.commit() needed here if autocommit=True, but doesn't hurt for clarity or if autocommit is False.
                conn.commit() 
                inserted_count = cursor.rowcount if cursor.rowcount != -1 else len(rows_to_insert)
                results[table_name] = {"success": True, "message": f"成功导入 {inserted_count} 条记录。", "inserted_count": inserted_count}
            except Error as e:
                conn.rollback()
                results[table_name] = {"success": False, "message": f"导入时发生错误: {str(e)}", "inserted_count": 0, "errors": [str(e)]}
            
        return results

    except Error as e:
        # General error not specific to a table import
        return {"error": f"数据库操作错误: {e}"}
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close() 
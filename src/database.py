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
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FULLTEXT INDEX ft_content (content)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS updated_content (
            updated_content_version INT PRIMARY KEY AUTO_INCREMENT,
            content TEXT NOT NULL,
            operation VARCHAR(50) NOT NULL CHECK (operation IN ('CREATE', 'EDIT', 'DELETE', 'REVIEW', 'APPROVE', 'MERGE')),
            created_by INT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_operation (operation),
            INDEX idx_created_at (created_at),
            FOREIGN KEY (created_by) REFERENCES User(user_id) ON DELETE SET NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS llm_type (
            llm_type_id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,
            params BIGINT NOT NULL CHECK (params > 0),
            costs_per_million_token DECIMAL(10,2) NOT NULL CHECK (costs_per_million_token >= 0),
            description TEXT DEFAULT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_name (name),
            INDEX idx_is_active (is_active)
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
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(100) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'guest' CHECK (role IN ('admin', 'evaluator', 'guest', 'user')),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP NULL DEFAULT NULL,
            INDEX idx_username (username),
            INDEX idx_role (role),
            INDEX idx_is_active (is_active)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ori_ans (
            ori_ans_id INT PRIMARY KEY AUTO_INCREMENT,
            content TEXT NOT NULL,
            ori_qs_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_ori_qs (ori_qs_id),
            FULLTEXT INDEX ft_content (content),
            FOREIGN KEY (ori_qs_id) REFERENCES ori_qs(ori_qs_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS standard_ans (
            ans_id INT PRIMARY KEY AUTO_INCREMENT,
            ans_content TEXT NOT NULL,
            ori_ans_id INT NOT NULL,
            eval_id INT DEFAULT NULL,
            std_ans_id INT DEFAULT NULL,
            std_qs_id INT DEFAULT NULL,
            updated_content_version INT NOT NULL,
            created_by INT DEFAULT NULL,
            approved_by INT DEFAULT NULL,
            status ENUM('draft', 'review', 'approved', 'archived') DEFAULT 'draft',
            quality_score DECIMAL(3,2) DEFAULT NULL CHECK (quality_score >= 0 AND quality_score <= 5),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_ori_ans (ori_ans_id),
            INDEX idx_status (status),
            INDEX idx_quality_score (quality_score),
            INDEX idx_created_at (created_at),
            FULLTEXT INDEX ft_ans_content (ans_content),
            FOREIGN KEY (ori_ans_id) REFERENCES ori_ans(ori_ans_id) ON DELETE CASCADE,
            FOREIGN KEY (updated_content_version) REFERENCES updated_content(updated_content_version) ON DELETE RESTRICT,
            FOREIGN KEY (created_by) REFERENCES User(user_id) ON DELETE SET NULL,
            FOREIGN KEY (approved_by) REFERENCES User(user_id) ON DELETE SET NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS llm_evaluation (
            eval_id INT PRIMARY KEY AUTO_INCREMENT,
            llm_answer TEXT NOT NULL,
            llm_type_id INT NOT NULL,
            std_ans_id INT NOT NULL,
            llm_score DECIMAL(5,2) NOT NULL CHECK (llm_score >= 0 AND llm_score <= 100),
            evaluated_by INT DEFAULT NULL,
            evaluation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT DEFAULT NULL,
            INDEX idx_llm_type (llm_type_id),
            INDEX idx_std_ans (std_ans_id),
            INDEX idx_score (llm_score),
            INDEX idx_evaluation_date (evaluation_date),
            FOREIGN KEY (llm_type_id) REFERENCES llm_type(llm_type_id) ON DELETE CASCADE,
            FOREIGN KEY (std_ans_id) REFERENCES standard_ans(ans_id) ON DELETE CASCADE,
            FOREIGN KEY (evaluated_by) REFERENCES User(user_id) ON DELETE SET NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS standard_QS (
            std_qs_id INT PRIMARY KEY AUTO_INCREMENT,
            content TEXT NOT NULL,
            ori_qs_id INT NOT NULL,
            tag_id INT NOT NULL,
            std_ans_id INT DEFAULT NULL,
            updated_content_version INT NOT NULL,
            created_by INT DEFAULT NULL,
            approved_by INT DEFAULT NULL,
            status ENUM('draft', 'review', 'approved', 'archived') DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_ori_qs (ori_qs_id),
            INDEX idx_tag (tag_id),
            INDEX idx_status (status),
            INDEX idx_created_at (created_at),
            FULLTEXT INDEX ft_content (content),
            FOREIGN KEY (ori_qs_id) REFERENCES ori_qs(ori_qs_id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE RESTRICT,
            FOREIGN KEY (updated_content_version) REFERENCES updated_content(updated_content_version) ON DELETE RESTRICT,
            FOREIGN KEY (created_by) REFERENCES User(user_id) ON DELETE SET NULL,
            FOREIGN KEY (approved_by) REFERENCES User(user_id) ON DELETE SET NULL
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS standard_pair (
            pair_id INT PRIMARY KEY AUTO_INCREMENT,
            std_qs_id INT NOT NULL,
            std_ans_id INT NOT NULL,
            eval_id INT NOT NULL,
            updated_content_version INT NOT NULL,
            created_by INT DEFAULT NULL,
            confidence_score DECIMAL(3,2) DEFAULT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
            is_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified_at TIMESTAMP NULL DEFAULT NULL,
            INDEX idx_std_qs (std_qs_id),
            INDEX idx_std_ans (std_ans_id),
            INDEX idx_eval (eval_id),
            INDEX idx_confidence (confidence_score),
            INDEX idx_verified (is_verified),
            FOREIGN KEY (std_qs_id) REFERENCES standard_QS(std_qs_id) ON DELETE CASCADE,
            FOREIGN KEY (std_ans_id) REFERENCES standard_ans(ans_id) ON DELETE CASCADE,
            FOREIGN KEY (eval_id) REFERENCES llm_evaluation(eval_id) ON DELETE CASCADE,
            FOREIGN KEY (updated_content_version) REFERENCES updated_content(updated_content_version) ON DELETE RESTRICT,
            FOREIGN KEY (created_by) REFERENCES User(user_id) ON DELETE SET NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id VARCHAR(128) PRIMARY KEY,
            user_id INT NOT NULL,
            ip_address VARCHAR(45) DEFAULT NULL,
            user_agent TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            INDEX idx_user_id (user_id),
            INDEX idx_expires_at (expires_at),
            INDEX idx_is_active (is_active),
            FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS system_logs (
            log_id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT DEFAULT NULL,
            action VARCHAR(100) NOT NULL,
            table_name VARCHAR(50) DEFAULT NULL,
            record_id INT DEFAULT NULL,
            old_values JSON DEFAULT NULL,
            new_values JSON DEFAULT NULL,
            ip_address VARCHAR(45) DEFAULT NULL,
            user_agent TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_action (action),
            INDEX idx_table_name (table_name),
            INDEX idx_created_at (created_at),
            FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE SET NULL
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

def get_paginated_query(query, params=None, page=1, page_size=10):
    """执行分页查询"""
    offset = (page - 1) * page_size
    
    # 获取总数的查询
    count_query = f"SELECT COUNT(*) FROM ({query}) as count_table"
    success_count, total_result = execute_query(count_query, params, True)
    
    if not success_count:
        return False, "获取总数失败", 0, []
    
    total_count = total_result[0][0] if total_result else 0
    total_pages = (total_count + page_size - 1) // page_size
    
    # 分页查询
    paginated_query = f"{query} LIMIT %s OFFSET %s"
    final_params = list(params) if params else []
    final_params.extend([page_size, offset])
    
    success, result = execute_query(paginated_query, final_params, True)
    
    if success:
        return True, "查询成功", total_count, result, total_pages
    else:
        return False, result, 0, [], 0


        # oq.content as question_content,
def get_all_questions_with_answers(page=1, page_size=10):
    """获取所有问题及其对应的答案"""
    query = """
        SELECT
            oq.content AS question_content,
            COALESCE(oa.content, '暂无原答案') AS original_answer_content,
            COALESCE(sa.ans_content, '暂无标准答案') AS standard_answer_content
        FROM ori_qs oq
        LEFT JOIN ori_ans oa ON oq.ori_qs_id = oa.ori_qs_id
        LEFT JOIN standard_ans sa ON oa.ori_ans_id = sa.ori_ans_id
        ORDER BY oq.ori_qs_id
    """
    
    #     SELECT 
    #     sp.pair_id,
    #     sq.content as question, 
    #     sa.ans_content as answer,
    #     t.name as tag,
    #     uc.operation as last_operation,
    #     uc.content as update_info
    # FROM standard_pair sp # 用pair来join的
    # INNER JOIN standard_QS sq ON sp.std_qs_id = sq.std_qs_id
    # INNER JOIN standard_ans sa ON sp.std_ans_id = sa.ans_id
    # INNER JOIN tags t ON sq.tag_id = t.tag_id
    # INNER JOIN updated_content uc ON sp.updated_content_version = uc.updated_content_version
    # ORDER BY sp.pair_id
    
    return get_paginated_query(query, None, page, page_size)

def get_questions_with_tags(page=1, page_size=10):
    """获取带标签的问题"""
    query = """
    SELECT 
        sq.std_qs_id,
        sq.content as question_content,
        t.name as tag_name,
        oq.content as original_question
    FROM standard_QS sq
    INNER JOIN tags t ON sq.tag_id = t.tag_id
    INNER JOIN ori_qs oq ON sq.ori_qs_id = oq.ori_qs_id
    ORDER BY t.name, sq.std_qs_id
    """
    return get_paginated_query(query, None, page, page_size)

def get_llm_evaluation_results(page=1, page_size=10):
    """获取LLM评估结果 - 只返回有关联问题的评估记录"""
    # 只查询有真实问题关联的评估记录，按问题ID排序
    query = """
    SELECT 
        le.eval_id,
        lt.name as llm_model,
        lt.params as model_params,
        le.llm_score,
        oa.content as standard_answer,
        le.llm_answer,
        oq.content as question_content,
        oq.ori_qs_id as question_id
    FROM llm_evaluation le
    INNER JOIN llm_type lt ON le.llm_type_id = lt.llm_type_id
    INNER JOIN ori_ans oa ON le.std_ans_id = oa.ori_ans_id
    INNER JOIN ori_qs oq ON oa.ori_qs_id = oq.ori_qs_id
    WHERE oq.content IS NOT NULL
    ORDER BY oq.ori_qs_id ASC, le.llm_score DESC
    """
    return get_paginated_query(query, None, page, page_size)

def get_top_scored_answers(page=1, page_size=10):
    """获取高分答案排行"""
    query = """
    SELECT 
        le.std_ans_id as ans_id,
        COALESCE(oa.content, CONCAT('原始答案ID: ', le.std_ans_id)) as ans_content,
        AVG(le.llm_score) as avg_score,
        COUNT(le.eval_id) as evaluation_count,
        COALESCE(oq.content, '无关联问题') as question_content
    FROM llm_evaluation le
    LEFT JOIN ori_ans oa ON le.std_ans_id = oa.ori_ans_id
    LEFT JOIN ori_qs oq ON oa.ori_qs_id = oq.ori_qs_id
    GROUP BY le.std_ans_id, oa.content, oq.content
    HAVING evaluation_count > 0
    ORDER BY avg_score DESC
    """
    return get_paginated_query(query, None, page, page_size)

def get_question_answer_pairs(page=1, page_size=10):
    """获取完整的问答配对"""
    query = """
    SELECT 
        sp.pair_id,
        sq.content as question,
        sa.ans_content as answer,
        t.name as tag,
        uc.operation as last_operation,
        uc.content as update_info
    FROM standard_pair sp
    INNER JOIN standard_QS sq ON sp.std_qs_id = sq.std_qs_id
    INNER JOIN standard_ans sa ON sp.std_ans_id = sa.ans_id
    INNER JOIN tags t ON sq.tag_id = t.tag_id
    INNER JOIN updated_content uc ON sp.updated_content_version = uc.updated_content_version
    ORDER BY sp.pair_id
    """
    return get_paginated_query(query, None, page, page_size)

def get_model_performance_comparison(page=1, page_size=10):
    """获取模型性能比较"""
    query = """
    SELECT 
        lt.name as model_name,
        lt.params as model_params,
        COUNT(le.eval_id) as total_evaluations,
        AVG(le.llm_score) as avg_score,
        MAX(le.llm_score) as max_score,
        MIN(le.llm_score) as min_score,
        lt.costs_per_million_token as cost_per_million
    FROM llm_type lt
    LEFT JOIN llm_evaluation le ON lt.llm_type_id = le.llm_type_id
    GROUP BY lt.llm_type_id, lt.name, lt.params, lt.costs_per_million_token
    ORDER BY avg_score DESC
    """
    return get_paginated_query(query, None, page, page_size)

def get_questions_by_tag(tag_name, page=1, page_size=10):
    """根据标签获取问题"""
    query = """
    SELECT 
        sq.std_qs_id,
        sq.content as question,
        sa.ans_content as answer,
        t.name as tag
    FROM standard_QS sq
    INNER JOIN tags t ON sq.tag_id = t.tag_id
    LEFT JOIN standard_ans sa ON sq.std_ans_id = sa.ans_id
    WHERE t.name = %s
    ORDER BY sq.std_qs_id
    """
    return get_paginated_query(query, (tag_name,), page, page_size)

def get_answers_by_score_range(min_score, max_score, page=1, page_size=10):
    """根据评分范围获取答案"""
    query = """
    SELECT DISTINCT
        le.std_ans_id as ans_id,
        COALESCE(oa.content, CONCAT('原始答案ID: ', le.std_ans_id)) as ans_content,
        le.llm_score,
        COALESCE(oq.content, '无关联问题') as question,
        lt.name as model_name
    FROM llm_evaluation le
    INNER JOIN llm_type lt ON le.llm_type_id = lt.llm_type_id
    LEFT JOIN ori_ans oa ON le.std_ans_id = oa.ori_ans_id
    LEFT JOIN ori_qs oq ON oa.ori_qs_id = oq.ori_qs_id
    WHERE le.llm_score BETWEEN %s AND %s
    ORDER BY le.llm_score DESC
    """
    return get_paginated_query(query, (min_score, max_score), page, page_size)

def get_recent_updates(page=1, page_size=10):
    """获取最近更新的内容"""
    query = """
    SELECT 
        uc.updated_content_version,
        uc.operation,
        uc.content as update_description,
        COUNT(DISTINCT sq.std_qs_id) as affected_questions,
        COUNT(DISTINCT sa.ans_id) as affected_answers
    FROM updated_content uc
    LEFT JOIN standard_QS sq ON uc.updated_content_version = sq.updated_content_version
    LEFT JOIN standard_ans sa ON uc.updated_content_version = sa.updated_content_version
    GROUP BY uc.updated_content_version, uc.operation, uc.content
    ORDER BY uc.updated_content_version DESC
    """
    return get_paginated_query(query, None, page, page_size)

def search_content(search_term, page=1, page_size=10):
    """搜索问题和答案内容"""
    query = """
    SELECT 
        'Question' as content_type,
        sq.std_qs_id as id,
        sq.content as content,
        t.name as tag
    FROM standard_QS sq
    INNER JOIN tags t ON sq.tag_id = t.tag_id
    WHERE sq.content LIKE %s
    
    UNION ALL
    
    SELECT 
        'Answer' as content_type,
        sa.ans_id as id,
        sa.ans_content as content,
        NULL as tag
    FROM standard_ans sa
    WHERE sa.ans_content LIKE %s
    
    ORDER BY content_type, id
    """
    search_pattern = f"%{search_term}%"
    return get_paginated_query(query, (search_pattern, search_pattern), page, page_size)

def get_database_statistics():
    """获取数据库统计信息"""
    stats_queries = {
        "总问题数": "SELECT COUNT(*) FROM ori_qs",
        "总答案数": "SELECT COUNT(*) FROM ori_ans", 
        "标准问题数": "SELECT COUNT(*) FROM standard_QS",
        "标准答案数": "SELECT COUNT(*) FROM standard_ans",
        "评估记录数": "SELECT COUNT(*) FROM llm_evaluation",
        "问答配对数": "SELECT COUNT(*) FROM standard_pair",
        "标签数量": "SELECT COUNT(*) FROM tags",
        "LLM模型数": "SELECT COUNT(*) FROM llm_type",
        "更新记录数": "SELECT COUNT(*) FROM updated_content"
    }
    
    results = {}
    for stat_name, query in stats_queries.items():
        success, result = execute_query(query, None, True)
        if success and result:
            results[stat_name] = result[0][0]
        else:
            results[stat_name] = 0
    
    return results

def get_tag_distribution(page=1, page_size=10):
    """获取标签分布统计"""
    query = """
    SELECT 
        t.name as tag_name,
        COUNT(sq.std_qs_id) as question_count,
        COUNT(DISTINCT sa.ans_id) as answer_count
    FROM tags t
    LEFT JOIN standard_QS sq ON t.tag_id = sq.tag_id
    LEFT JOIN standard_ans sa ON sq.std_ans_id = sa.ans_id
    GROUP BY t.tag_id, t.name
    ORDER BY question_count DESC
    """
    return get_paginated_query(query, None, page, page_size)

def get_model_cost_analysis(page=1, page_size=10):
    """获取模型成本分析"""
    query = """
    SELECT 
        lt.name as model_name,
        lt.params as parameters,
        lt.costs_per_million_token as cost_per_million,
        COUNT(le.eval_id) as total_evaluations,
        AVG(le.llm_score) as avg_score,
        (COUNT(le.eval_id) * lt.costs_per_million_token / 1000000) as estimated_cost
    FROM llm_type lt
    LEFT JOIN llm_evaluation le ON lt.llm_type_id = le.llm_type_id
    GROUP BY lt.llm_type_id, lt.name, lt.params, lt.costs_per_million_token
    ORDER BY estimated_cost DESC
    """
    return get_paginated_query(query, None, page, page_size)

def get_evaluation_trends(page=1, page_size=10):
    """获取评估趋势分析"""
    query = """
    SELECT 
        le.eval_id,
        lt.name as model_name,
        le.llm_score,
        CASE 
            WHEN le.llm_score >= 80 THEN '优秀'
            WHEN le.llm_score >= 60 THEN '良好'
            WHEN le.llm_score >= 40 THEN '一般'
            ELSE '较差'
        END as score_category,
        sa.ans_content as answer_preview
    FROM llm_evaluation le
    JOIN llm_type lt ON le.llm_type_id = lt.llm_type_id
    JOIN standard_ans sa ON le.std_ans_id = sa.ans_id
    ORDER BY le.llm_score DESC
    """
    return get_paginated_query(query, None, page, page_size)

def get_answer_length_analysis(page=1, page_size=10):
    """获取答案长度分析"""
    query = """
    SELECT 
        sa.ans_id,
        CHAR_LENGTH(sa.ans_content) as answer_length,
        AVG(le.llm_score) as avg_score,
        COUNT(le.eval_id) as evaluation_count,
        CASE 
            WHEN CHAR_LENGTH(sa.ans_content) < 100 THEN '短'
            WHEN CHAR_LENGTH(sa.ans_content) < 500 THEN '中'
            ELSE '长'
        END as length_category,
        LEFT(sa.ans_content, 100) as answer_preview
    FROM standard_ans sa
    LEFT JOIN llm_evaluation le ON sa.ans_id = le.std_ans_id
    GROUP BY sa.ans_id, sa.ans_content
    ORDER BY answer_length DESC
    """
    return get_paginated_query(query, None, page, page_size)

def get_question_complexity_analysis(page=1, page_size=10):
    """获取问题复杂度分析"""
    query = """
    SELECT 
        sq.std_qs_id,
        sq.content as question,
        CHAR_LENGTH(sq.content) as question_length,
        t.name as tag,
        COUNT(DISTINCT sa.ans_id) as answer_count,
        AVG(le.llm_score) as avg_score,
        CASE 
            WHEN CHAR_LENGTH(sq.content) < 50 THEN '简单'
            WHEN CHAR_LENGTH(sq.content) < 150 THEN '中等'
            ELSE '复杂'
        END as complexity_level
    FROM standard_QS sq
    LEFT JOIN tags t ON sq.tag_id = t.tag_id
    LEFT JOIN standard_ans sa ON sq.std_ans_id = sa.ans_id
    LEFT JOIN llm_evaluation le ON sa.ans_id = le.std_ans_id
    GROUP BY sq.std_qs_id, sq.content, t.name
    ORDER BY question_length DESC
    """
    return get_paginated_query(query, None, page, page_size)

def get_orphan_records(page=1, page_size=10):
    """获取孤立记录（没有关联的记录）"""
    query = """
    SELECT 
        'Questions without Answers' as record_type,
        oq.ori_qs_id as id,
        oq.content as content,
        'No associated answers' as issue
    FROM ori_qs oq
    LEFT JOIN standard_QS sq ON oq.ori_qs_id = sq.ori_qs_id
    WHERE sq.std_qs_id IS NULL
    
    UNION ALL
    
    SELECT 
        'Answers without Questions' as record_type,
        oa.ori_ans_id as id,
        LEFT(oa.content, 100) as content,
        'No associated questions' as issue
    FROM ori_ans oa
    LEFT JOIN standard_ans sa ON oa.ori_ans_id = sa.ori_ans_id
    LEFT JOIN standard_QS sq ON sa.std_qs_id = sq.std_qs_id
    WHERE sq.std_qs_id IS NULL
    
    ORDER BY record_type, id
    """
    return get_paginated_query(query, None, page, page_size)

def get_evaluation_score_distribution():
    """获取评估分数分布"""
    query = """
    SELECT 
        CASE 
            WHEN llm_score >= 90 THEN '90-100'
            WHEN llm_score >= 80 THEN '80-89'
            WHEN llm_score >= 70 THEN '70-79'
            WHEN llm_score >= 60 THEN '60-69'
            WHEN llm_score >= 50 THEN '50-59'
            ELSE '< 50'
        END as score_range,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM llm_evaluation), 2) as percentage
    FROM llm_evaluation
    GROUP BY 
        CASE 
            WHEN llm_score >= 90 THEN '90-100'
            WHEN llm_score >= 80 THEN '80-89'
            WHEN llm_score >= 70 THEN '70-79'
            WHEN llm_score >= 60 THEN '60-69'
            WHEN llm_score >= 50 THEN '50-59'
            ELSE '< 50'
        END
    ORDER BY score_range DESC
    """
    success, result = execute_query(query, None, True)
    if success:
        return True, "查询成功", result
    else:
        return False, result, [] 
import streamlit as st
import pandas as pd

def show_success_message(message):
    """显示成功消息"""
    st.success(message)

def show_error_message(message):
    """显示错误消息"""
    st.error(message)

def show_warning_message(message):
    """显示警告消息"""
    st.warning(message)

def show_table_data(table_name, data):
    """显示表数据"""
    if data.empty:
        st.info(f"{table_name} 表中没有数据")
    else:
        st.write(f"### {table_name} 表数据")
        st.dataframe(data)

def get_table_schema(table_name, conn):
    """获取完整表结构信息（增强版）"""
    try:
        cursor = conn.cursor()
        
        # 获取基础列信息
        cursor.execute(f"""
            SELECT 
                COLUMN_NAME,
                COLUMN_TYPE,
                IS_NULLABLE,
                COLUMN_KEY,
                COLUMN_DEFAULT,
                EXTRA,
                COLUMN_COMMENT,
                CHARACTER_SET_NAME,
                COLLATION_NAME
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """, (table_name,))
        
        columns = cursor.fetchall()
        
        # 获取索引信息
        cursor.execute(f"SHOW INDEX FROM {table_name}")
        indexes = cursor.fetchall()
        
        # 构建列信息
        schema_data = []
        for col in columns:
            schema_data.append({
                "字段名": col[0],
                "类型": col[1],
                "允许NULL": "是" if col[2] == "YES" else "否",
                "键类型": _parse_key_type(col[3], indexes),
                "默认值": _parse_default_value(col[4]),
                "额外属性": col[5],
                "注释": col[6] or "",
                "字符集": col[7] or "",
                "排序规则": col[8] or ""
            })
        
        # 添加外键信息
        cursor.execute(f"""
            SELECT 
                COLUMN_NAME,
                CONSTRAINT_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = %s 
                AND REFERENCED_TABLE_NAME IS NOT NULL
        """, (table_name,))
        
        foreign_keys = cursor.fetchall()
        for fk in foreign_keys:
            for col_info in schema_data:
                if col_info["字段名"] == fk[0]:
                    col_info.update({
                        "外键约束": fk[1],
                        "引用表": fk[2],
                        "引用字段": fk[3]
                    })
        
        cursor.close()
        return pd.DataFrame(schema_data)
    
    except Exception as e:
        st.error(f"获取表结构失败: {str(e)}")
        return pd.DataFrame()

def _parse_key_type(key_flag, indexes):
    """解析键类型"""
    if "PRI" in key_flag:
        return "主键"
    if "UNI" in key_flag:
        return "唯一键"
    
    # 检查是否为外键
    for index in indexes:
        if index[2] == "FOREIGN":
            return "外键"
    return ""

def _parse_default_value(value):
    """处理默认值显示"""
    if value is None:
        return "NULL"
    if isinstance(value, str) and value.upper() == "CURRENT_TIMESTAMP":
        return "当前时间"
    return str(value)

def show_table_schema(table_name, conn):
    """显示表结构"""
    schema_df = get_table_schema(table_name, conn)
    st.write(f"### {table_name} 表结构")
    st.dataframe(schema_df)

def generate_sample_data(format_type="multi_table"):
    """
    生成示例JSON数据。
    format_type: "multi_table" (默认) 返回多表结构的字典，用于批量导入。
                 "single_table_ori_qs" 返回ori_qs表的示例数据列表，用于单表导入。
    """
    if format_type == "single_table_ori_qs":
        return [
            {"content": "如何优化MySQL查询性能？这是一个单表示例。"},
            {"content": "数据库设计的三大范式是什么？单表示例。"}
        ]
    
    # multi_table format (default)
    return {
        "ori_qs": [
            {"content": "如何优化MySQL查询性能？(来自批量JSON)"},
            {"content": "数据库设计的三大范式是什么？(来自批量JSON)"}
        ],
        "tags": [
            {"name": "性能优化"},
            {"name": "数据库设计"}
        ],
        "original_ans": [ # 假设 original_ans 表有 content 字段
            {"content": "批量导入：可以通过添加合适的索引来优化查询..."},
            {"content": "批量导入：第一范式要求字段原子性..."}
        ]
        # 注意：如果表之间存在严格的插入顺序（如外键约束），
        # 用户提供的JSON数据需要自行保证顺序，或分批导入。
        # 此示例数据较为简单，不包含复杂的外键关系数据。
    }

def download_sample_json(format_type="multi_table"):
    """生成可供下载的示例JSON"""
    import json
    from io import BytesIO
    data = generate_sample_data(format_type=format_type)
    return BytesIO(json.dumps(data, indent=2, ensure_ascii=False).encode()) 
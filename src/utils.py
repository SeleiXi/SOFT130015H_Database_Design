import streamlit as st
import pandas as pd

def show_success_message(message):
    """显示成功消息"""
    st.success(message)

def show_error_message(message):
    """显示错误消息"""
    st.error(message)

def show_table_data(table_name, data):
    """显示表数据"""
    if data.empty:
        st.info(f"{table_name} 表中没有数据")
    else:
        st.write(f"### {table_name} 表数据")
        st.dataframe(data)

def get_table_schema(table_name, conn):
    """获取表结构信息"""
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE {table_name}")
    columns = cursor.fetchall()
    
    schema_data = []
    for col in columns:
        schema_data.append({
            "字段名": col[0],
            "类型": col[1],
            "允许NULL": "是" if col[2] == "YES" else "否",
            "键": col[3],
            "默认值": col[4],
            "额外": col[5]
        })
    
    cursor.close()
    return pd.DataFrame(schema_data)

def show_table_schema(table_name, conn):
    """显示表结构"""
    schema_df = get_table_schema(table_name, conn)
    st.write(f"### {table_name} 表结构")
    st.dataframe(schema_df) 
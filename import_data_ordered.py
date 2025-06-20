#!/usr/bin/env python3
"""
按正确顺序导入数据的脚本
考虑外键依赖关系，按顺序导入各个表
"""

import json
import logging
from src.database import batch_import_json_data, get_connection

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_data_in_order():
    """按依赖关系顺序导入数据"""
    try:
        # 读取完整数据
        with open('data/data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info("开始按顺序导入数据...")
        
        # 定义导入顺序（基础表先导入，有外键依赖的表后导入）
        import_order = [
            # 1. 基础表（无外键依赖）
            'ori_qs',          # 原始问题
            'tags',            # 标签
            'original_ans',    # 原始答案  
            'llm_type',        # LLM类型
            'user',            # 用户表
            'updated_content', # 更新内容
            
            # 2. 有依赖关系的表
            'standard_ans',    # 标准答案（依赖original_ans, updated_content）
            'standard_qs',     # 标准问题（依赖ori_qs, tags, updated_content, user）
            'llm_evaluation',  # LLM评估（依赖llm_type, standard_ans, user）
            'standard_pair',   # 标准问答对（依赖standard_qs, standard_ans, llm_evaluation, updated_content, user）
        ]
        
        total_imported = 0
        all_results = {}
        
        for table_name in import_order:
            if table_name in data:
                logger.info(f"\n正在导入表: {table_name}")
                logger.info(f"记录数: {len(data[table_name])}")
                
                # 单表导入
                table_data = {table_name: data[table_name]}
                result = batch_import_json_data(table_data)
                
                all_results[table_name] = result.get(table_name, {})
                
                if result.get(table_name, {}).get("success"):
                    imported_count = result[table_name].get("inserted_count", 0)
                    total_imported += imported_count
                    logger.info(f"✅ {table_name}: 成功导入 {imported_count} 条记录")
                else:
                    error_msg = result.get(table_name, {}).get("message", "未知错误")
                    logger.error(f"❌ {table_name}: 导入失败 - {error_msg}")
                    
                    # 如果是关键表导入失败，询问是否继续
                    if table_name in ['user', 'llm_type', 'ori_qs', 'tags']:
                        logger.error(f"关键表 {table_name} 导入失败，可能影响后续表的导入")
                        
            else:
                logger.warning(f"数据中未找到表: {table_name}")
        
        logger.info(f"\n🎉 数据导入完成！总共导入 {total_imported} 条记录")
        
        # 显示导入摘要
        logger.info("\n📊 导入摘要:")
        for table_name, result in all_results.items():
            if result.get("success"):
                count = result.get("inserted_count", 0)
                logger.info(f"  ✅ {table_name}: {count} 条记录")
            else:
                logger.info(f"  ❌ {table_name}: 失败")
        
        return all_results
        
    except Exception as e:
        logger.error(f"导入数据时发生错误: {e}")
        return {"error": str(e)}

def check_table_dependencies():
    """检查表之间的依赖关系"""
    try:
        logger.info("检查表依赖关系...")
        
        conn = get_connection()
        if not conn:
            logger.error("数据库连接失败")
            return False
        
        cursor = conn.cursor()
        
        # 查询外键约束
        fk_query = """
        SELECT 
            TABLE_NAME,
            COLUMN_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE REFERENCED_TABLE_SCHEMA = DATABASE()
        AND REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY TABLE_NAME, COLUMN_NAME
        """
        
        cursor.execute(fk_query)
        fk_constraints = cursor.fetchall()
        
        logger.info("外键依赖关系:")
        for fk in fk_constraints:
            logger.info(f"  {fk[0]}.{fk[1]} -> {fk[2]}.{fk[3]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"检查依赖关系时发生错误: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始有序数据导入")
    
    # 1. 检查表依赖关系
    check_table_dependencies()
    
    # 2. 按顺序导入数据
    result = import_data_in_order()
    
    if "error" in result:
        logger.error(f"导入失败: {result['error']}")
    else:
        logger.info("数据导入任务完成!")

if __name__ == "__main__":
    main() 
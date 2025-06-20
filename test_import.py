#!/usr/bin/env python3
"""
测试修复后的数据导入功能
"""

import json
import logging
from src.database import batch_import_json_data, get_connection

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_llm_evaluation_import():
    """测试llm_evaluation表的数据导入"""
    try:
        # 读取修复后的数据
        with open('data/data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 只导入llm_evaluation表的前几条记录进行测试
        test_data = {
            "llm_evaluation": data["llm_evaluation"][:3]  # 只测试前3条记录
        }
        
        logger.info("开始测试llm_evaluation表数据导入...")
        logger.info(f"测试数据包含 {len(test_data['llm_evaluation'])} 条记录")
        
        # 显示第一条记录的llm_answer字段格式
        first_record = test_data["llm_evaluation"][0]
        logger.info(f"第一条记录的llm_answer字段类型: {type(first_record['llm_answer'])}")
        logger.info(f"llm_answer内容预览: {first_record['llm_answer'][:100]}...")
        
        # 尝试导入
        result = batch_import_json_data(test_data)
        
        logger.info("导入结果:")
        for table_name, table_result in result.items():
            if table_result.get("success"):
                logger.info(f"✅ {table_name}: {table_result['message']}")
            else:
                logger.error(f"❌ {table_name}: {table_result['message']}")
                if "errors" in table_result:
                    for error in table_result["errors"]:
                        logger.error(f"   错误详情: {error}")
        
        return result
        
    except Exception as e:
        logger.error(f"测试导入时发生错误: {e}")
        return {"error": str(e)}

def test_database_connection():
    """测试数据库连接"""
    try:
        conn = get_connection()
        if conn:
            logger.info("✅ 数据库连接成功")
            conn.close()
            return True
        else:
            logger.error("❌ 数据库连接失败")
            return False
    except Exception as e:
        logger.error(f"❌ 数据库连接错误: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始测试修复后的数据导入功能")
    
    # 1. 测试数据库连接
    if not test_database_connection():
        logger.error("数据库连接失败，终止测试")
        return
    
    # 2. 测试llm_evaluation表导入
    result = test_llm_evaluation_import()
    
    if "error" in result:
        logger.error(f"测试失败: {result['error']}")
    elif "llm_evaluation" in result and result["llm_evaluation"].get("success"):
        logger.info("🎉 测试成功！数据格式修复有效，可以正常导入")
    else:
        logger.error("测试失败，请检查错误信息")

if __name__ == "__main__":
    main() 
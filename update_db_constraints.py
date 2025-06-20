#!/usr/bin/env python3
"""
更新数据库约束条件的脚本
将llm_evaluation表的llm_score字段约束从0-5更新为0-100
"""

import logging
from src.database import get_connection, execute_query

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_llm_evaluation_constraints():
    """更新llm_evaluation表的约束条件"""
    try:
        logger.info("开始更新llm_evaluation表的约束条件...")
        
        # 获取数据库连接
        conn = get_connection()
        if not conn:
            logger.error("数据库连接失败")
            return False
        
        cursor = conn.cursor()
        
        # 首先检查当前约束
        logger.info("检查当前表约束...")
        check_constraints_query = """
        SELECT CONSTRAINT_NAME, CHECK_CLAUSE 
        FROM information_schema.CHECK_CONSTRAINTS 
        WHERE CONSTRAINT_SCHEMA = DATABASE() 
        AND CONSTRAINT_NAME LIKE '%llm_evaluation%'
        """
        
        cursor.execute(check_constraints_query)
        constraints = cursor.fetchall()
        
        logger.info(f"找到 {len(constraints)} 个约束条件:")
        for constraint in constraints:
            logger.info(f"  - {constraint[0]}: {constraint[1]}")
        
        # 找到并删除旧的约束
        constraint_to_drop = None
        for constraint in constraints:
            if 'llm_score' in constraint[1] and '<= 5' in constraint[1]:
                constraint_to_drop = constraint[0]
                break
        
        if constraint_to_drop:
            logger.info(f"删除旧约束: {constraint_to_drop}")
            drop_constraint_query = f"ALTER TABLE llm_evaluation DROP CHECK {constraint_to_drop}"
            cursor.execute(drop_constraint_query)
            conn.commit()
            logger.info("✅ 旧约束已删除")
        else:
            logger.info("未找到需要删除的旧约束（可能已经更新过）")
        
        # 添加新的约束
        logger.info("添加新的约束条件...")
        add_constraint_query = """
        ALTER TABLE llm_evaluation 
        ADD CONSTRAINT chk_llm_score_range 
        CHECK (llm_score >= 0 AND llm_score <= 100)
        """
        
        try:
            cursor.execute(add_constraint_query)
            conn.commit()
            logger.info("✅ 新约束条件已添加")
        except Exception as e:
            if "Duplicate" in str(e) or "already exists" in str(e):
                logger.info("约束条件已存在，跳过添加")
            else:
                raise e
        
        # 验证约束更新
        logger.info("验证约束更新...")
        cursor.execute(check_constraints_query)
        new_constraints = cursor.fetchall()
        
        logger.info(f"更新后的约束条件:")
        for constraint in new_constraints:
            logger.info(f"  - {constraint[0]}: {constraint[1]}")
        
        cursor.close()
        conn.close()
        
        logger.info("🎉 约束条件更新完成!")
        return True
        
    except Exception as e:
        logger.error(f"更新约束条件时发生错误: {e}")
        return False

def test_score_validation():
    """测试新的分数范围验证"""
    try:
        logger.info("测试新的分数范围验证...")
        
        # 测试插入一个有效分数
        test_insert_query = """
        INSERT INTO llm_evaluation 
        (llm_answer, llm_type_id, std_ans_id, llm_score, notes) 
        VALUES 
        ('{"test": "data"}', 1, 1, 85.5, 'Test record')
        """
        
        success, result = execute_query(test_insert_query)
        
        if success:
            logger.info("✅ 百分制分数验证成功")
            
            # 删除测试记录
            delete_test_query = "DELETE FROM llm_evaluation WHERE notes = 'Test record'"
            execute_query(delete_test_query)
            logger.info("测试记录已清理")
            
            return True
        else:
            logger.error(f"❌ 分数验证失败: {result}")
            return False
            
    except Exception as e:
        logger.error(f"测试分数验证时发生错误: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始更新数据库约束条件")
    
    # 1. 更新约束条件
    if not update_llm_evaluation_constraints():
        logger.error("约束条件更新失败")
        return
    
    # 2. 测试新约束（需要先有相关表的数据）
    # test_score_validation()  # 暂时注释掉，因为可能缺少依赖数据
    
    logger.info("数据库约束条件更新完成!")

if __name__ == "__main__":
    main() 
"""
LLM评估模块
用于评估标准问答对的质量，使用LangChain框架
"""

import os
import logging
from typing import List, Dict, Tuple, Optional
from decimal import Decimal
import json
from datetime import datetime

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv

# Local imports
from database import (
    get_connection, execute_query, 
    get_paginated_query
)

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMEvaluator:
    """LLM评估器类"""
    
    def __init__(self):
        """初始化评估器"""
        self.models = {
            "GPT-4": self._init_gpt4,
            "GPT-3.5-Turbo": self._init_gpt35,
            "Claude-3-Opus": self._init_claude_opus,
            "Claude-3-Sonnet": self._init_claude_sonnet
        }
        
        # 评估标准提示模板
        self.evaluation_prompt = PromptTemplate(
            input_variables=["question", "answer", "criteria"],
            template="""
你是一个专业的问答质量评估专家。请评估以下问答对的质量。

【问题】
{question}

【答案】
{answer}

【评估标准】
{criteria}

请从以下5个维度进行评分，每个维度给出0-100分的整数分数：

1. 准确性 (accuracy)：答案是否正确回答了问题
2. 完整性 (completeness)：答案是否完整，涵盖了问题的各个方面  
3. 清晰度 (clarity)：答案表达是否清晰易懂
4. 专业性 (professionalism)：答案是否体现了专业水准
5. 相关性 (relevance)：答案与问题的相关程度

请严格按照以下JSON格式返回结果，不要添加任何其他文字：

{{
    "accuracy": 85,
    "completeness": 90,
    "clarity": 88,
    "professionalism": 87,
    "relevance": 92,
    "total_score": 88.4,
    "reasoning": "详细的评价理由说明..."
}}

注意：total_score是五个维度分数的平均值。请确保JSON格式正确，字段名使用英文。
"""
        )
    
    def _init_gpt4(self) -> ChatOpenAI:
        """初始化GPT-4模型"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY环境变量未设置")
        
        return ChatOpenAI(
            model="gpt-4",
            temperature=0.3,
            openai_api_key=api_key
        )
    
    def _init_gpt35(self) -> ChatOpenAI:
        """初始化GPT-3.5模型"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY环境变量未设置")
        
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            openai_api_key=api_key
        )
    
    def _init_claude_opus(self) -> ChatAnthropic:
        """初始化Claude-3 Opus模型"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY环境变量未设置")
        
        return ChatAnthropic(
            model="claude-3-opus-20240229",
            temperature=0.3,
            anthropic_api_key=api_key
        )
    
    def _init_claude_sonnet(self) -> ChatAnthropic:
        """初始化Claude-3 Sonnet模型"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY环境变量未设置")
        
        return ChatAnthropic(
            model="claude-3-sonnet-20240229",
            temperature=0.3,
            anthropic_api_key=api_key
        )
    
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        return list(self.models.keys())
    
    def init_model(self, model_name: str, temperature: float = 0.3):
        """初始化指定的模型"""
        if model_name not in self.models:
            raise ValueError(f"不支持的模型: {model_name}")
        
        try:
            # 创建模型实例
            model_instance = self.models[model_name]()
            
            # 如果需要自定义温度，重新设置
            if temperature != 0.3:
                model_instance.temperature = temperature
                
            return model_instance
        except Exception as e:
            logger.error(f"初始化模型 {model_name} 失败: {e}")
            raise
    
    def get_standard_pairs(self, tag_filter: Optional[str] = None, 
                          pair_id: Optional[int] = None,
                          limit: Optional[int] = None) -> List[Dict]:
        """获取标准问答对"""
        
        if pair_id:
            # 获取特定的问答对
            query = """
            SELECT 
                sp.pair_id,
                sq.content as question,
                sa.ans_content as answer,
                t.name as tag,
                sq.std_qs_id,
                sa.ans_id
            FROM standard_pair sp
            JOIN standard_QS sq ON sp.std_qs_id = sq.std_qs_id
            JOIN standard_ans sa ON sp.std_ans_id = sa.ans_id
            JOIN tags t ON sq.tag_id = t.tag_id
            WHERE sp.pair_id = %s
            """
            success, result = execute_query(query, (pair_id,), fetch=True)
            
        elif tag_filter:
            # 按标签筛选
            query = """
            SELECT 
                sp.pair_id,
                sq.content as question,
                sa.ans_content as answer,
                t.name as tag,
                sq.std_qs_id,
                sa.ans_id
            FROM standard_pair sp
            JOIN standard_QS sq ON sp.std_qs_id = sq.std_qs_id
            JOIN standard_ans sa ON sp.std_ans_id = sa.ans_id
            JOIN tags t ON sq.tag_id = t.tag_id
            WHERE t.name = %s
            """
            params = (tag_filter,)
            if limit:
                query += " LIMIT %s"
                params = (tag_filter, limit)
            
            success, result = execute_query(query, params, fetch=True)
        else:
            # 获取所有问答对
            query = """
            SELECT 
                sp.pair_id,
                sq.content as question,
                sa.ans_content as answer,
                t.name as tag,
                sq.std_qs_id,
                sa.ans_id
            FROM standard_pair sp
            JOIN standard_QS sq ON sp.std_qs_id = sq.std_qs_id
            JOIN standard_ans sa ON sp.std_ans_id = sa.ans_id
            JOIN tags t ON sq.tag_id = t.tag_id
            """
            if limit:
                query += f" LIMIT {limit}"
            
            success, result = execute_query(query, fetch=True)
        
        if not success:
            logger.error(f"获取标准问答对失败: {result}")
            return []
        
        pairs = []
        for row in result:
            pairs.append({
                'pair_id': row[0],
                'question': row[1],
                'answer': row[2],
                'tag': row[3],
                'std_qs_id': row[4],
                'ans_id': row[5]
            })
        
        return pairs
    
    def evaluate_pair(self, model_name: str, question: str, answer: str, 
                     criteria: str = "标准问答评估", temperature: float = 0.3) -> Dict:
        """评估单个问答对"""
        
        try:
            # 初始化模型
            llm = self.init_model(model_name, temperature)
            
            # 创建评估链
            chain = LLMChain(llm=llm, prompt=self.evaluation_prompt)
            
            # 执行评估
            result = chain.run(
                question=question,
                answer=answer,
                criteria=criteria
            )
            
            logger.info(f"LLM原始输出: {result}")
            
            # 解析结果
            try:
                # 清理和提取JSON部分
                json_str = self._extract_json_from_response(result)
                logger.info(f"提取的JSON字符串: {json_str}")
                
                evaluation = json.loads(json_str)
                logger.info(f"解析后的JSON: {evaluation}")
                
                # 渲染到页面上
                # st.write(json_str)
                
                # 验证和清理字段
                evaluation = self._validate_and_clean_evaluation(evaluation)
                
                return {
                    'success': True,
                    'evaluation': evaluation,
                    'raw_response': result
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                logger.error(f"尝试解析的JSON字符串: '{json_str}'")
                logger.error(f"LLM完整原始输出: {result}")
                
                # 尝试使用正则表达式提取分数
                fallback_evaluation = self._extract_scores_with_regex(result)
                
                return {
                    'success': False,
                    'error': f"JSON解析失败: {e}",
                    'evaluation': fallback_evaluation,
                    'raw_response': result
                }
            
            except Exception as parse_error:
                logger.error(f"解析过程出错: {parse_error}")
                logger.error(f"LLM完整原始输出: {result}")
                
                return {
                    'success': False,
                    'error': f"解析错误: {parse_error}",
                    'evaluation': self._get_default_evaluation(f"解析失败: {parse_error}"),
                    'raw_response': result
                }
                
        except Exception as e:
            logger.error(f"评估过程出错: {e}")
            return {
                'success': False,
                'error': str(e),
                'evaluation': self._get_default_evaluation(f"评估失败: {e}")
            }
    
    def _extract_json_from_response(self, response: str) -> str:
        """从LLM响应中提取JSON字符串"""
        
        # 方法1: 查找```json代码块
        if "```json" in response:
            json_start = response.find("```json") + 7
            json_end = response.find("```", json_start)
            if json_end != -1:
                json_str = response[json_start:json_end].strip()
                return json_str
        
        # 方法2: 查找```代码块（不一定有json标识）
        if "```" in response:
            parts = response.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("{") and part.endswith("}"):
                    return part
        
        # 方法3: 查找JSON对象（从第一个{到最后一个}）
        start_idx = response.find("{")
        end_idx = response.rfind("}")
        
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            json_str = response[start_idx:end_idx + 1]
            return json_str
        
        # 方法4: 如果都没找到，返回原始响应
        return response.strip()
    
    def _validate_and_clean_evaluation(self, evaluation: Dict) -> Dict:
        """验证和清理评估结果"""
        
        required_fields = ['accuracy', 'completeness', 'clarity', 
                          'professionalism', 'relevance', 'total_score']
        
        cleaned_evaluation = {}
        
        # 清理字段名（移除多余的空白字符）
        for key, value in evaluation.items():
            clean_key = key.strip().replace('\n', '').replace('\t', '').replace(' ', '')
            
            # 映射可能的字段名变体
            if clean_key.lower() in ['accuracy', '准确性']:
                cleaned_evaluation['accuracy'] = self._safe_float_convert(value)
            elif clean_key.lower() in ['completeness', '完整性']:
                cleaned_evaluation['completeness'] = self._safe_float_convert(value)
            elif clean_key.lower() in ['clarity', '清晰度']:
                cleaned_evaluation['clarity'] = self._safe_float_convert(value)
            elif clean_key.lower() in ['professionalism', '专业性']:
                cleaned_evaluation['professionalism'] = self._safe_float_convert(value)
            elif clean_key.lower() in ['relevance', '相关性']:
                cleaned_evaluation['relevance'] = self._safe_float_convert(value)
            elif clean_key.lower() in ['total_score', 'totalscore', '总分', '总体分数']:
                cleaned_evaluation['total_score'] = self._safe_float_convert(value)
            elif clean_key.lower() in ['reasoning', '评价理由', '理由']:
                cleaned_evaluation['reasoning'] = str(value)
        
        # 确保所有必要字段都存在
        for field in required_fields:
            if field not in cleaned_evaluation:
                cleaned_evaluation[field] = 0
        
        # 如果没有reasoning字段，添加默认值
        if 'reasoning' not in cleaned_evaluation:
            cleaned_evaluation['reasoning'] = "未提供详细评价理由"
        
        # 计算总分（如果total_score为0或缺失）
        if cleaned_evaluation['total_score'] == 0:
            scores = [cleaned_evaluation[field] for field in required_fields[:-1]]  # 排除total_score
            if any(score > 0 for score in scores):
                cleaned_evaluation['total_score'] = sum(scores) / len(scores)
        
        return cleaned_evaluation
    
    def _safe_float_convert(self, value) -> float:
        """安全地转换值为浮点数"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                # 移除可能的非数字字符
                clean_value = ''.join(c for c in value if c.isdigit() or c == '.')
                return float(clean_value) if clean_value else 0
            else:
                return 0
        except (ValueError, TypeError):
            return 0
    
    def _extract_scores_with_regex(self, response: str) -> Dict:
        """使用正则表达式从响应中提取分数"""
        import re
        
        evaluation = self._get_default_evaluation("正则表达式提取")
        
        # 定义分数提取模式
        patterns = {
            'accuracy': [r'准确性[：:]\s*(\d+)', r'accuracy[：:]\s*(\d+)', r'"accuracy"\s*:\s*(\d+)'],
            'completeness': [r'完整性[：:]\s*(\d+)', r'completeness[：:]\s*(\d+)', r'"completeness"\s*:\s*(\d+)'],
            'clarity': [r'清晰度[：:]\s*(\d+)', r'clarity[：:]\s*(\d+)', r'"clarity"\s*:\s*(\d+)'],
            'professionalism': [r'专业性[：:]\s*(\d+)', r'professionalism[：:]\s*(\d+)', r'"professionalism"\s*:\s*(\d+)'],
            'relevance': [r'相关性[：:]\s*(\d+)', r'relevance[：:]\s*(\d+)', r'"relevance"\s*:\s*(\d+)'],
            'total_score': [r'总分[：:]\s*(\d+\.?\d*)', r'total_score[：:]\s*(\d+\.?\d*)', r'"total_score"\s*:\s*(\d+\.?\d*)']
        }
        
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    try:
                        evaluation[field] = float(match.group(1))
                        break
                    except (ValueError, IndexError):
                        continue
        
        # 如果找到了一些分数但总分为0，计算平均值
        if evaluation['total_score'] == 0:
            scores = [evaluation[field] for field in ['accuracy', 'completeness', 'clarity', 'professionalism', 'relevance']]
            if any(score > 0 for score in scores):
                evaluation['total_score'] = sum(scores) / len(scores)
        
        return evaluation
    
    def _get_default_evaluation(self, reason: str = "未知错误") -> Dict:
        """获取默认的评估结果"""
        return {
            'accuracy': 0,
            'completeness': 0,
            'clarity': 0,
            'professionalism': 0,
            'relevance': 0,
            'total_score': 0,
            'reasoning': reason
        }
    
    def save_evaluation_result(self, pair_id: int, ans_id: int, 
                              model_name: str, evaluation: Dict,
                              llm_answer: str = "") -> bool:
        """保存评估结果到数据库"""
        
        try:
            # 首先获取或创建LLM类型记录
            llm_type_id = self._get_or_create_llm_type(model_name)
            
            # 插入评估记录
            eval_query = """
            INSERT INTO llm_evaluation 
            (llm_answer, llm_type_id, std_ans_id, llm_score)
            VALUES (%s, %s, %s, %s)
            """
            
            success, result = execute_query(
                eval_query,
                (llm_answer, llm_type_id, ans_id, 
                 Decimal(str(evaluation['total_score'])))
            )
            
            if success:
                logger.info(f"评估结果已保存 - Pair ID: {pair_id}, 分数: {evaluation['total_score']}")
                return True
            else:
                logger.error(f"保存评估结果失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"保存评估结果出错: {e}")
            return False
    
    def _get_or_create_llm_type(self, model_name: str) -> int:
        """获取或创建LLM类型记录"""
        
        # 模型参数和成本配置
        model_configs = {
            "gpt-4": {"params": 1000000000000, "cost": 30.0},  # 1T参数，$30/1M tokens
            "gpt-3.5-turbo": {"params": 175000000000, "cost": 0.5},  # 175B参数，$0.5/1M tokens
            "claude-3-opus": {"params": 500000000000, "cost": 15.0},  # 估计500B参数，$15/1M tokens
            "claude-3-sonnet": {"params": 200000000000, "cost": 3.0}  # 估计200B参数，$3/1M tokens
        }
        
        config = model_configs.get(model_name, {"params": 0, "cost": 0.0})
        
        # 检查是否已存在
        check_query = "SELECT llm_type_id FROM llm_type WHERE name = %s"
        success, result = execute_query(check_query, (model_name,), fetch=True)
        
        if success and result:
            return result[0][0]
        
        # 创建新记录
        insert_query = """
        INSERT INTO llm_type (name, params, costs_per_million_token)
        VALUES (%s, %s, %s)
        """
        
        success, result = execute_query(
            insert_query,
            (model_name, config["params"], Decimal(str(config["cost"])))
        )
        
        if success:
            # 获取新插入的ID
            get_id_query = "SELECT LAST_INSERT_ID()"
            success, result = execute_query(get_id_query, fetch=True)
            if success and result:
                return result[0][0]
        
        raise Exception(f"无法创建LLM类型记录: {model_name}")
    
    def batch_evaluate(self, model_name: str, 
                      tag_filter: Optional[str] = None,
                      pair_id: Optional[int] = None,
                      limit: Optional[int] = None,
                      criteria: str = "标准问答评估",
                      temperature: float = 0.3) -> Dict:
        """批量评估标准问答对"""
        
        logger.info(f"开始批量评估 - 模型: {model_name}, 温度: {temperature}")
        
        # 获取问答对
        pairs = self.get_standard_pairs(tag_filter, pair_id, limit)
        
        if not pairs:
            return {
                'success': False,
                'message': '没有找到需要评估的问答对',
                'results': []
            }
        
        results = []
        success_count = 0
        fail_count = 0
        
        for i, pair in enumerate(pairs):
            logger.info(f"评估进度: {i+1}/{len(pairs)} - Pair ID: {pair['pair_id']}")
            
            try:
                # 评估问答对
                eval_result = self.evaluate_pair(
                    model_name, 
                    pair['question'], 
                    pair['answer'], 
                    criteria,
                    temperature
                )
                
                if eval_result['success']:
                    # 保存评估结果
                    save_success = self.save_evaluation_result(
                        pair['pair_id'],
                        pair['ans_id'],
                        model_name,
                        eval_result['evaluation'],
                        eval_result.get('raw_response', '')
                    )
                    
                    if save_success:
                        success_count += 1
                    else:
                        fail_count += 1
                else:
                    fail_count += 1
                
                results.append({
                    'pair_id': pair['pair_id'],
                    'question': pair['question'][:100] + '...' if len(pair['question']) > 100 else pair['question'],
                    'score': eval_result['evaluation']['total_score'],
                    'answer': pair['answer'],
                    'success': eval_result['success'],
                    'error': eval_result.get('error', '')
                })
                
            except Exception as e:
                logger.error(f"评估Pair ID {pair['pair_id']}时出错: {e}")
                fail_count += 1
                
                results.append({
                    'pair_id': pair['pair_id'],
                    'question': pair['question'][:100] + '...' if len(pair['question']) > 100 else pair['question'],
                    'score': 0,
                    'success': False,
                    'error': str(e)
                })
        
        logger.info(f"批量评估完成 - 成功: {success_count}, 失败: {fail_count}")
        
        return {
            'success': True,
            'message': f'评估完成 - 成功: {success_count}, 失败: {fail_count}',
            'total_pairs': len(pairs),
            'success_count': success_count,
            'fail_count': fail_count,
            'results': results
        }
    
    def get_evaluation_statistics(self, model_name: Optional[str] = None) -> Dict:
        """获取评估统计信息"""
        
        base_query = """
        SELECT 
            lt.name as model_name,
            COUNT(*) as total_evaluations,
            AVG(le.llm_score) as avg_score,
            MIN(le.llm_score) as min_score,
            MAX(le.llm_score) as max_score,
            STDDEV(le.llm_score) as score_stddev
        FROM llm_evaluation le
        JOIN llm_type lt ON le.llm_type_id = lt.llm_type_id
        """
        
        if model_name:
            base_query += " WHERE lt.name = %s"
            params = (model_name,)
        else:
            params = None
        
        base_query += " GROUP BY lt.name ORDER BY avg_score DESC"
        
        success, result = execute_query(base_query, params, fetch=True)
        
        if not success:
            return {'success': False, 'error': result}
        
        stats = []
        for row in result:
            stats.append({
                'model_name': row[0],
                'total_evaluations': row[1],
                'avg_score': float(row[2]) if row[2] else 0,
                'min_score': float(row[3]) if row[3] else 0,
                'max_score': float(row[4]) if row[4] else 0,
                'score_stddev': float(row[5]) if row[5] else 0
            })
        
        return {
            'success': True,
            'statistics': stats
        }


# 创建全局评估器实例
evaluator = LLMEvaluator()


def evaluate_standard_pairs(model_name: str, 
                           tag_filter: Optional[str] = None,
                           pair_id: Optional[int] = None,
                           limit: Optional[int] = None,
                           criteria: str = "标准问答评估",
                           temperature: float = 0.3) -> Dict:
    """评估标准问答对的便捷函数"""
    return evaluator.batch_evaluate(model_name, tag_filter, pair_id, limit, criteria, temperature)


def get_model_statistics(model_name: Optional[str] = None) -> Dict:
    """获取模型评估统计的便捷函数"""
    return evaluator.get_evaluation_statistics(model_name)


if __name__ == "__main__":
    # 测试代码
    print("LLM评估器测试")
    
    # 获取可用模型
    models = evaluator.get_available_models()
    print(f"可用模型: {models}")
    
    # 获取标准问答对
    pairs = evaluator.get_standard_pairs(limit=1)
    if pairs:
        print(f"测试问答对: {pairs[0]['question'][:50]}...")
    else:
        print("没有找到标准问答对") 
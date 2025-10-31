"""Error Analyzer - Uses LLM to analyze test failures"""

import json
import re
from typing import Dict, Any
from ..core.interfaces import IAnalyzer


class ErrorAnalyzer(IAnalyzer):
    """错误分析器 - 使用 LLM 分析测试失败的根本原因"""

    def __init__(self, llm_client):
        """初始化分析器

        Args:
            llm_client: 具有 chat() 方法的 LLM 客户端
        """
        self.llm_client = llm_client

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析测试失败

        Args:
            data: 测试结果，包含 'output' 和 'errors'

        Returns:
            分析结果 {
                'error_type': str,
                'location': str,
                'root_cause': str,
                'fix_suggestions': List[str]
            }
        """
        error_output = data.get('output', '')
        errors = data.get('errors', [])

        # 构建分析提示
        prompt = f"""
作为专业的 QA 工程师，分析以下测试失败的根本原因：

测试输出：
{error_output[:2000]}  # 限制长度

错误信息：
{errors[:5] if errors else '无'}

请提供详细分析（JSON 格式）：
{{
  "error_type": "语法错误/导入错误/逻辑错误/配置错误",
  "location": "file:line",
  "root_cause": "详细原因说明",
  "fix_suggestions": ["具体建议1", "具体建议2"],
  "priority": "high/medium/low"
}}
"""

        try:
            response = await self.llm_client.chat(prompt)

            # 尝试解析 JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())

        except Exception as e:
            # 分析失败时返回原始信息
            pass

        # 降级：返回基本分析
        return {
            'error_type': 'unknown',
            'root_cause': error_output[:500],
            'fix_suggestions': ['检查测试输出中的错误信息', '确认代码语法正确'],
            'raw_output': error_output
        }
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
                'fix_suggestions': List[str],
                'code_snippet': str
            }
        """
        error_output = data.get('output', '')
        errors = data.get('errors', [])

        # 提取关键错误信息
        error_summary = self._extract_error_summary(error_output)

        # 构建更详细的分析提示
        prompt = f"""
你是一个专业的 QA 工程师和调试专家。请详细分析以下测试失败的根本原因：

完整测试输出：
{error_output[:3000]}

关键错误信息：
{error_summary}

错误列表：
{json.dumps(errors[:5], ensure_ascii=False) if errors else '无'}

请提供非常详细的分析，帮助开发者快速定位并修复问题。输出 JSON 格式：

{{
  "error_type": "语法错误/导入错误/逻辑错误/断言错误/配置错误/运行时错误",
  "location": "具体文件名:行号（如果能确定）",
  "root_cause": "详细分析错误的根本原因，包括为什么会出现这个错误",
  "immediate_cause": "直接导致错误的代码或配置",
  "fix_suggestions": [
    "具体修复建议1（越详细越好，包括代码示例）",
    "具体修复建议2",
    "具体修复建议3"
  ],
  "code_snippet": "如果能确定，提供有问题的代码片段",
  "priority": "high/medium/low",
  "similar_issues": "类似问题的常见原因（可选）"
}}

重要：
1. 分析要具体、可操作，避免泛泛而谈
2. 如果是导入错误，说明缺少什么模块或路径问题
3. 如果是语法错误，指出具体的语法问题
4. 如果是逻辑错误，分析预期行为和实际行为的差异
5. fix_suggestions 要给出可以直接使用的代码修改建议
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
            'root_cause': error_summary or error_output[:500],
            'fix_suggestions': [
                '检查测试输出中的错误信息',
                '确认代码语法正确',
                '验证导入路径是否正确',
                '检查测试断言是否符合预期'
            ],
            'raw_output': error_output,
            'immediate_cause': 'Unable to parse error details'
        }

    def _extract_error_summary(self, output: str) -> str:
        """从输出中提取关键错误摘要"""
        import re

        summaries = []

        # 提取 Python 异常
        exception_pattern = r'((\w+Error|Exception): .+)'
        exceptions = re.findall(exception_pattern, output)
        if exceptions:
            summaries.extend([exc[0] for exc in exceptions[:3]])

        # 提取 FAILED 行
        failed_pattern = r'(FAILED .+)'
        failed_tests = re.findall(failed_pattern, output)
        if failed_tests:
            summaries.extend(failed_tests[:3])

        # 提取 ERROR 行
        error_pattern = r'(ERROR .+)'
        error_lines = re.findall(error_pattern, output)
        if error_lines:
            summaries.extend(error_lines[:3])

        # 提取 AssertionError
        assertion_pattern = r'(AssertionError.*)'
        assertions = re.findall(assertion_pattern, output)
        if assertions:
            summaries.extend(assertions[:2])

        return '\n'.join(summaries) if summaries else ''
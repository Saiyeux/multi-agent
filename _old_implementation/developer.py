"""Developer Agent - Code implementation and testing"""

import re
from typing import Dict, Any
from .base_agent import BaseAgent
from ..llm.prompts import DEVELOPER_SYSTEM_PROMPT


class DeveloperAgent(BaseAgent):
    """全栈开发者 - 代码实现与测试"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("Developer", config, DEVELOPER_SYSTEM_PROMPT)

    async def implement(self, architecture_doc: str) -> Dict[str, str]:
        """根据架构文档实现代码

        Args:
            architecture_doc: 架构设计文档

        Returns:
            字典 {filename: code_content}
        """
        prompt = f"""
根据以下架构设计，生成完整的可运行代码：

{architecture_doc}

要求：
1. 代码必须完整、可运行
2. 包含必要的注释和文档字符串
3. 遵循PEP 8编码规范（Python）或相应语言的规范
4. 使用清晰的变量和函数命名

请按以下格式输出（每个文件用分隔符标记）：

=== FILE: filename.py ===
```python
# 代码内容
```

=== FILE: another_file.py ===
```python
# 代码内容
```
"""
        response = await self.chat(prompt)
        return self._parse_code_files(response)

    async def write_tests(self, code_files: Dict[str, str]) -> Dict[str, str]:
        """为代码编写测试

        Args:
            code_files: 代码文件字典

        Returns:
            测试文件字典 {test_filename: test_code}
        """
        # 将代码文件汇总
        code_summary = "\n\n".join([
            f"=== {filename} ===\n{content}"
            for filename, content in code_files.items()
        ])

        prompt = f"""
为以下代码编写完整的单元测试：

{code_summary}

要求：
1. 使用pytest框架
2. 测试覆盖主要功能和边界条件
3. 测试函数命名清晰（test_xxx）
4. 包含必要的fixture和mock

请按以下格式输出：

=== FILE: test_xxx.py ===
```python
# 测试代码
```
"""
        response = await self.chat(prompt)
        return self._parse_code_files(response)

    async def fix_issues(self, error_report: Dict[str, Any]) -> Dict[str, str]:
        """根据错误报告修复代码问题

        Args:
            error_report: 错误报告，包含errors列表

        Returns:
            修复后的代码文件字典
        """
        errors = error_report.get('errors', [])
        error_summary = "\n".join([
            f"- {err.get('file', 'unknown')}: {err.get('message', 'unknown error')}"
            for err in errors
        ])

        prompt = f"""
以下测试失败，请修复代码问题：

错误列表：
{error_summary}

详细错误信息：
{error_report}

请分析错误原因，并输出修复后的完整代码文件。

输出格式：
=== FILE: filename.py ===
```python
# 修复后的代码
```
"""
        response = await self.chat(prompt)
        return self._parse_code_files(response)

    def _parse_code_files(self, response: str) -> Dict[str, str]:
        """解析LLM响应中的代码文件

        Args:
            response: LLM响应文本

        Returns:
            {filename: code_content}
        """
        files = {}
        # 匹配 === FILE: xxx === 格式
        pattern = r'===\s*FILE:\s*([^\s=]+)\s*===\s*```(?:\w+)?\s*\n(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)

        for filename, code in matches:
            files[filename.strip()] = code.strip()

        # 如果没有匹配到文件分隔符，尝试提取单个代码块
        if not files:
            code_block_pattern = r'```(?:\w+)?\s*\n(.*?)```'
            code_matches = re.findall(code_block_pattern, response, re.DOTALL)
            if code_matches:
                # 默认文件名为main.py
                files['main.py'] = code_matches[0].strip()

        return files

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理开发任务

        Args:
            input_data: {'architecture_doc': str, 'fix_errors': dict (optional)}

        Returns:
            {'code_files': dict, 'test_files': dict}
        """
        architecture_doc = input_data.get('architecture_doc')
        fix_errors = input_data.get('fix_errors')

        if fix_errors:
            # 修复模式
            code_files = await self.fix_issues(fix_errors)
            return {'code_files': code_files}
        else:
            # 开发模式
            if not architecture_doc:
                raise ValueError("Missing 'architecture_doc' in input_data")

            code_files = await self.implement(architecture_doc)
            test_files = await self.write_tests(code_files)

            return {
                'code_files': code_files,
                'test_files': test_files
            }
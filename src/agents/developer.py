"""Developer Agent - Code implementation and testing (Refactored)"""

import re
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from .base_agent import BaseAgent
from ..llm.prompts import DEVELOPER_SYSTEM_PROMPT


class DeveloperAgent(BaseAgent):
    """全栈开发者 - 代码实现与测试

    支持的 actions:
    - implement: 实现代码
    - write_tests: 编写测试
    - fix_issues: 修复问题
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__("developer", config, DEVELOPER_SYSTEM_PROMPT)

    def _get_action_handler(self, action: str) -> Optional[Callable]:
        """获取动作处理器"""
        handlers = {
            'implement': self._handle_implement,
            'write_tests': self._handle_write_tests,
            'fix_issues': self._handle_fix_issues
        }
        return handlers.get(action)

    async def _handle_implement(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理代码实现"""
        architecture_doc = input_data.get('architecture_doc')
        if not architecture_doc:
            raise ValueError("Missing 'architecture_doc' in input_data")

        code_files = await self._implement(architecture_doc)
        return {'code_files': code_files}

    async def _handle_write_tests(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理测试编写"""
        code_files = input_data.get('code_files')
        if not code_files:
            raise ValueError("Missing 'code_files' in input_data")

        test_files = await self._write_tests(code_files)
        return {'test_files': test_files}

    async def _handle_fix_issues(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理问题修复"""
        test_result = input_data.get('test_result')
        analysis = input_data.get('analysis', {})

        if not test_result:
            raise ValueError("Missing 'test_result' in input_data")

        fixed_files = await self._fix_issues(test_result, analysis)
        return {'fixed_files': fixed_files}

    async def _implement(self, architecture_doc: str) -> Dict[str, str]:
        """实现代码"""
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

    async def _write_tests(self, code_files: Dict[str, str]) -> Dict[str, str]:
        """编写测试"""
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
5. 不要在测试代码中使用非ASCII字符的bytes字面量（如 b"中文"）
6. **重要**：测试文件需要导入被测试的模块，使用以下导入方式：
   - 在测试文件开头添加路径设置：
     ```python
     import sys
     from pathlib import Path
     sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))
     ```
   - 然后直接导入需要测试的模块（**不要**添加 `main.` 或其他包前缀）
   - 例如：如果要测试 `calculate.py` 中的 `add` 函数，使用：
     ```python
     from calculate import add
     ```
     而**不是** `from main.calculate import add`
7. 文件名必须以 test_ 开头，例如：test_calculator.py
8. **不要**在文件名前加目录前缀（如 tests/），只写文件名

请按以下格式输出：

=== FILE: test_xxx.py ===
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

# 你的测试代码
```
"""
        response = await self.chat(prompt)
        return self._parse_code_files(response)

    async def _fix_issues(self, test_result: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, str]:
        """修复问题"""
        error_output = test_result.get('output', '')

        # 构建详细的错误描述
        error_desc = f"""
测试输出：
{error_output}

分析结果：
{analysis if analysis else '无详细分析'}
"""

        prompt = f"""
以下测试失败，请修复代码问题：

{error_desc}

重要提示：
1. 如果需要修复测试文件，必须在测试文件开头添加路径设置：
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))
```

2. 导入模块时，直接使用模块名（**不要**添加 `main.` 或其他包前缀）
   例如：`from calculate import add` 而**不是** `from main.calculate import add`

3. 不要在文件名前加目录前缀（如 tests/），只写文件名

请提供修复后的完整代码文件。

输出格式：
=== FILE: filename.py ===
```python
# 修复后的代码
```
"""
        response = await self.chat(prompt)
        return self._parse_code_files(response)

    def _parse_code_files(self, response: str) -> Dict[str, str]:
        """解析LLM响应中的代码文件"""
        files = {}
        # 匹配 === FILE: xxx === 格式
        pattern = r'===\s*FILE:\s*([^\s=]+)\s*===\s*```(?:\w+)?\s*\n(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)

        for filename, code in matches:
            # 清理文件名：移除目录前缀，只保留文件名
            # 例如：tests/test_add.py -> test_add.py
            clean_filename = Path(filename.strip()).name
            files[clean_filename] = code.strip()

        # 如果没有匹配到文件分隔符，尝试提取单个代码块
        if not files:
            code_block_pattern = r'```(?:\w+)?\s*\n(.*?)```'
            code_matches = re.findall(code_block_pattern, response, re.DOTALL)
            if code_matches:
                # 默认文件名为main.py
                files['main.py'] = code_matches[0].strip()

        return files
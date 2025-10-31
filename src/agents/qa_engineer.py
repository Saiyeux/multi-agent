"""QA Engineer Agent - Testing and quality assurance (Refactored)"""

import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from .base_agent import BaseAgent
from ..llm.prompts import QA_SYSTEM_PROMPT


class QAAgent(BaseAgent):
    """质量保障工程师 - 测试与发布

    支持的 actions:
    - run_tests: 运行测试
    - review_code: 代码审查
    - package_release: 打包发布
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__("qa", config, QA_SYSTEM_PROMPT)

    def _get_action_handler(self, action: str) -> Optional[Callable]:
        """获取动作处理器"""
        handlers = {
            'run_tests': self._handle_run_tests,
            'review_code': self._handle_review_code,
            'package_release': self._handle_package_release
        }
        return handlers.get(action)

    async def _handle_run_tests(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理测试运行"""
        code_dir = input_data.get('code_dir')
        test_dir = input_data.get('test_dir')

        if not code_dir or not test_dir:
            raise ValueError("Missing 'code_dir' or 'test_dir' in input_data")

        return await self._run_tests(Path(code_dir), Path(test_dir))

    async def _handle_review_code(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理代码审查"""
        code_files = input_data.get('code_files')
        if not code_files:
            raise ValueError("Missing 'code_files' in input_data")

        return await self._review_code(code_files)

    async def _handle_package_release(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理打包发布"""
        code_dir = input_data.get('code_dir')
        if not code_dir:
            raise ValueError("Missing 'code_dir' in input_data")

        package_path = await self._package_release(Path(code_dir))
        return {'package_path': package_path}

    async def _run_tests(self, code_dir: Path, test_dir: Path) -> Dict[str, Any]:
        """运行测试"""
        try:
            # 计算相对于 workspace 的相对路径
            workspace = code_dir.parent
            test_dir_rel = test_dir.relative_to(workspace)

            # 使用pytest运行测试，使用相对路径避免路径拼接问题
            result = subprocess.run(
                ['pytest', str(test_dir_rel), '-v', '--tb=short'],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=60
            )

            output = result.stdout + result.stderr

            # 解析pytest输出
            passed = result.returncode == 0
            total, failed = self._parse_pytest_output(output)

            return {
                'passed': passed,
                'total': total,
                'failed': failed,
                'output': output,
                'errors': self._extract_errors_from_output(output) if not passed else []
            }

        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'total': 0,
                'failed': 0,
                'output': 'Test execution timeout',
                'errors': [{'message': 'Test execution timeout'}]
            }
        except Exception as e:
            return {
                'passed': False,
                'total': 0,
                'failed': 0,
                'output': str(e),
                'errors': [{'message': str(e)}]
            }

    def _parse_pytest_output(self, output: str) -> tuple[int, int]:
        """解析pytest输出，提取测试统计"""
        import re

        # 尝试从输出中提取统计信息
        passed_match = re.search(r'(\d+) passed', output)
        failed_match = re.search(r'(\d+) failed', output)
        error_match = re.search(r'(\d+) error', output)

        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        errors = int(error_match.group(1)) if error_match else 0

        total = passed + failed + errors
        return total, failed + errors

    def _extract_errors_from_output(self, output: str) -> List[Dict[str, str]]:
        """从pytest输出中提取错误信息"""
        errors = []

        # 简单提取：将输出分段
        lines = output.split('\n')
        current_error = {}

        for line in lines:
            # 检测错误标记
            if 'ERROR' in line or 'FAILED' in line or 'SyntaxError' in line:
                if current_error:
                    errors.append(current_error)
                current_error = {'message': line}
            elif current_error and line.strip():
                # 继续收集错误信息
                current_error['message'] += '\n' + line

        if current_error:
            errors.append(current_error)

        # 如果没有提取到具体错误，返回完整输出
        if not errors:
            errors = [{'message': output}]

        return errors

    async def _review_code(self, code_files: Dict[str, str]) -> Dict[str, Any]:
        """代码审查"""
        code_summary = "\n\n".join([
            f"=== {filename} ===\n{content}"
            for filename, content in code_files.items()
        ])

        prompt = f"""
请对以下代码进行审查，关注：

1. 代码质量和可读性
2. 潜在的bug和安全问题
3. 性能优化建议
4. 最佳实践遵循情况

代码：
{code_summary}

请输出JSON格式的审查报告：
{{
  "overall_score": 0-100,
  "issues": [
    {{"file": "xx.py", "line": 10, "severity": "high/medium/low", "message": "问题描述"}}
  ],
  "suggestions": ["建议1", "建议2"]
}}
"""
        response = await self.chat(prompt)

        try:
            # 尝试解析JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass

        # 如果解析失败，返回原始响应
        return {'raw_review': response}

    async def _package_release(self, code_dir: Path) -> str:
        """打包发布"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        release_name = f"release_{timestamp}"

        # 创建发布目录
        release_dir = code_dir.parent / 'releases' / release_name
        release_dir.mkdir(parents=True, exist_ok=True)

        # 复制代码文件（递归）
        for item in code_dir.rglob('*'):
            if item.is_file():
                rel_path = item.relative_to(code_dir)
                dest = release_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)

        # 打包为zip
        archive_path = code_dir.parent / 'releases' / f"{release_name}.zip"
        shutil.make_archive(
            str(archive_path.with_suffix('')),
            'zip',
            release_dir
        )

        return str(archive_path)
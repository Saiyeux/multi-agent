"""QA Engineer Agent - Testing and quality assurance"""

import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List
from .base_agent import BaseAgent
from ..llm.prompts import QA_SYSTEM_PROMPT


class QAAgent(BaseAgent):
    """质量保障工程师 - 测试与发布"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("QA", config, QA_SYSTEM_PROMPT)

    async def run_tests(self, code_dir: Path, test_dir: Path) -> Dict[str, Any]:
        """运行测试用例

        Args:
            code_dir: 代码目录
            test_dir: 测试目录

        Returns:
            测试结果 {'passed': bool, 'total': int, 'failed': int, 'errors': list}
        """
        try:
            # 使用pytest运行测试
            result = subprocess.run(
                ['pytest', str(test_dir), '-v', '--tb=short', '--json-report', '--json-report-file=/tmp/pytest_report.json'],
                cwd=code_dir.parent,
                capture_output=True,
                text=True,
                timeout=60
            )

            # 尝试读取JSON报告
            report_file = Path('/tmp/pytest_report.json')
            if report_file.exists():
                with open(report_file, 'r') as f:
                    report = json.load(f)

                return {
                    'passed': report.get('exitcode') == 0,
                    'total': report['summary']['total'],
                    'failed': report['summary'].get('failed', 0),
                    'errors': self._extract_errors(report),
                    'output': result.stdout
                }
            else:
                # 降级到简单解析
                return self._parse_pytest_output(result)

        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'total': 0,
                'failed': 0,
                'errors': [{'message': 'Test execution timeout'}],
                'output': ''
            }
        except Exception as e:
            return {
                'passed': False,
                'total': 0,
                'failed': 0,
                'errors': [{'message': str(e)}],
                'output': ''
            }

    def _extract_errors(self, report: Dict) -> List[Dict[str, str]]:
        """从pytest报告中提取错误信息"""
        errors = []
        for test in report.get('tests', []):
            if test.get('outcome') in ['failed', 'error']:
                errors.append({
                    'file': test.get('nodeid', ''),
                    'message': test.get('call', {}).get('longrepr', 'Unknown error')
                })
        return errors

    def _parse_pytest_output(self, result: subprocess.CompletedProcess) -> Dict[str, Any]:
        """简单解析pytest输出"""
        output = result.stdout + result.stderr
        passed = result.returncode == 0

        # 尝试从输出中提取统计信息
        import re
        match = re.search(r'(\d+) passed', output)
        total = int(match.group(1)) if match else 0

        match = re.search(r'(\d+) failed', output)
        failed = int(match.group(1)) if match else 0

        return {
            'passed': passed,
            'total': total + failed,
            'failed': failed,
            'errors': [{'message': output}] if not passed else [],
            'output': output
        }

    async def review_code(self, code_files: Dict[str, str]) -> Dict[str, Any]:
        """代码审查

        Args:
            code_files: 代码文件字典

        Returns:
            审查报告
        """
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

    async def package_release(self, code_dir: Path) -> str:
        """打包发布

        Args:
            code_dir: 代码目录

        Returns:
            打包文件路径
        """
        import shutil
        from datetime import datetime

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        release_name = f"release_{timestamp}"

        # 创建发布目录
        release_dir = code_dir.parent / 'releases' / release_name
        release_dir.mkdir(parents=True, exist_ok=True)

        # 复制代码文件
        for item in code_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, release_dir / item.name)

        # 打包为zip
        archive_path = code_dir.parent / 'releases' / f"{release_name}.zip"
        shutil.make_archive(
            str(archive_path.with_suffix('')),
            'zip',
            release_dir
        )

        return str(archive_path)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理QA任务

        Args:
            input_data: {
                'action': 'test' | 'review' | 'package',
                'code_dir': Path,
                'test_dir': Path (for test),
                'code_files': dict (for review)
            }

        Returns:
            处理结果
        """
        action = input_data.get('action', 'test')

        if action == 'test':
            code_dir = input_data.get('code_dir')
            test_dir = input_data.get('test_dir')
            return await self.run_tests(code_dir, test_dir)

        elif action == 'review':
            code_files = input_data.get('code_files', {})
            return await self.review_code(code_files)

        elif action == 'package':
            code_dir = input_data.get('code_dir')
            package_path = await self.package_release(code_dir)
            return {'package_path': package_path}

        else:
            raise ValueError(f"Unknown action: {action}")
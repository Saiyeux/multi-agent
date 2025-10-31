"""Coding Stage"""

import re
from ..core.interfaces import IStage, StageResult, StageStatus, WorkflowContext


class CodingStage(IStage):
    """代码实现阶段"""

    @property
    def name(self) -> str:
        return "coding"

    def _ensure_syspath_in_test(self, content: str) -> str:
        """确保测试文件中包含 sys.path 设置"""
        # 检查是否已经有 sys.path.insert
        if 'sys.path.insert' in content:
            return content

        # sys.path 设置代码
        syspath_code = '''import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

'''

        # 找到第一个 import 语句的位置
        lines = content.split('\n')
        insert_index = 0

        # 跳过开头的注释和空行
        for i, line in enumerate(lines):
            stripped = line.strip()
            # 跳过注释、空行、编码声明
            if not stripped or stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''") or 'coding' in stripped:
                continue
            # 找到第一个非注释行
            insert_index = i
            break

        # 在第一个非注释行之前插入 sys.path 设置
        lines.insert(insert_index, syspath_code.rstrip())

        return '\n'.join(lines)

    async def execute(self, context: WorkflowContext) -> StageResult:
        """执行代码实现"""
        developer = context.get_agent('developer')
        if not developer:
            return StageResult(
                status=StageStatus.FAILED,
                error="Developer agent not found"
            )

        # 获取架构文档
        design_result = context.get('architecture_design_result')
        if not design_result or design_result.status != StageStatus.SUCCESS:
            return StageResult(
                status=StageStatus.FAILED,
                error="Architecture design not completed"
            )

        architecture_doc = design_result.output.get('document')

        try:
            # 实现代码
            code_result = await developer.process({
                'action': 'implement',
                'architecture_doc': architecture_doc
            })

            code_files = code_result['code_files']

            # 保存代码文件（过滤掉测试文件，测试文件应该在 write_tests 阶段生成）
            for filename, content in code_files.items():
                # 跳过测试文件
                if filename.startswith('test_') or filename.endswith('_test.py'):
                    continue
                context.memory.save('code', filename, content)

            # 编写测试
            test_result = await developer.process({
                'action': 'write_tests',
                'code_files': code_files
            })

            test_files = test_result['test_files']

            # 保存测试文件（确保测试文件不会被误存到其他目录）
            for filename, content in test_files.items():
                # 自动添加 sys.path 设置（如果测试文件中还没有）
                content = self._ensure_syspath_in_test(content)
                # 测试文件始终保存到tests目录，无论文件名是否符合规范
                context.memory.save('tests', filename, content)

            return StageResult(
                status=StageStatus.SUCCESS,
                output={
                    'code_files': code_files,
                    'test_files': test_files
                }
            )

        except Exception as e:
            return StageResult(
                status=StageStatus.FAILED,
                error=str(e)
            )
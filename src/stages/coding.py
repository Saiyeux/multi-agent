"""Coding Stage"""

from ..core.interfaces import IStage, StageResult, StageStatus, WorkflowContext


class CodingStage(IStage):
    """代码实现阶段"""

    @property
    def name(self) -> str:
        return "coding"

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

            # 保存代码文件
            for filename, content in code_files.items():
                context.memory.save('code', filename, content)

            # 编写测试
            test_result = await developer.process({
                'action': 'write_tests',
                'code_files': code_files
            })

            test_files = test_result['test_files']

            # 保存测试文件
            for filename, content in test_files.items():
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
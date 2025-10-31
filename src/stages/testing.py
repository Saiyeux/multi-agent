"""Testing Stage - with retry and analysis"""

from typing import Optional
from ..core.interfaces import IStage, StageResult, StageStatus, WorkflowContext, IAnalyzer


class TestingStage(IStage):
    """测试阶段 - 支持迭代重试和错误分析"""

    def __init__(self, analyzer: Optional[IAnalyzer] = None, max_retries: int = 3):
        """初始化测试阶段

        Args:
            analyzer: 错误分析器（可选）
            max_retries: 最大重试次数
        """
        self.analyzer = analyzer
        self.max_retries = max_retries

    @property
    def name(self) -> str:
        return "testing"

    async def execute(self, context: WorkflowContext) -> StageResult:
        """执行测试，失败时自动重试"""
        qa_agent = context.get_agent('qa')
        dev_agent = context.get_agent('developer')

        if not qa_agent or not dev_agent:
            return StageResult(
                status=StageStatus.FAILED,
                error="QA or Developer agent not found"
            )

        # 检查是否有代码和测试
        code_result = context.get('coding_result')
        if not code_result or code_result.status != StageStatus.SUCCESS:
            return StageResult(
                status=StageStatus.FAILED,
                error="Coding stage not completed"
            )

        # 开始测试循环
        retries = 0
        while retries < self.max_retries:
            try:
                # 运行测试
                test_result = await qa_agent.process({
                    'action': 'run_tests',
                    'code_dir': context.memory.workspace / 'code',
                    'test_dir': context.memory.workspace / 'tests'
                })

                # 测试通过
                if test_result['passed']:
                    return StageResult(
                        status=StageStatus.SUCCESS,
                        output=test_result,
                        metadata={'iterations': retries + 1}
                    )

                # 测试失败 - 分析原因
                analysis = {}
                if self.analyzer:
                    analysis = await self.analyzer.analyze(test_result)

                # 保存分析结果到上下文
                context.set('last_test_analysis', analysis)

                # 让开发者修复
                fix_result = await dev_agent.process({
                    'action': 'fix_issues',
                    'test_result': test_result,
                    'analysis': analysis
                })

                # 保存修复后的代码
                fixed_files = fix_result.get('fixed_files', {})
                for filename, content in fixed_files.items():
                    context.memory.save('code', filename, content)

                retries += 1
                context.iteration = retries

            except Exception as e:
                return StageResult(
                    status=StageStatus.FAILED,
                    error=f"Testing error: {str(e)}",
                    metadata={'iterations': retries + 1}
                )

        # 超过重试次数
        return StageResult(
            status=StageStatus.FAILED,
            error=f"Tests failed after {self.max_retries} retries",
            output=test_result if 'test_result' in locals() else {},
            metadata={'iterations': retries}
        )
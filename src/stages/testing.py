"""Testing Stage - with retry and analysis"""

import json
from datetime import datetime
from typing import Optional
from ..core.interfaces import IStage, StageResult, StageStatus, WorkflowContext, IAnalyzer


class TestingStage(IStage):
    """测试阶段 - 支持迭代重试和错误分析

    支持 Debug 模式：从 context 中读取配置，实现无限迭代
    """

    def __init__(self, analyzer: Optional[IAnalyzer] = None, max_retries: int = 3):
        """初始化测试阶段

        Args:
            analyzer: 错误分析器（可选）
            max_retries: 默认最大重试次数（debug 模式会被覆盖）
        """
        self.analyzer = analyzer
        self.default_max_retries = max_retries

    @property
    def name(self) -> str:
        return "testing"

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

        # 读取配置：支持 Debug 模式（无限迭代）
        debug_mode = context.config.get('debug', {}).get('enabled', False)
        max_retries = float('inf') if debug_mode else self.default_max_retries

        print(f"\n{'='*60}")
        if debug_mode:
            print("🐛 Debug Mode: Unlimited iterations")
        else:
            print(f"🔄 Max iterations: {max_retries}")
        print(f"{'='*60}\n")

        # 开始测试循环
        retries = 0
        iteration_history = []  # 记录每次迭代的详细信息

        while retries < max_retries:
            print(f"\n{'─'*60}")
            print(f"🔄 Iteration {retries + 1}")
            print(f"{'─'*60}\n")

            try:
                # 运行测试
                print(f"[QA] Running tests...")
                test_result = await qa_agent.process({
                    'action': 'run_tests',
                    'code_dir': context.memory.workspace / 'code',
                    'test_dir': context.memory.workspace / 'tests'
                })

                # 记录测试结果
                iteration_log = {
                    'iteration': retries + 1,
                    'test_passed': test_result['passed'],
                    'test_output': test_result.get('output', ''),
                    'test_stats': {
                        'total': test_result.get('total', 0),
                        'failed': test_result.get('failed', 0)
                    }
                }

                print(f"[QA] Tests {'✅ PASSED' if test_result['passed'] else '❌ FAILED'}")
                print(f"     Total: {test_result.get('total', 0)}, Failed: {test_result.get('failed', 0)}")

                # 测试通过
                if test_result['passed']:
                    print(f"\n{'='*60}")
                    print(f"✅ All tests passed after {retries + 1} iteration(s)!")
                    print(f"{'='*60}\n")

                    # 保存迭代历史
                    context.set('iteration_history', iteration_history)

                    return StageResult(
                        status=StageStatus.SUCCESS,
                        output=test_result,
                        metadata={
                            'iterations': retries + 1,
                            'iteration_history': iteration_history
                        }
                    )

                # 测试失败 - 分析原因
                print(f"\n[QA] Analyzing failure...")
                analysis = {}
                if self.analyzer:
                    analysis = await self.analyzer.analyze(test_result)
                    print(f"[QA] Analysis complete:")
                    print(f"     Error type: {analysis.get('error_type', 'unknown')}")
                    print(f"     Root cause: {analysis.get('root_cause', 'N/A')[:100]}...")

                iteration_log['analysis'] = analysis

                # 保存分析结果到上下文
                context.set('last_test_analysis', analysis)

                # 让开发者修复
                print(f"\n[Developer] Fixing issues based on analysis...")
                fix_result = await dev_agent.process({
                    'action': 'fix_issues',
                    'test_result': test_result,
                    'analysis': analysis
                })

                # 保存修复后的代码
                fixed_files = fix_result.get('fixed_files', {})
                print(f"[Developer] Fixed {len(fixed_files)} file(s)")
                for filename in fixed_files.keys():
                    print(f"     - {filename}")

                iteration_log['fixed_files'] = list(fixed_files.keys())

                for filename, content in fixed_files.items():
                    # 根据文件名判断保存位置：测试文件保存到tests目录，其他文件保存到code目录
                    if filename.startswith('test_') or filename.endswith('_test.py'):
                        # 自动添加 sys.path 设置（如果测试文件中还没有）
                        content = self._ensure_syspath_in_test(content)
                        context.memory.save('tests', filename, content)
                    else:
                        context.memory.save('code', filename, content)

                # 保存本次迭代记录
                iteration_history.append(iteration_log)

                # 保存迭代日志到文件
                self._save_iteration_log(context, iteration_log)

                retries += 1
                context.iteration = retries

                # 检查是否应该停止（用户可以设置标志）
                if context.get('should_stop'):
                    print(f"\n⚠️  Stop requested by user")
                    context.set('iteration_history', iteration_history)
                    return StageResult(
                        status=StageStatus.FAILED,
                        error="Stopped by user",
                        metadata={
                            'iterations': retries,
                            'iteration_history': iteration_history
                        }
                    )

            except Exception as e:
                print(f"\n❌ Error in iteration {retries + 1}: {str(e)}")
                context.set('iteration_history', iteration_history)
                return StageResult(
                    status=StageStatus.FAILED,
                    error=f"Testing error: {str(e)}",
                    metadata={
                        'iterations': retries + 1,
                        'iteration_history': iteration_history
                    }
                )

        # 超过重试次数
        print(f"\n{'='*60}")
        print(f"❌ Tests failed after {retries} iteration(s)")
        print(f"{'='*60}\n")

        # 保存完整的迭代历史
        context.set('iteration_history', iteration_history)

        return StageResult(
            status=StageStatus.FAILED,
            error=f"Tests failed after {retries} retries",
            output=test_result if 'test_result' in locals() else {},
            metadata={
                'iterations': retries,
                'iteration_history': iteration_history
            }
        )

    def _save_iteration_log(self, context: WorkflowContext, iteration_log: dict):
        """保存迭代日志到文件"""
        try:
            reports_dir = context.memory.workspace / 'reports'
            reports_dir.mkdir(exist_ok=True)

            log_file = reports_dir / 'iteration_log.jsonl'

            # 添加时间戳
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                **iteration_log
            }

            # 追加写入（JSONL 格式，每行一个 JSON）
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

            print(f"[System] Iteration log saved to: {log_file}")

        except Exception as e:
            print(f"[System] Warning: Failed to save iteration log: {e}")
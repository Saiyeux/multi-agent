"""Console Reporter - Prints events to console"""

from ..core.interfaces import IReporter, WorkflowEvent


class ConsoleReporter(IReporter):
    """控制台报告器 - 输出工作流事件到控制台"""

    def __init__(self, verbose: bool = True):
        """初始化报告器

        Args:
            verbose: 是否输出详细信息
        """
        self.verbose = verbose

    async def report(self, event: WorkflowEvent):
        """报告事件"""
        event_type = event.event_type
        stage_name = event.stage_name

        # 根据事件类型输出不同格式
        if event_type == 'stage_start':
            print(f"\n[{stage_name}] Starting...")

        elif event_type == 'stage_end':
            status = event.data.get('status', 'unknown')
            if status == 'success':
                print(f"[{stage_name}] ✓ Completed successfully")
            else:
                print(f"[{stage_name}] ✗ Failed: {event.data.get('error', 'unknown')}")

            if self.verbose and event.data.get('output'):
                self._print_output(event.data['output'])

        elif event_type == 'stage_skipped':
            print(f"[{stage_name}] ⊘ Skipped")

        elif event_type == 'stage_error':
            print(f"[{stage_name}] ✗ Error: {event.data.get('error', 'unknown')}")

        elif event_type == 'intervention_start':
            print(f"\n[Intervention] Human intervention requested for {stage_name}")
            print(f"  Reason: {event.data.get('reason', 'unknown')}")

        elif event_type == 'intervention_end':
            print(f"[Intervention] Completed")

        elif event_type == 'workflow_aborted':
            print(f"\n[Workflow] ✗ Aborted by user")

        elif event_type == 'max_iterations_reached':
            iterations = event.data.get('iterations', 0)
            print(f"[{stage_name}] ⚠ Max iterations reached ({iterations})")

        elif event_type == 'error':
            print(f"\n[Error] {event.data.get('error', 'unknown')}")

    def _print_output(self, output: dict):
        """打印输出（简化版）"""
        if isinstance(output, dict):
            for key, value in output.items():
                if isinstance(value, str) and len(value) < 100:
                    print(f"  {key}: {value}")
                elif isinstance(value, (int, float, bool)):
                    print(f"  {key}: {value}")
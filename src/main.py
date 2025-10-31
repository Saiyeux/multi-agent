"""CLI entry point for multi-agent development system (Refactored)"""

import argparse
import asyncio
import sys
from pathlib import Path

from .builders.workflow_builder import WorkflowBuilder


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Software Development System"
    )
    parser.add_argument(
        '--requirement', '-r',
        type=str,
        required=True,
        help='User requirement description'
    )
    parser.add_argument(
        '--config', '-c',
        type=str,
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode (unlimited iterations)'
    )

    args = parser.parse_args()

    # 检查配置文件是否存在
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        sys.exit(1)

    try:
        # 构建工作流引擎
        print(f"Loading configuration from {config_path}...")
        engine = WorkflowBuilder.build_from_config(str(config_path))

        # 如果指定了 debug 模式，覆盖配置
        if args.debug:
            engine.debug_mode = True
            engine.max_iterations = float('inf')
            print("Debug mode enabled (unlimited iterations)")

        # 运行开发流程
        print(f"\n{'='*60}")
        print(f"Multi-Agent Development System (New Architecture)")
        print(f"{'='*60}\n")

        result = await engine.run({
            'requirement': args.requirement
        })

        # 输出结果
        print(f"\n{'='*60}")
        print(f"Results")
        print(f"{'='*60}\n")

        if result['status'] == 'success':
            print(f"✅ Development completed successfully!")
            print(f"\nPackage: {result['output']}")
            print(f"Duration: {result['duration']}")
            print(f"Iterations: {result['iterations']}")
            sys.exit(0)
        elif result['status'] == 'aborted':
            print(f"⚠️  Workflow aborted by user")
            sys.exit(130)
        else:
            print(f"❌ Development failed!")
            print(f"\nReason: {result.get('error', 'Unknown')}")
            print(f"Duration: {result['duration']}")
            print(f"Iterations: {result['iterations']}")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
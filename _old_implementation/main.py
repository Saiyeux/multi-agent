"""CLI entry point for multi-agent development system"""

import argparse
import asyncio
import sys
from pathlib import Path
from .orchestrator import DevOrchestrator


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

    args = parser.parse_args()

    # 检查配置文件是否存在
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        sys.exit(1)

    try:
        # 加载配置
        print(f"Loading configuration from {config_path}...")
        config = DevOrchestrator.load_config(str(config_path))

        # 创建协调器
        orchestrator = DevOrchestrator(config)

        # 运行开发流程
        print(f"\n{'='*60}")
        print(f"Multi-Agent Development System")
        print(f"{'='*60}\n")

        result = await orchestrator.run(args.requirement)

        # 输出结果
        print(f"\n{'='*60}")
        print(f"Results")
        print(f"{'='*60}\n")

        if result['status'] == 'success':
            print(f"✅ Development completed successfully!")
            print(f"\nPackage: {result['package']}")
            print(f"\nTest Report:")
            print(f"  Total tests: {result['report']['total']}")
            print(f"  Passed: {result['report']['total'] - result['report']['failed']}")
            print(f"  Failed: {result['report']['failed']}")
            sys.exit(0)
        else:
            print(f"❌ Development failed!")
            print(f"\nReason: {result.get('reason', result.get('message', 'Unknown'))}")
            if 'last_result' in result:
                print(f"\nLast test result:")
                print(f"  Total tests: {result['last_result']['total']}")
                print(f"  Failed: {result['last_result']['failed']}")
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
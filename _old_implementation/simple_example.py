"""Simple example of using the Multi-Agent Development System"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator import DevOrchestrator


async def main():
    """运行一个简单的开发示例"""

    # 简单的计算器需求
    requirement = """
创建一个简单的命令行计算器程序。

功能需求：
1. 支持基本四则运算：加、减、乘、除
2. 支持连续计算
3. 输入 'quit' 或 'exit' 退出程序
4. 处理除零错误

示例交互：
> 2 + 3
5
> 10 / 2
5
> 5 * 4
20
> quit
Goodbye!
"""

    print("="*60)
    print("Multi-Agent Development System - Example")
    print("="*60)
    print("\nRequirement:")
    print(requirement)
    print("\n" + "="*60 + "\n")

    # 加载配置
    config_path = Path(__file__).parent.parent / "config.yaml"
    config = DevOrchestrator.load_config(str(config_path))

    # 创建协调器
    orchestrator = DevOrchestrator(config)

    # 运行开发流程
    result = await orchestrator.run(requirement)

    # 输出结果
    print("\n" + "="*60)
    print("Result")
    print("="*60 + "\n")

    if result['status'] == 'success':
        print("✅ Development completed successfully!")
        print(f"\n📦 Package: {result['package']}")
        print(f"\n📊 Test Report:")
        print(f"   Total: {result['report']['total']}")
        print(f"   Passed: {result['report']['total'] - result['report']['failed']}")
        print(f"   Failed: {result['report']['failed']}")

        # 显示生成的文件
        print(f"\n📁 Generated Files:")
        for category in ['requirements', 'design', 'code', 'tests']:
            files = orchestrator.memory.list_files(category)
            if files:
                print(f"\n  {category}/")
                for f in files:
                    print(f"    - {f}")

    else:
        print("❌ Development failed!")
        print(f"\nReason: {result.get('reason', result.get('message', 'Unknown'))}")


if __name__ == '__main__':
    asyncio.run(main())
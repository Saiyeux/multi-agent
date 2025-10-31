#!/usr/bin/env python3
"""
查看迭代日志工具

用法:
    python scripts/view_iteration_log.py                # 查看所有迭代
    python scripts/view_iteration_log.py --latest       # 只查看最新一次
    python scripts/view_iteration_log.py --iteration 3  # 查看第3次迭代
"""

import json
import argparse
from pathlib import Path
from datetime import datetime


def load_iteration_log(log_file: Path):
    """加载迭代日志"""
    if not log_file.exists():
        print(f"❌ Log file not found: {log_file}")
        return []

    iterations = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                iterations.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return iterations


def print_iteration(iteration, show_full_output=False):
    """打印单次迭代信息"""
    print(f"\n{'='*80}")
    print(f"🔄 Iteration {iteration['iteration']}")
    print(f"⏰ Time: {iteration.get('timestamp', 'N/A')}")
    print(f"{'='*80}\n")

    # 测试结果
    test_passed = iteration.get('test_passed', False)
    test_stats = iteration.get('test_stats', {})

    print(f"📊 Test Result: {'✅ PASSED' if test_passed else '❌ FAILED'}")
    print(f"   Total tests: {test_stats.get('total', 0)}")
    print(f"   Failed: {test_stats.get('failed', 0)}")

    if not test_passed:
        # 错误分析
        analysis = iteration.get('analysis', {})
        if analysis:
            print(f"\n🔍 Error Analysis:")
            print(f"   Error type: {analysis.get('error_type', 'unknown')}")
            print(f"   Location: {analysis.get('location', 'N/A')}")
            print(f"   Root cause: {analysis.get('root_cause', 'N/A')[:200]}...")

            fix_suggestions = analysis.get('fix_suggestions', [])
            if fix_suggestions:
                print(f"\n💡 Fix Suggestions:")
                for i, suggestion in enumerate(fix_suggestions[:3], 1):
                    print(f"   {i}. {suggestion[:150]}...")

        # 修复的文件
        fixed_files = iteration.get('fixed_files', [])
        if fixed_files:
            print(f"\n🔧 Fixed Files ({len(fixed_files)}):")
            for filename in fixed_files:
                print(f"   - {filename}")

    # 完整输出（可选）
    if show_full_output and not test_passed:
        test_output = iteration.get('test_output', '')
        if test_output:
            print(f"\n📝 Full Test Output:")
            print(f"{'─'*80}")
            print(test_output[:1000])
            if len(test_output) > 1000:
                print(f"\n... ({len(test_output) - 1000} more characters)")
            print(f"{'─'*80}")


def main():
    parser = argparse.ArgumentParser(description="View iteration logs")
    parser.add_argument('--latest', action='store_true', help='Show only the latest iteration')
    parser.add_argument('--iteration', type=int, help='Show specific iteration number')
    parser.add_argument('--full', action='store_true', help='Show full test output')
    parser.add_argument('--log-file', type=str,
                        default='workspace/reports/iteration_log.jsonl',
                        help='Path to log file')

    args = parser.parse_args()

    log_file = Path(args.log_file)
    iterations = load_iteration_log(log_file)

    if not iterations:
        print("📭 No iteration logs found")
        return

    print(f"\n{'='*80}")
    print(f"📂 Iteration Log: {log_file}")
    print(f"📊 Total iterations: {len(iterations)}")
    print(f"{'='*80}")

    # 根据参数显示
    if args.latest:
        print_iteration(iterations[-1], args.full)
    elif args.iteration:
        target_iter = [it for it in iterations if it['iteration'] == args.iteration]
        if target_iter:
            print_iteration(target_iter[0], args.full)
        else:
            print(f"\n❌ Iteration {args.iteration} not found")
    else:
        # 显示所有迭代的摘要
        for iteration in iterations:
            iter_num = iteration['iteration']
            passed = iteration.get('test_passed', False)
            timestamp = iteration.get('timestamp', '')
            status = '✅' if passed else '❌'

            print(f"  {status} Iteration {iter_num:2d} - {timestamp}")

        print(f"\n💡 Use --iteration <N> to see details of a specific iteration")
        print(f"💡 Use --latest to see the most recent iteration")
        print(f"💡 Use --full to include complete test output")


if __name__ == '__main__':
    main()

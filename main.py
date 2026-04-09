#!/usr/bin/env python3
"""
AI 全自动编程 Agent - 主控脚本
基于文件交互的多智能体协作系统
"""

import sys
import time
import argparse
from pathlib import Path

import config
from core.state_manager import StateManager
from core.sentry_checks import SentryCheck
from core.llm_client import llm_client

from skills.planner import run_planner
from skills.coder import run_coder
from skills.debugger import run_debugger
from skills.reviewer import run_reviewer


def print_banner():
    """打印启动横幅"""
    print("""
╔══════════════════════════════════════════════════╗
║     AI 全自动编程 Agent - 多智能体协作系统       ║
║           基于文件交互模式                        ║
╚══════════════════════════════════════════════════╝
    """)


def print_status(state: dict):
    """打印当前状态"""
    print(f"\n📊 当前状态:")
    print(f"   阶段: {state.get('current_phase', 'unknown')}")
    print(f"   重试次数: {state.get('retry_count', 0)}/{state.get('max_retries', config.MAX_RETRIES)}")
    print(f"   总编码周期: {state.get('total_cycles', 0)}/{config.TOTAL_CYCLE_LIMIT}")
    print(f"   Reviewer 驳回: {state.get('review_reject_count', 0)} 次")
    if state.get('last_error_signature'):
        print(f"   上次错误: {state['last_error_signature'][:20]}...")


def print_usage_stats():
    """打印 API 调用统计"""
    stats = llm_client.usage_stats
    if stats["total_calls"] > 0:
        print(f"\n💰 API 调用统计:")
        print(f"   调用次数: {stats['total_calls']}")
        print(f"   Token 用量: {stats['total_tokens']}")


def run_single_cycle():
    """执行单个工作流周期"""
    state = StateManager.load()
    phase = state.get("current_phase", "planning")

    # 死循环检测
    loop_detected, loop_msg = SentryCheck.detect_loop()
    if loop_detected:
        print(f"\n⚠️⚠️⚠️ {loop_msg}")
        print("建议人工介入，查看决策日志。")
        print(f"决策日志位置: {config.WORKSPACE_DIR / 'state.json'}")
        return False

    try:
        if phase == "planning":
            ok, msg = SentryCheck.check_before_planner()
            if not ok:
                print(f"❌ Planner 前置检查失败: {msg}")
                return False
            run_planner()

        elif phase == "coding":
            ok, msg = SentryCheck.check_before_coder()
            if not ok:
                print(f"❌ Coder 前置检查失败: {msg}")
                if "回退到 planning" in msg:
                    StateManager.update(current_phase="planning")
                return False
            run_coder()

        elif phase == "debugging":
            ok, msg = SentryCheck.check_before_debugger()
            if not ok:
                print(f"❌ Debugger 前置检查失败: {msg}")
                StateManager.update(current_phase="coding")
                return False
            run_debugger()

        elif phase == "reviewing":
            ok, msg = SentryCheck.check_before_reviewer()
            if not ok:
                print(f"❌ Reviewer 前置检查失败: {msg}")
                StateManager.update(current_phase="debugging")
                return False
            run_reviewer()

        elif phase == "completed":
            print("\n🎉🎉🎉 所有任务已完成！")
            return False

        else:
            print(f"❌ 未知阶段: {phase}")
            return False

        return True

    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_continuous(max_cycles: int = 10, delay: int = 2):
    """连续运行多个周期"""
    print_banner()

    for cycle in range(1, max_cycles + 1):
        print(f"\n{'='*50}")
        print(f"第 {cycle} 轮执行")
        print('='*50)

        state = StateManager.load()
        print_status(state)

        if state.get("current_phase") == "completed":
            print("\n🎉 任务已完成，退出循环。")
            break

        should_continue = run_single_cycle()
        if not should_continue:
            if state.get("current_phase") != "completed":
                print("\n⚠️ 流程中断，请检查日志。")
            break

        time.sleep(delay)

    # 打印最终总结
    print("\n" + "="*50)
    print("执行完成。最终状态:")
    final_state = StateManager.load()
    print_status(final_state)

    # 打印决策摘要
    trail = final_state.get("decision_trail", [])
    if trail:
        print(f"\n📝 决策日志摘要 (共 {len(trail)} 条):")
        for entry in trail[-5:]:
            print(f"   [{entry.get('agent', 'unknown')}] {entry.get('timestamp', '')[:16]}")

    # 打印 API 用量
    print_usage_stats()


def init_workspace(task_description: str):
    """初始化工作区，创建第一个任务"""
    print_banner()
    print("正在初始化工作区...")

    # 创建任务文件
    task = {
        "id": "task_001",
        "description": task_description,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "pending"
    }
    StateManager.save_current_task(task)

    # 初始化状态
    StateManager.save({
        "current_phase": "planning",
        "current_task_id": task["id"],
        "original_requirement": task_description,
        "retry_count": 0,
        "max_retries": config.MAX_RETRIES,
        "total_cycles": 0,
        "review_reject_count": 0,
        "last_error_signature": None,
        "loop_detection": {
            "consecutive_same_error": 0,
            "action_on_threshold": "pause_and_request_human_guidance"
        },
        "decision_trail": [],
        "version": 1
    })

    print(f"✅ 工作区初始化完成")
    print(f"   任务: {task_description}")
    print(f"   工作目录: {config.WORKSPACE_DIR}")
    print("\n现在可以运行: python main.py --run")


def main():
    parser = argparse.ArgumentParser(description="AI 全自动编程 Agent")
    parser.add_argument("--init", type=str, metavar="TASK", help="初始化工作区并设置任务描述")
    parser.add_argument("--run", action="store_true", help="运行自动编程流程")
    parser.add_argument("--cycles", type=int, default=10, help="最大运行周期数 (默认: 10)")
    parser.add_argument("--delay", type=int, default=2, help="周期之间的延迟秒数 (默认: 2)")
    parser.add_argument("--status", action="store_true", help="查看当前状态")
    parser.add_argument("--reset", action="store_true", help="重置工作区")

    args = parser.parse_args()

    if args.reset:
        if config.WORKSPACE_DIR.exists():
            confirm = input(f"⚠️ 即将删除 {config.WORKSPACE_DIR}，确认吗？(y/N): ").strip().lower()
            if confirm != 'y':
                print("已取消。")
                return
            import shutil
            shutil.rmtree(config.WORKSPACE_DIR, ignore_errors=True)
            print("✅ 工作区已重置")
        else:
            print("工作区不存在，无需重置。")
        return

    if args.status:
        print_banner()
        state = StateManager.load()
        print_status(state)
        task = StateManager.get_current_task()
        if task:
            print(f"\n📋 当前任务: {task.get('description', 'N/A')}")
        return

    if args.init:
        init_workspace(args.init)
        return

    if args.run:
        run_continuous(max_cycles=args.cycles, delay=args.delay)
        return

    parser.print_help()


if __name__ == "__main__":
    main()

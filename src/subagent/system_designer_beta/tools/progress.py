"""
进度提示工具 - 为工作流提供进度反馈

用法:
    from tools.progress import ProgressTracker
    
    tracker = ProgressTracker("写策划案")
    tracker.step(1, 5, "正在分析UI参考图...")
    # ... 执行操作
    tracker.step(2, 5, "正在生成需求Draft...")
    # ... 执行操作
    tracker.complete("策划案生成完成！")
"""

import sys
from typing import Optional


class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, task_name: str, output_file=None):
        """
        初始化进度跟踪器
        
        Args:
            task_name: 任务名称
            output_file: 输出文件（默认 stderr）
        """
        self.task_name = task_name
        self.output_file = output_file or sys.stderr
        self.current_step = 0
        self.total_steps = 0
        
    def start(self, total_steps: int, message: str = ""):
        """
        开始任务
        
        Args:
            total_steps: 总步骤数
            message: 开始消息
        """
        self.total_steps = total_steps
        self.current_step = 0
        msg = f"🚀 开始{self.task_name}"
        if message:
            msg += f": {message}"
        print(msg, file=self.output_file)
        
    def step(self, step_num: int, total_steps: int, message: str):
        """
        更新进度
        
        Args:
            step_num: 当前步骤
            total_steps: 总步骤数
            message: 进度消息
        """
        self.current_step = step_num
        self.total_steps = total_steps
        percentage = int((step_num / total_steps) * 100)
        progress_bar = self._make_progress_bar(percentage)
        print(f"[{progress_bar}] {step_num}/{total_steps} ({percentage}%) {message}", 
              file=self.output_file)
        
    def info(self, message: str):
        """输出信息消息"""
        print(f"ℹ️ {message}", file=self.output_file)
        
    def warning(self, message: str):
        """输出警告消息"""
        print(f"⚠️ {message}", file=self.output_file)
        
    def error(self, message: str):
        """输出错误消息"""
        print(f"❌ {message}", file=self.output_file)
        
    def complete(self, message: str = ""):
        """
        完成任务
        
        Args:
            message: 完成消息
        """
        msg = f"✅ {self.task_name}完成"
        if message:
            msg += f": {message}"
        print(msg, file=self.output_file)
        
    def _make_progress_bar(self, percentage: int, width: int = 20) -> str:
        """生成进度条"""
        filled = int(width * percentage / 100)
        bar = "█" * filled + "░" * (width - filled)
        return bar


def print_step(step_num: int, total_steps: int, message: str):
    """
    打印步骤进度（简单版本）
    
    Args:
        step_num: 当前步骤
        total_steps: 总步骤数
        message: 消息
    """
    percentage = int((step_num / total_steps) * 100)
    print(f"[{step_num}/{total_steps}] ({percentage}%) {message}", file=sys.stderr)


def print_workflow_start(workflow_name: str, steps: list):
    """
    打印工作流开始信息
    
    Args:
        workflow_name: 工作流名称
        steps: 步骤列表
    """
    print(f"\n{'='*50}", file=sys.stderr)
    print(f"🚀 {workflow_name}", file=sys.stderr)
    print(f"{'='*50}", file=sys.stderr)
    for i, step in enumerate(steps, 1):
        print(f"  {i}. {step}", file=sys.stderr)
    print(f"{'='*50}\n", file=sys.stderr)


def print_workflow_complete(workflow_name: str, output_path: Optional[str] = None):
    """
    打印工作流完成信息
    
    Args:
        workflow_name: 工作流名称
        output_path: 输出文件路径
    """
    print(f"\n{'='*50}", file=sys.stderr)
    print(f"✅ {workflow_name}完成！", file=sys.stderr)
    if output_path:
        print(f"📄 输出文件: {output_path}", file=sys.stderr)
    print(f"{'='*50}\n", file=sys.stderr)


# 工作流步骤定义
WORKFLOW_STEPS = {
    "write": [
        "获取UI参考图或文字描述",
        "调用需求拆解Agent（A2）",
        "等待用户确认需求Draft",
        "调用系统策划Agent（A1）",
        "调用规范审查Agent（A3）",
        "保存对话记录",
        "调用Prompt守护Agent（A5）"
    ],
    "review": [
        "获取策划案内容",
        "调用规范审查Agent（A3）",
        "展示审查报告",
        "保存对话记录"
    ],
    "revision": [
        "获取原策划案和修改意见",
        "调用系统策划Agent（A1）",
        "调用规范审查Agent（A3）",
        "保存对话记录"
    ],
    "reverse": [
        "获取策划案内容",
        "调用逆向需求Agent（A4）",
        "调用系统策划Agent（A1）",
        "调用规范审查Agent（A3）",
        "保存对话记录"
    ]
}


def get_workflow_steps(workflow: str) -> list:
    """获取工作流步骤"""
    return WORKFLOW_STEPS.get(workflow, [])
"""
测试配置文件
"""
import os
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "subagent" / "system_designer_beta"))

# 设置测试环境变量
os.environ["ANTHROPIC_API_KEY"] = "test-key-for-testing"
os.environ["LOG_LEVEL"] = "WARNING"  # 测试时减少日志输出

import pytest


@pytest.fixture
def sample_requirements_draft():
    """示例需求Draft"""
    return """
# 需求 Draft：签到系统

## 功能概述
用户每日签到获得奖励，连续签到有额外奖励。

## 核心功能
1. 每日签到按钮
2. 签到日历
3. 奖励发放
4. 连续签到统计

## UI 要求
- 签到按钮居中显示
- 日历以月视图展示
- 奖励图标清晰可见
"""


@pytest.fixture
def sample_planning_document():
    """示例策划案"""
    return """
# 签到系统策划案

## 一、系统概述
### 1.1 系统名称
签到系统

### 1.2 系统定位
提升用户活跃度和留存率的核心系统。

### 1.3 核心价值
- 提升DAU
- 增加用户粘性
- 促进付费转化

## 二、功能详情
### 2.1 每日签到
- 点击签到按钮获得奖励
- 奖励：金币、道具、经验

### 2.2 连续签到
- 连续7天额外奖励
- 断签重置计数

## 三、数值设计
| 天数 | 奖励 |
|------|------|
| 1 | 100金币 |
| 2 | 150金币 |
| 3 | 200金币 |
| 7 | 500金币+稀有道具 |
"""


@pytest.fixture
def sample_review_result():
    """示例审查结果"""
    return """
## 规范审查报告

### 通过项
- [x] 系统概述完整
- [x] 功能描述清晰

### 问题项
- [ ] 缺少详细的UI交互说明
- [ ] 数值设计缺少平衡性分析

### 建议
1. 补充UI交互流程图
2. 添加数值平衡性测试数据
"""


@pytest.fixture
def temp_dir(tmp_path):
    """临时目录"""
    # 创建必要的子目录
    (tmp_path / "docs").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "images").mkdir()
    (tmp_path / "data" / "sessions").mkdir()
    (tmp_path / "data" / "test").mkdir()
    return tmp_path
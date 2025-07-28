#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
链式时延协议管理系统
Chain Delay Protocol Management System

基于"神圣座位原理"和"下必为例原则"的行为管理工具
"""

import json
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from formula_manager import FormulaManager


class ChainDelayProtocol:
    def __init__(self, update_callback=None):
        self.data_file = 'protocol_data.json'
        self.data = self.load_data()
        self.update_callback = update_callback

        # 初始化定式管理器
        self.formula_manager = FormulaManager(data_callback=self.save_data)
        self.formula_manager.set_formulas_data(self.data.get("formulas", {}))

        # 运行时状态
        self.reservation_active = False
        self.reservation_end_time = None
        self.task_active = False
        self.task_end_time = None
        self.timer_thread = None

        # 启动时打印历史信息
        print("="*50)
        print(f"👑 历史最长链: {self.data.get('longest_chain', 0)} 节点")
        if self.data.get('task_history'):
            print("📜 最近任务:")
            for task in self.data['task_history'][-5:]:
                print(f"  - {task}")
        print("="*50)

    def load_data(self) -> Dict[str, Any]:
        """加载数据文件"""
        default_data = {
            "task_chain": [],
            "allowed_violations": [],
            "formulas": {
                "formulas": [],
                "last_addition_date": None
            },
            "settings": {
                "reservation_minutes": 15,
                "task_minutes": 30
            },
            "longest_chain": 0,
            "task_history": []
        }

        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # 合并默认数据和加载的数据
                for key, value in default_data.items():
                    if key not in data:
                        data[key] = value
                return data
            except Exception as e:
                print(f"加载数据文件失败: {e}")
                return default_data
        else:
            return default_data

    def save_data(self):
        """保存数据到文件"""
        self.data['formulas'] = self.formula_manager.get_formulas_data()
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

        if self.update_callback:
            self.update_callback()

    def start_reservation(self, minutes: Optional[int] = None):
        """启动预约链"""
        if self.reservation_active or self.task_active:
            print("已有活动的预约或任务，无法启动新的预约")
            return False

        reservation_minutes = minutes if minutes is not None else self.data[
            "settings"]["reservation_minutes"]
        self.reservation_active = True
        self.reservation_end_time = datetime.now() + timedelta(minutes=reservation_minutes)

        print(f"\n🔔 预约链已启动！")
        print(f"⏰ 必须在 {reservation_minutes} 分钟内触发'神圣座位'")
        print(f"⏱️  截止时间: {self.reservation_end_time.strftime('%H:%M:%S')}")

        # 启动计时器线程
        self.timer_thread = threading.Thread(target=self._reservation_timer)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        return True

    def _reservation_timer(self):
        """预约链计时器"""
        while self.reservation_active and datetime.now() < self.reservation_end_time:
            remaining = (self.reservation_end_time -
                         datetime.now()).total_seconds()
            if remaining > 0:
                time.sleep(1)
            else:
                break

        if self.reservation_active:
            print(f"\n⚠️  预约链超时！")
            print("请选择处理方式:")
            print("1. 清空预约链记录")
            print("2. 允许当前情况，但预约链失去约束力")
            self.reservation_active = False

    def start_task(self, minutes: Optional[int] = None, task_name: Optional[str] = None):
        """触发神圣座位，开始任务"""
        if self.task_active:
            print("❌ 任务已在进行中")
            return

        # 如果预约是激活的，就停止它
        if self.reservation_active:
            self.reservation_active = False
            print("\n🔔 预约链已完成，神圣座位触发！")

        task_minutes = minutes if minutes is not None else self.data["settings"]["task_minutes"]
        task_name = task_name if task_name else "未命名任务"

        self.task_active = True
        self.task_end_time = datetime.now() + timedelta(minutes=task_minutes)

        new_node_id = len(self.data["task_chain"]) + 1
        new_node = {
            "id": new_node_id,
            "name": task_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.data["task_chain"].append(new_node)
        self.save_data()

        print(f"\n👑 任务 '#{new_node_id} [{task_name}]' 已开始！")
        print(f"⏳ 任务时长: {task_minutes} 分钟")
        print(f"⏱️  预计完成: {self.task_end_time.strftime('%H:%M:%S')}")

        # 启动任务计时器线程
        self.timer_thread = threading.Thread(target=self._task_timer)
        self.timer_thread.daemon = True
        self.timer_thread.start()

        return True

    def _task_timer(self):
        """任务计时器"""
        while self.task_active and datetime.now() < self.task_end_time:
            remaining = (self.task_end_time - datetime.now()).total_seconds()
            if remaining > 0:
                time.sleep(1)
            else:
                break

        if self.task_active:
            self.complete_task()

    def complete_task(self):
        """完成任务"""
        if not self.task_active:
            print("❌ 没有正在进行的任务")
            return

        remaining_time = (self.task_end_time - datetime.now()).total_seconds()

        if remaining_time > 0:
            print(f"\n🎉 任务提前完成！")
        else:
            print(f"\n🎉 任务按时完成！")

        self.task_active = False
        current_chain_length = len(self.data['task_chain'])
        last_task = self.data['task_chain'][-1]

        print(
            f"🔗 任务 '#{last_task['id']} [{last_task['name']}]' 已完成。当前链长: {current_chain_length}")

        # 更新最长链记录
        if current_chain_length > self.data.get('longest_chain', 0):
            self.data['longest_chain'] = current_chain_length
            print(f"👑 新纪录！最长链更新为: {current_chain_length}")

        self.save_data()
        return True

    def stop_task(self):
        """停止任务"""
        if not self.task_active:
            print("没有进行中的任务")
            return

        self.task_active = False
        print("⏹️  任务已停止")

    def reset_chain(self, description: str):
        """重置任务链"""
        print(f"\n⚠️ {description}，任务链已断开！")

        # 将当前链条记录到历史
        if self.data['task_chain']:
            chain_str = ' -> '.join(
                [f"#{n['id']} [{n['name']}]" for n in self.data['task_chain']])
            self.data['task_history'].append(chain_str)
            # 保留最近20条历史
            self.data['task_history'] = self.data['task_history'][-20:]

        self.data["task_chain"] = []
        self.task_active = False
        self.reservation_active = False
        self.save_data()
        print(f"\n🔄 任务链已重置")
        print(f"📝 重置原因: {description}")
        print("⚡ 下次将从 #1 重新开始")

    def allow_violation(self, description: str):
        """永久允许违规行为"""
        violation = {
            "id": max([v["id"] for v in self.data["allowed_violations"]], default=0) + 1,
            "description": description,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "permanent": True
        }

        self.data["allowed_violations"].append(violation)
        self.save_data()

        print(f"\n✅ 行为已永久允许")
        print(f"📝 允许行为: {description}")
        print("⚠️  此行为在后续任务中将不再视为违规")

    def show_status(self):
        """显示当前状态"""
        print("\n" + "="*50)
        print("📊 链式时延协议 - 当前状态")
        print("="*50)

        # 预约链状态
        if self.reservation_active:
            remaining = (self.reservation_end_time -
                         datetime.now()).total_seconds()
            if remaining > 0:
                print(
                    f"🔔 预约链: 进行中 (剩余 {int(remaining//60)}:{int(remaining%60):02d})")
            else:
                print("🔔 预约链: 已超时")
        else:
            print("🔔 预约链: 未激活")

        # 任务链状态
        if self.task_active:
            remaining = (self.task_end_time - datetime.now()).total_seconds()
            if remaining > 0:
                print(
                    f"🎯 任务链: 进行中 (剩余 {int(remaining//60)}:{int(remaining%60):02d})")
            else:
                print("🎯 任务链: 已完成")
        else:
            print("🎯 任务链: 未激活")

        # 最长链记录
        print(f"👑 历史最长链: {self.data.get('longest_chain', 0)} 节点")

        # 任务链节点
        print(f"\n📈 当前任务链 ({len(self.data['task_chain'])} 节):")
        if self.data["task_chain"]:
            for node in self.data["task_chain"]:
                print(
                    f"  #{node['id']} [{node['name']}] - {node['timestamp']}")
        else:
            print("  当前无任务链")

    def show_allowed_violations(self):
        """显示已允许的违规行为"""
        print("\n" + "="*50)
        print("📋 已永久允许的行为")
        print("="*50)

        if not self.data["allowed_violations"]:
            print("暂无已允许行为")
            return

        for violation in self.data["allowed_violations"]:
            print(f"\n🔸 {violation['description']}")
            print(f"   时间: {violation['timestamp']}")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定式管理模块
Formula Management Module

独立的定式树管理功能，与链式时延协议解耦
"""

import json
from datetime import date, timedelta
from typing import Dict, List, Optional, Any, Tuple


class FormulaManager:
    """定式管理器类"""
    
    def __init__(self, data_callback=None):
        """
        初始化定式管理器
        
        Args:
            data_callback: 数据保存回调函数，用于与主系统同步数据
        """
        self.data_callback = data_callback
        self._formulas = []
        self.last_addition_date = None
        self.active_tree_progress = {}  # 跟踪活跃定式树的进度
        self._load_default_formulas()
    
    def _load_default_formulas(self):
        """加载默认定式数据"""
        self._formulas = [
            {"id": 1, "name": "A定式", "parent": None, "children": [2, 3], "status": "活跃", "last_active_time": date.today().isoformat()},
            {"id": 2, "name": "B定式", "parent": 1, "children": [4], "status": "活跃", "last_active_time": date.today().isoformat()},
            {"id": 3, "name": "C定式", "parent": 1, "children": [], "status": "未执行", "last_active_time": None},
            {"id": 4, "name": "D定式", "parent": 2, "children": [], "status": "未执行", "last_active_time": None}
        ]
    
    def set_formulas_data(self, data: Dict[str, Any]):
        """设置定式数据"""
        self._formulas = data.get("formulas", [])
        # 加载进度并确保键为 int 类型（JSON 会将字典键转换为字符串）
        raw_progress = data.get("active_tree_progress", {})
        self.active_tree_progress = {int(k): v for k, v in raw_progress.items()}
        last_date_str = data.get("last_addition_date")
        if last_date_str:
            self.last_addition_date = date.fromisoformat(last_date_str)
        else:
            self.last_addition_date = None
    
    def get_formulas_data(self) -> Dict[str, Any]:
        """获取定式数据"""
        return {
            "formulas": self._formulas,
            "last_addition_date": self.last_addition_date.isoformat() if self.last_addition_date else None,
            "active_tree_progress": self.active_tree_progress  # 保存进度
        }
    
    def _save_data(self):
        """保存数据（通过回调函数）"""
        if self.data_callback:
            self.data_callback()
    
    def show_formula_tree(self, parent_id=None, level=0) -> str:
        """
        显示定式树结构
        
        Args:
            parent_id: 父节点ID，None表示根节点
            level: 层级深度
            
        Returns:
            格式化的树形结构字符串
        """
        result = []
        formulas = [f for f in self._formulas if f["parent"] == parent_id]
        
        for formula in formulas:
            indent = "  " * level
            result.append(f"{indent}📁 {formula['name']} (ID: {formula['id']})")
            # 递归显示子节点
            child_result = self.show_formula_tree(formula["id"], level + 1)
            if child_result:
                result.append(child_result)
        
        return "\n".join(result) if result else ""
    
    def print_formula_tree(self, parent_id=None, level=0):
        """打印定式树结构（用于命令行界面）"""
        formulas = [f for f in self._formulas if f["parent"] == parent_id]
        
        for formula in formulas:
            indent = "  " * level
            print(f"{indent}📁 {formula['name']} (ID: {formula['id']})")
            self.print_formula_tree(formula["id"], level + 1)
    
    def add_formula(self, name: str, parent_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        添加新定式

        Args:
            name: 定式名称
            parent_id: 父节点ID，None表示根节点

        Returns:
            (是否添加成功, 提示信息)
        """
        # 检查今天是否已经添加过
        if self.last_addition_date == date.today():
            return False, "今天已经添加过一个定式了，请明天再试。"

        if not name.strip():
            return False, "定式名称不能为空。"

        # 验证父节点是否存在
        if parent_id and not any(f["id"] == parent_id for f in self._formulas):
            return False, "父定式不存在。"

        # 创建新定式
        new_id = max([f["id"] for f in self._formulas], default=0) + 1
        new_formula = {
            "id": new_id,
            "name": name.strip(),
            "parent": parent_id,
            "children": [],
            "status": "未执行",
            "last_active_time": None
        }

        # 更新父节点的children
        if parent_id:
            for formula in self._formulas:
                if formula["id"] == parent_id:
                    formula["children"].append(new_id)
                    break

        self._formulas.append(new_formula)
        self.last_addition_date = date.today()  # 更新添加日期
        self._save_data()
        return True, f"定式 '{name.strip()}' 已成功添加。"
    
    def remove_formula(self, formula_id: int, confirm: bool = False) -> Tuple[bool, List[str]]:
        """
        删除定式及其所有子节点

        Args:
            formula_id: 要删除的定式ID
            confirm: 是否确认删除，默认为False（只返回待删除列表）

        Returns:
            (是否删除成功, 被删除的定式名称列表)
        """
        # 获取要删除的节点及其所有子节点
        def get_descendants(node_id):
            descendants = [node_id]
            for formula in self._formulas:
                if formula["parent"] == node_id:
                    descendants.extend(get_descendants(formula["id"]))
            return descendants
        
        to_delete = get_descendants(formula_id)
        deleted_names = [f["name"] for f in self._formulas if f["id"] in to_delete]
        
        if not deleted_names:
            return False, []
        
        if confirm is False:
            return True, deleted_names
        
        # 删除指定节点及其子节点
        self._formulas = [f for f in self._formulas if f["id"] not in to_delete]
        
        # 更新其他节点的children
        for formula in self._formulas:
            formula["children"] = [c for c in formula["children"] if c not in to_delete]
        
        self._save_data()
        return True, deleted_names
    
    def get_formula_by_id(self, formula_id: int) -> Optional[Dict]:
        """根据ID获取定式"""
        for formula in self._formulas:
            if formula["id"] == formula_id:
                return formula
        return None
    
    def get_formula_by_name(self, name: str) -> Optional[Dict]:
        """根据名称获取定式"""
        for formula in self._formulas:
            if formula["name"] == name:
                return formula
        return None
    
    def get_root_formulas(self) -> List[Dict]:
        """获取所有根节点定式"""
        return [f for f in self._formulas if f["parent"] is None]
    
    def get_children_formulas(self, parent_id: int) -> List[Dict]:
        """获取指定节点的子定式"""
        return [f for f in self._formulas if f["parent"] == parent_id]

    def get_nodes_at_level(self, root_id: int, level: int) -> List[Dict]:
        """
        获取指定树在特定层级的所有节点
        
        Args:
            root_id: 树的根节点ID
            level: 目标层级 (根节点为0)
            
        Returns:
            在指定层级的所有节点的列表
        """
        if level < 0:
            return []

        # Start with the root node at level 0
        nodes_at_current_level = [self.get_formula_by_id(root_id)]
        
        # Iteratively find children for each level up to the target level
        for _ in range(level):
            next_level_nodes = []
            # If the current level is empty, we can't go deeper
            if not nodes_at_current_level:
                return []
            for node in nodes_at_current_level:
                if node: # Should always be true unless data is inconsistent
                    children = self.get_children_formulas(node['id'])
                    next_level_nodes.extend(children)
            nodes_at_current_level = next_level_nodes
        
        # Filter out any potential None values if get_formula_by_id returned None initially
        return [node for node in nodes_at_current_level if node]

    def execute_next_level(self, root_id: int) -> bool:
        """
        将指定树的层级进度加一。如果已是最后一层，则重置为0。
        
        Args:
            root_id: 树的根节点ID
            
        Returns:
            True 如果完成了一个循环 (回到根层), 否则 False
        """
        if root_id not in self.active_tree_progress:
            return False # 或者可以引发一个错误

        current_level = self.active_tree_progress[root_id]
        next_level_nodes = self.get_nodes_at_level(root_id, current_level + 1)

        if not next_level_nodes:
            # 已经是最后一层，重置为0
            self.active_tree_progress[root_id] = 0
            self._save_data()
            return True
        else:
            # 进入下一层
            self.active_tree_progress[root_id] = current_level + 1
            self._save_data()
            return False

    def get_active_formulas_display(self) -> str:
        """
        生成所有活跃定式树当前层级任务的格式化字符串
        
        Returns:
            用于UI显示的格式化字符串
        """
        if not self.active_tree_progress:
            return "当前没有活跃的定式树。"

        display_parts = []
        # 对活跃树按ID排序，以确保显示顺序稳定
        sorted_active_trees = sorted(self.active_tree_progress.items())

        for root_id, current_level in sorted_active_trees:
            root_node = self.get_formula_by_id(root_id)
            if not root_node:
                continue
            
            tree_name = root_node.get('name', f"ID: {root_id}")
            header = f"🌳 {tree_name} (当前层级: {current_level}):"
            display_parts.append(header)
            
            nodes_at_level = self.get_nodes_at_level(root_id, current_level)
            
            if not nodes_at_level:
                display_parts.append("  - (当前层级无任务)")
            else:
                for node in nodes_at_level:
                    display_parts.append(f"  - {node.get('name', '未知任务')}")
            display_parts.append("") # 添加空行以分隔不同的树
        
        return "\n".join(display_parts)

    def change_formula_status(self, formula_id: int) -> bool:
        """切换定式的状态（活跃/未执行）"""
        formula = self.get_formula_by_id(formula_id)
        if formula:
            is_root = formula.get('parent') is None
            
            if formula['status'] == '活跃':
                formula['status'] = '未执行'
                # 如果是根节点，从进度跟踪中移除
                if is_root and formula_id in self.active_tree_progress:
                    del self.active_tree_progress[formula_id]
            else:
                formula['status'] = '活跃'
                formula['last_active_time'] = date.today().isoformat()
                # 如果是根节点，添加到进度跟踪中，层级为0
                if is_root:
                    self.active_tree_progress[formula_id] = 0
            
            self._save_data()
            return True
        return False
    

    
    def update_formula_name(self, formula_id: int, new_name: str) -> bool:
        """更新定式名称"""
        if not new_name.strip():
            return False
        
        formula = self.get_formula_by_id(formula_id)
        if formula:
            formula["name"] = new_name.strip()
            self._save_data()
            return True
        return False
    
    def get_formula_count(self) -> int:
        """获取定式总数"""
        return len(self._formulas)
    

    
    def clear_all_formulas(self) -> bool:
        """清空所有定式"""
        self._formulas = []
        self._save_data()
        return True
    
    def export_formulas(self) -> str:
        """导出定式数据为JSON字符串"""
        return json.dumps(self._formulas, ensure_ascii=False, indent=2)
    
    def check_inactive_formulas(self) -> List[str]:
        """检查并返回超过一周未活跃的定式名称列表"""
        inactive_formulas = []
        one_week_ago = date.today() - timedelta(days=7)
        for formula in self._formulas:
            if formula['status'] == '活跃' and formula['last_active_time']:
                last_active = date.fromisoformat(formula['last_active_time'])
                if last_active < one_week_ago:
                    inactive_formulas.append(formula['name'])
        return inactive_formulas

    def import_formulas(self, json_data: str) -> bool:
        """从JSON字符串导入定式数据"""
        try:
            formulas = json.loads(json_data)
            if isinstance(formulas, list):
                self._formulas = formulas
                self._save_data()
                return True
        except json.JSONDecodeError:
            pass
        return False

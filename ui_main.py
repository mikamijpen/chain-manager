#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
链式时延协议管理系统 - GUI界面
Chain Delay Protocol Management System - GUI Interface

基于tkinter的现代化图形用户界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import sys
from main import ChainDelayProtocol
from formula_manager import FormulaManager

def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')



class TextRedirector:
    """A class to redirect stdout to a tkinter Text widget."""
    def __init__(self, widget):
        self.widget = widget

    def write(self, text):
        self.widget.configure(state='normal')
        self.widget.insert('end', text)
        self.widget.see('end')
        self.widget.configure(state='disabled')

    def flush(self):
        pass

class FormulaManagerGUI:
    """GUI for managing formulas in a separate window."""
    def __init__(self, parent, formula_manager):
        self.window = tk.Toplevel(parent)
        self.window.title("管理定式")
        self.window.geometry("500x600")
        self.window.transient(parent)
        self.window.grab_set()

        self.formula_manager = formula_manager
        self.create_widgets()
        center_window(self.window)

    def create_widgets(self):
        tree_frame = ttk.LabelFrame(self.window, text="定式树", padding=10)
        tree_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.tree_view = ttk.Treeview(tree_frame, columns=("status",), show="tree headings")
        self.tree_view.heading("#0", text="定式内容")
        self.tree_view.heading("status", text="状态")
        self.tree_view.pack(expand=True, fill="both")

        self.refresh_tree()

        action_frame = ttk.Frame(self.window, padding=10)
        action_frame.pack(fill="x")

        # Add Formula Section
        add_frame = ttk.LabelFrame(action_frame, text="添加定式 (选中条目为父级)", padding=10)
        add_frame.pack(fill="x", pady=5)

        ttk.Label(add_frame, text="名称:").grid(row=0, column=0, padx=5, pady=5)
        self.name_entry = ttk.Entry(add_frame)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        add_frame.columnconfigure(1, weight=1)

        add_button = ttk.Button(add_frame, text="添加", command=self.add_formula_action)
        add_button.grid(row=1, columnspan=2, pady=10)

        # Remove Formula Section
        remove_frame = ttk.LabelFrame(action_frame, text="删除定式 (选中条目)", padding=10)
        remove_frame.pack(fill="x", pady=5)

        remove_button = ttk.Button(remove_frame, text="删除", command=self.remove_formula_action)
        remove_button.pack(pady=5, side="left", padx=5)

        change_status_button = ttk.Button(remove_frame, text="更改状态", command=self.change_status_action)
        change_status_button.pack(pady=5, side="right", padx=5)

    def refresh_tree(self):
        for i in self.tree_view.get_children():
            self.tree_view.delete(i)
        self.populate_tree(None, '')

    def populate_tree(self, parent_id, parent_node):
        formulas_data = self.formula_manager.get_formulas_data()
        children = [f for f in formulas_data.get('formulas', []) if f["parent"] == parent_id]
        for child in children:
            node = self.tree_view.insert(parent_node, 'end', iid=child['id'], text=child['name'], values=(child['status'],))
            self.populate_tree(child['id'], node)

    def add_formula_action(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("警告", "请输入定式名称", parent=self.window)
            return

        selected_item = self.tree_view.focus()
        parent_id = int(selected_item) if selected_item else None

        success, message = self.formula_manager.add_formula(name, parent_id)

        if success:
            messagebox.showinfo("成功", message, parent=self.window)
            self.refresh_tree()
            self.name_entry.delete(0, 'end')
        else:
            messagebox.showerror("错误", message, parent=self.window)

    def change_status_action(self):
        selected_item = self.tree_view.focus()
        if not selected_item:
            messagebox.showwarning("警告", "请选择一个定式", parent=self.window)
            return

        formula_id = int(selected_item)
        self.formula_manager.change_formula_status(formula_id)
        self.refresh_tree()

    def remove_formula_action(self):
        selected_item = self.tree_view.focus()
        if not selected_item:
            messagebox.showwarning("警告", "请在树中选择要删除的定式", parent=self.window)
            return

        remove_id = int(selected_item)
        formula = self.formula_manager.get_formula_by_id(remove_id)
        if not formula:
            messagebox.showerror("错误", f"未找到ID为 {remove_id} 的定式", parent=self.window)
            return

        confirm = messagebox.askyesno("确认删除", f"确定要删除定式 '{formula['name']}' 及其所有子定式吗？", parent=self.window)
        if confirm:
            success, deleted_names = self.formula_manager.remove_formula(remove_id)
            if success:
                messagebox.showinfo("成功", f"定式 '{', '.join(deleted_names)}' 已被删除", parent=self.window)
                self.refresh_tree()
            else:
                messagebox.showerror("错误", "删除失败", parent=self.window)

class CustomChoiceDialog(tk.Toplevel):
    def __init__(self, parent, title, message, button_texts, show_input=False, input_prompt=""):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.result = None
        self.input_text = ""

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill="both")

        if message:
            ttk.Label(main_frame, text=message, wraplength=350, justify="left").pack(pady=5, anchor='w')

        if show_input:
            ttk.Label(main_frame, text=input_prompt).pack(pady=(10, 0), anchor='w')
            self.input_entry = ttk.Entry(main_frame, width=50)
            self.input_entry.pack(pady=5, fill="x")
            self.input_entry.focus_set()

        button_frame = ttk.Frame(self, padding=10)
        button_frame.pack(fill="x")

        for text in button_texts:
            button = ttk.Button(button_frame, text=text, command=lambda t=text: self.on_button_click(t))
            button.pack(side="left", padx=10, pady=10, expand=True, fill="x")

        center_window(self)
        self.wait_window(self)

    def on_button_click(self, choice):
        if hasattr(self, 'input_entry'):
            self.input_text = self.input_entry.get().strip()
            if not self.input_text:
                messagebox.showwarning("警告", "必须提供说明。", parent=self)
                return
        self.result = choice
        self.destroy()

class InputDialog(tk.Toplevel):
    def __init__(self, parent, title, prompts):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.result = None

        self.entries = {}
        for i, prompt in enumerate(prompts):
            ttk.Label(self, text=prompt).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            entry = ttk.Entry(self)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            self.entries[prompt] = entry

        self.entries[prompts[0]].focus_set()

        button_frame = ttk.Frame(self)
        button_frame.grid(row=len(prompts), columnspan=2, pady=10)

        ttk.Button(button_frame, text="确定", command=self.on_ok).pack(side="left", padx=5)
        ttk.Button(button_frame, text="取消", command=self.on_cancel).pack(side="left", padx=5)

        center_window(self)
        self.wait_window(self)

    def on_ok(self):
        self.result = {prompt: entry.get().strip() for prompt, entry in self.entries.items()}
        self.destroy()

    def on_cancel(self):
        self.destroy()


class ChainDelayProtocolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("链式时延协议管理系统")
        self.root.geometry("650x750")

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', font=('Helvetica', 12), padding=10)
        self.style.configure('TLabel', font=('Helvetica', 12))
        self.style.configure('Header.TLabel', font=('Helvetica', 16, 'bold'))

        self.create_widgets()
        self.protocol = ChainDelayProtocol()
        self.protocol.update_callback = self.update_formula_status_bar
        self.update_formula_status_bar()
        self.check_for_inactive_formulas()

        # Initialize countdown timer variables
        self.countdown_label = None
        self.countdown_active = False
        self.countdown_end_time = None
        self.countdown_after_id = None
        

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(expand=True, fill="both")
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        header_label = ttk.Label(main_frame, text="链式时延协议管理系统", style='Header.TLabel')
        header_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # Left side for controls
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="10")
        control_frame.grid(row=1, column=0, sticky="ns", padx=(0, 10))
        control_frame.columnconfigure(0, weight=1)

        # --- Core Actions ---
        ttk.Label(control_frame, text="核心操作", font=('Helvetica', 11, 'bold')).grid(row=0, column=0, sticky='w', pady=(0, 5))
        core_buttons = [
            ("启动预约链", self.start_reservation),
            ("触发神圣座位", self.start_task),
            ("完成任务", self.complete_task),
            ("处理违规", self.handle_violation),
        ]
        for i, (text, command) in enumerate(core_buttons, start=1):
            button = ttk.Button(control_frame, text=text, command=command)
            button.grid(row=i, column=0, sticky="ew", pady=3)

        # --- View Actions ---
        ttk.Separator(control_frame, orient='horizontal').grid(row=len(core_buttons)+1, column=0, sticky='ew', pady=10)
        ttk.Label(control_frame, text="查看", font=('Helvetica', 11, 'bold')).grid(row=len(core_buttons)+2, column=0, sticky='w', pady=(0, 5))
        view_buttons = [
            ("查看状态", self.show_status),
            ("查看允许规则", self.show_allowed_rules),
        ]
        for i, (text, command) in enumerate(view_buttons, start=len(core_buttons)+3):
            button = ttk.Button(control_frame, text=text, command=command)
            button.grid(row=i, column=0, sticky="ew", pady=3)

        # --- Management Actions ---
        ttk.Separator(control_frame, orient='horizontal').grid(row=len(core_buttons)+len(view_buttons)+3, column=0, sticky='ew', pady=10)
        ttk.Label(control_frame, text="管理", font=('Helvetica', 11, 'bold')).grid(row=len(core_buttons)+len(view_buttons)+4, column=0, sticky='w', pady=(0, 5))
        manage_buttons = [
            ("管理定式", self.open_formula_manager),
            ("执行下一层", self.execute_next_formula_level),
        ]
        for i, (text, command) in enumerate(manage_buttons, start=len(core_buttons)+len(view_buttons)+5):
            button = ttk.Button(control_frame, text=text, command=command)
            button.grid(row=i, column=0, sticky="ew", pady=3)

        # Right side for log
        log_frame = ttk.LabelFrame(main_frame, text="系统日志", padding="10")
        log_frame.grid(row=1, column=1, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state='disabled', font=('Consolas', 10))
        self.log_text.grid(row=0, column=0, sticky="nsew")

        # Bottom area for active formulas status
        active_formulas_frame = ttk.LabelFrame(main_frame, text="活跃定式状态", padding="10")
        active_formulas_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        active_formulas_frame.columnconfigure(0, weight=1)

        self.formula_status_bar = ttk.Label(active_formulas_frame, text="---", wraplength=450, justify="left")
        self.formula_status_bar.grid(row=0, column=0, sticky="ew")


        sys.stdout = TextRedirector(self.log_text)

    def show_status(self):
        self.protocol.show_status()


    def show_allowed_rules(self):
        self.protocol.show_allowed_violations()

    def start_reservation(self):
        dialog = InputDialog(self.root, "启动预约链", ["预约时间(分):"])
        if dialog.result:
            try:
                minutes_str = dialog.result["预约时间(分):"]
                minutes = int(minutes_str) if minutes_str else None
                if self.protocol.start_reservation(minutes):
                    self.start_countdown(minutes if minutes is not None else self.protocol.data["settings"]["reservation_minutes"])
            except ValueError:
                messagebox.showerror("错误", "分钟数必须是有效的数字")

    def start_task(self):
        dialog = InputDialog(self.root, "触发神圣座位", ["任务时间(分):", "任务名称:"])
        if dialog.result:
            try:
                minutes_str = dialog.result["任务时间(分):"]
                minutes = int(minutes_str) if minutes_str else None
                task_name = dialog.result["任务名称:"] or None
                if self.protocol.start_task(minutes, task_name):
                    self.start_countdown(minutes if minutes is not None else self.protocol.data["settings"]["task_minutes"])
            except ValueError:
                messagebox.showerror("错误", "分钟数必须是有效的数字")

    def complete_task(self):
        if self.protocol.complete_task():
            self.stop_countdown()

    def handle_violation(self):
        message = "如何处理本次违规？"
        button_texts = ["任务失败", "添加例外"]
        
        dialog = CustomChoiceDialog(
            self.root, 
            "处理违规", 
            message, 
            button_texts, 
            show_input=True, 
            input_prompt="违规说明:"
        )

        choice = dialog.result
        description = dialog.input_text

        if choice == "任务失败":
            self.protocol.reset_chain(description)
            self.stop_countdown()
            messagebox.showinfo("操作成功", f"任务链已因‘{description}’重置。")
        elif choice == "添加例外":
            self.protocol.allow_violation(description)
            messagebox.showinfo("操作成功", f"已将‘{description}’添加为例外规则。")

    def open_formula_manager(self):
        FormulaManagerGUI(self.root, self.protocol.formula_manager)

    def update_formula_status_bar(self):
        """更新定式状态栏"""
        display_text = self.protocol.formula_manager.get_active_formulas_display()
        if not display_text:
            display_text = "当前无活跃定式。"
        self.formula_status_bar.config(text=display_text)

    def execute_next_formula_level(self):
        """执行选定的活跃定式树的下一层"""
        active_trees = self.protocol.formula_manager.active_tree_progress
        if not active_trees:
            messagebox.showinfo("提示", "当前没有活跃的定式树。", parent=self.root)
            return

        choices = []
        for root_id in active_trees.keys():
            formula = self.protocol.formula_manager.get_formula_by_id(root_id)
            if formula:
                choices.append(f"{formula.get('name', f'ID: {root_id}')} (ID: {root_id})")

        dialog = CustomChoiceDialog(self.root, "选择定式树", "请选择要执行下一层的定式树：", choices)
        choice = dialog.result
        
        if choice:
            selected_id = int(choice.split('(ID: ')[1][:-1])
            completed = self.protocol.formula_manager.execute_next_level(selected_id)
            
            formula_name = self.protocol.formula_manager.get_formula_by_id(selected_id).get('name')
            if completed:
                messagebox.showinfo("操作成功", f"定式树 '{formula_name}' 已完成一轮，重置到初始层级。", parent=self.root)
            else:
                messagebox.showinfo("操作成功", f"定式树 '{formula_name}' 已推进到下一层。", parent=self.root)
            

    def check_for_inactive_formulas(self):
        inactive_list = self.protocol.formula_manager.check_inactive_formulas()
        if inactive_list:
            message = "以下定式已超过一周未激活，请考虑激活或删除：\n\n" + "\n".join(inactive_list)
            messagebox.showwarning("不活跃定式警告", message, parent=self.root)

    def start_countdown(self, minutes):
        if self.countdown_label is None:
            self.countdown_label = ttk.Label(self.root, text="", font=("Helvetica", 12, "bold"))
            self.countdown_label.place(relx=1.0, rely=1.0, x=-10, y=-10, anchor="se")

        self.countdown_end_time = time.time() + minutes * 60
        self.countdown_active = True
        self.update_countdown()

    def update_countdown(self):
        if not self.countdown_active:
            return

        remaining_seconds = self.countdown_end_time - time.time()
        if remaining_seconds > 0:
            mins, secs = divmod(int(remaining_seconds), 60)
            self.countdown_label.config(text=f"倒计时: {mins:02d}:{secs:02d}")
            self.countdown_after_id = self.root.after(1000, self.update_countdown)
        else:
            self.stop_countdown()

    def stop_countdown(self):
        self.countdown_active = False
        if self.countdown_label:
            self.countdown_label.config(text="")
            self.countdown_label.place_forget()
            self.countdown_label = None
        if self.countdown_after_id:
            self.root.after_cancel(self.countdown_after_id)
            self.countdown_after_id = None

if __name__ == "__main__":
    root = tk.Tk()
    app = ChainDelayProtocolGUI(root)
    root.mainloop()

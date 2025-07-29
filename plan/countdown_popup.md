[MODE: PLAN]

# 倒计时弹窗改造技术规格

## 目标
将当前右下角 `ttk.Label` 形式的倒计时改造为独立弹窗 (`tk.Toplevel`)，并实现以下特性：
1. 弹窗始终置顶于所有应用最上层（`topmost`）。
2. 弹窗尺寸尽量小，仅显示倒计时时间文本，例如 `00:59`。
3. 关闭逻辑保持不变：当倒计时结束或调用 `stop_countdown()` 时自动关闭。
4. 不影响现有业务逻辑与状态变量（`countdown_active`, `countdown_end_time`, 等）。

## 涉及文件
- `ui_main.py`

## 数据结构与变量调整
| 名称 | 类型 | 说明 |
| ---- | ---- | ---- |
| `self.countdown_window` | `tk.Toplevel` or `None` | 倒计时弹窗窗口实例。|
| `self.countdown_label` | `ttk.Label` | 位于弹窗内部，用于显示时间。|
| 其余现有变量 | 同原来 | 无需改动。|

## 详细修改点
1. **新增属性**：在 `__init__` 初始化 `self.countdown_window = None`。
2. **start_countdown(minutes)**
   - 若 `self.countdown_window is None`，创建 `tk.Toplevel(self.root)`。
   - 设置：
     ```python
     win = tk.Toplevel(self.root)
     win.overrideredirect(True)      # 无标题栏
     win.attributes("-topmost", True)
     win.resizable(False, False)
     ```
   - 计算合适的宽高（如 80x30），使用 `geometry` 定位到屏幕右下角（可复用现有 `root.winfo_screenwidth/height` 计算）。
   - 创建内部 `ttk.Label`, 赋给 `self.countdown_label`, `pack(expand=True)`。
3. **update_countdown()**
   - 逻辑保持不变，只是调用 `self.countdown_label.config(text=...)` 更新弹窗文本。
4. **stop_countdown()**
   - 在销毁标签前先 `self.countdown_window.destroy()` 并置 `self.countdown_window=None`。
   - 其余 `after_cancel` 保持。
5. **退出/主程序销毁**：在 `on_close` 或主窗口关闭时，若 `countdown_window` 存在也需销毁，避免残留。

## 兼容性 & UX
- 使用 `overrideredirect(True)` 去掉边框保证最小化尺寸。
- 置顶属性在 Windows、macOS、Linux 普遍可用。
- 设置黑色背景+白色字体（可选）提高可读性。

---
IMPLEMENTATION CHECKLIST:
1. 在 `ui_main.py` 的 `ChainDelayProtocolGUI.__init__` 中添加 `self.countdown_window = None`。
2. 修改 `start_countdown()`：创建并配置 `Toplevel` 弹窗；内部生成 `ttk.Label`；定位到右下。
3. 修改 `update_countdown()`：继续刷新 `self.countdown_label` 文本。
4. 修改 `stop_countdown()`：关闭 `after` 事件，销毁 `countdown_window`，清理变量。
5. 测试：启动预约/任务，确认弹窗始终置顶显示；手动或计时结束后弹窗自动关闭。
6. 代码检查与格式化。

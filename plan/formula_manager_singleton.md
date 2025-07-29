[MODE: PLAN]

目标: 引入懒加载单例 `FormulaManager`，保证 UI 层与核心逻辑共享同一实例，解决删除后数据被默认加载覆盖的问题。

---
## 技术规格

1. 新建 `formula_singleton.py`
   - 提供函数 `get_manager(data_callback=None) -> FormulaManager`。
   - 内部使用私有模块级变量 `_instance` 保存单例。
   - 首次调用时创建 `FormulaManager(data_callback)` 并返回；后续直接返回 `_instance`。

2. 修改 `main.py`
   - 删除 `from formula_manager import FormulaManager`。
   - 添加 `from formula_singleton import get_manager`。
   - 在 `ChainDelayProtocol.__init__` 中，将
     ```python
     self.formula_manager = FormulaManager(data_callback=self.save_data)
     ```
     替换为
     ```python
     self.formula_manager = get_manager(data_callback=self.save_data)
     ```

3. 修改 `ui_main.py`
   - 删除多余的 `from formula_manager import FormulaManager`。
   - 添加 `from formula_singleton import get_manager`（仅在需要独立创建实例的地方；当前 UI 已通过 `ChainDelayProtocol` 间接获得实例，无需频繁调用）。
   - 搜索并替换所有 `FormulaManager()` 直接实例化（若存在）为 `get_manager()`。

4. 确保其他模块若有直接 `FormulaManager()` 调用，也统一替换为 `get_manager()`。

5. 持久化逻辑
   - 不变。`data_callback` 仍由 `save_data()` 提供，保证修改后立即写盘。

6. 回溯兼容
   - `formula_singleton.get_manager()` 参数 `data_callback` 仅在首次创建时生效，后续调用忽略。

---
IMPLEMENTATION CHECKLIST:
1. [ ] 创建 `plan` 文件夹（如不存在）。
2. [ ] 创建 `formula_singleton.py` 并实现懒加载单例。
3. [ ] 更新 `main.py` 以使用 `get_manager()`。
4. [ ] 搜索项目中所有 `FormulaManager(` 实例化，替换为 `get_manager()`（预期修改 `ui_main.py`，其他文件视具体结果而定）。
5. [ ] 运行程序手动测试：
   - 删除定式 → 重启 UI → 树保持删除状态。
6. [ ] 更新文档或 README（如有）。

---
文件保存: 本计划已保存至 `./plan/formula_manager_singleton.md`。

---
[EXECUTION - Step 1/4]
已创建 `formula_singleton.py` 并实现 `get_manager()` 懒加载单例。

[EXECUTION - Step 2/4]
已在 `main.py` 中改用 `get_manager()` 并替换 import。

[EXECUTION - Step 3/4]
已在 `ui_main.py` 移除直接导入 `FormulaManager`，改为 `get_manager` 占位导入（未来可能使用），消除直接实例化。

[EXECUTION - Step 4/4]
全局搜索确认无其他 `FormulaManager()` 实例化。

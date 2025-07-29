"""FormulaManager 懒加载单例模块

使用 get_manager() 获取全局唯一的 FormulaManager 实例。
首次调用可传入 data_callback，用于持久化。
后续调用忽略 data_callback 参数，直接返回已创建的实例。
"""
from typing import Optional, Callable, Any

from formula_manager import FormulaManager

# 私有单例实例
_instance: Optional[FormulaManager] = None 

def get_manager(data_callback: Optional[Callable[[], Any]] = None) -> FormulaManager:
    """获取 FormulaManager 单例。

    Args:
        data_callback: 首次创建实例时注入的保存回调函数。

    Returns:
        FormulaManager 单例实例。
    """
    global _instance

    if _instance is None:
        _instance = FormulaManager(data_callback=data_callback)
    else:
        # 如果已存在实例，但之前未设置回调，可补充注入
        if data_callback and _instance.data_callback is None:
            _instance.data_callback = data_callback
    return _instance

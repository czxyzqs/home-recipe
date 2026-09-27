"""中国大陆工作日判断（法定节假日 + 调休补班），供周计划生成使用"""
from datetime import date

try:
    from chinese_calendar import is_workday as _cc_is_workday
except ImportError:  # 未安装时退化为周一~周五
    _cc_is_workday = None


def is_workday(d: date) -> bool:
    """判断是否中国大陆工作日；库未安装或年份超出数据范围时退回周一~周五"""
    if _cc_is_workday is not None:
        try:
            return _cc_is_workday(d)
        except NotImplementedError:
            pass
    return d.weekday() < 5

# 11 小时处理
import ztime

t = ztime.utcnow()
print(t.span('hour'))  # 获取到小时
print(t.floor('hour'))  # 移除小时后的时间
print(t.ceil('hour'))  # 最大化小时后的时间

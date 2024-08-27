# 08 获取日期和时间
import ztime

t = ztime.utcnow()
print(t.date())  # 获取日期
print(t.time())  # 获取时间

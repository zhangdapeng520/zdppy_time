# 09 替换指定时间
import ztime

t = ztime.utcnow()
print(t.replace(hour=4, minute=40))  # 替换指定时间

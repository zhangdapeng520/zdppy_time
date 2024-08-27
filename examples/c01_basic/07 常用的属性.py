# 07 常用的属性
import ztime

t = ztime.utcnow()
print(t.naive)
print(t.tzinfo)
print(t.year)
print(t.month)
print(t.day)
print(t.hour)

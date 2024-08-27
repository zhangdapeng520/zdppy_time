# 10 解析人性化时间
import ztime

t = ztime.utcnow()
print(t.dehumanize("2 days ago"))  # 解析人性化时间
print(t.dehumanize("2天前", locale="zh-cn"))  # 解析人性化时间

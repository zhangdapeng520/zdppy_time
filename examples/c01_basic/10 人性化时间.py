# 04 人性化时间

import ztime

utc = ztime.utcnow()
utc = utc.to("local")
print(utc)
print(utc.humanize())
print(utc.humanize(locale="zh-cn"))

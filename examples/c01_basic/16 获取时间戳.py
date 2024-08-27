# 02 获取时间戳

import ztime

utc = ztime.utcnow()
utc = utc.to("local")
print(utc)
print(utc.timestamp())

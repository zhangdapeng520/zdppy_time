# 01 获取当前时间

import ztime

# 获取本地时区的当前时间
print(ztime.now())

# 获取UTC时间，然后转为本地时区的时间
utc = ztime.utcnow()
utc = utc.to("local")
print(utc)

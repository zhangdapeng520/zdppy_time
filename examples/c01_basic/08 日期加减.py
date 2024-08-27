# 05 日期加减

import ztime

utc = ztime.utcnow()
utc = utc.to("local")

utc = utc.shift(hours=-1)
print(utc.humanize(locale="zh-cn"))

utc = utc.shift(days=-1)
print(utc.humanize(locale="zh-cn"))

utc = utc.shift(months=-1)
print(utc.humanize(locale="zh-cn"))

utc = utc.shift(years=-1)
print(utc.humanize(locale="zh-cn"))

utc = utc.shift(years=2)
print(utc.humanize(locale="zh-cn"))

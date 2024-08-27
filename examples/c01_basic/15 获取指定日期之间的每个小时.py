# 12 获取指定日期之间的每个小时
import ztime

from datetime import datetime

start = datetime(2013, 5, 5, 12, 30)
end = datetime(2013, 5, 5, 17, 15)
for r in ztime.ZTime.span_range('hour', start, end):
    print(r)

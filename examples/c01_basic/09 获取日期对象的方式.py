# 06 获取日期对象的方式
from datetime import datetime
import ztime

t = ztime.get(1367900664)
t = ztime.get(1367900664.152325)
t = ztime.get(datetime.utcnow())
t = ztime.get(datetime(2013, 5, 5), "local")
t = ztime.get('2013-05-05 12:30:45', 'YYYY-MM-DD HH:mm:ss')
t = ztime.get(2013, 5, 5)

print(t)

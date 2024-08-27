import ztime

utc = ztime.utcnow()
utc = utc.to("local")
print(utc)
print(utc.format())
print(utc.format("YYYY-MM-DD HH:mm:ss"))

## 更简单的写法
print(ztime.now_str())

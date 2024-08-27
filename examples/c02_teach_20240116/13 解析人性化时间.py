import ztime

s = "1小时前"

zn = ztime.now()
print(zn)

zn2 = zn.dehumanize(s, locale="zh-cn")
print(zn2)

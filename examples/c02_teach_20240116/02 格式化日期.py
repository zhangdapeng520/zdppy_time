from datetime import datetime

dn = datetime.now()
print(dn, type(dn))

s1 = dn.strftime("%Y-%m-%d %H:%M:%S")
print(s1, type(s1))

s2 = dn.strftime("%Y年%m月%d日 %H:%M:%S")
print(s2, type(s2))

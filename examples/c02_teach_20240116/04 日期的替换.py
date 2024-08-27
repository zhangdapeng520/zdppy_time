from datetime import datetime

dn = datetime.now()
print(dn)

d1 = dn.replace(year=2023)
print(d1)

d2 = dn.replace(month=3)
print(d2)

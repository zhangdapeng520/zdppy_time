from datetime import datetime, timedelta

dn = datetime.now()

# +10天
d1 = dn + timedelta(days=10)
print(d1)

# -10天
d2 = dn + timedelta(days=-10)
print(d2)

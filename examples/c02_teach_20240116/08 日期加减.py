import ztime

zn = ztime.now()
print(zn)

zn2 = zn.shift(hours=-1)
print(zn2)

zn3 = zn.shift(hours=1)
print(zn3)

zn4 = zn.shift(years=-1)
print(zn4)
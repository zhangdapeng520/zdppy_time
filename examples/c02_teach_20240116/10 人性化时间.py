import ztime

zn = ztime.now()
print(zn.humanize())

zn1 = zn.shift(hours=-1)
print(zn1.humanize())

zn2 = zn.shift(hours=1)
print(zn2.humanize())

zn3 = zn.shift(days=1)
print(zn3.humanize())

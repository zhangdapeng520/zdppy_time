import ztime

zn = ztime.now()
print(zn)

zn2 = ztime.utcnow()
print(zn2)

zn3 = zn2.to("local")
print(zn3)

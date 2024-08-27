import ztime

zn = ztime.now()

print(zn.naive, type(zn.naive))
print(zn.tzinfo, type(zn.tzinfo))
print(zn.year, type(zn.year))
print(zn.month, type(zn.month))
print(zn.day, type(zn.day))
print(zn.hour, type(zn.hour))
print(zn.minute, type(zn.minute))
print(zn.second, type(zn.second))

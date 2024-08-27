import ztime

zn = ztime.now()
print(zn)

print(zn.span("hour"))
print(zn.floor("hour"))
print(zn.ceil("hour"))

print(zn.span("month"))
print(zn.floor("month"))
print(zn.ceil("month"))

print(zn.span("day"))
print(zn.floor("day"))
print(zn.ceil("day"))

print(zn.span("year"))
print(zn.floor("year"))
print(zn.ceil("year"))

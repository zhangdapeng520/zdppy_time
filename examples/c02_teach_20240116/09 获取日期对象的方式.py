from datetime import datetime
import ztime

zn1 = ztime.now()
print(zn1)

zn2 = ztime.get(1708049404.3171942)
print(zn2)

zn3 = ztime.get(1708040000)
print(zn3)

zn4 = ztime.get(datetime.now())
print(zn4)

zn5 = ztime.get(datetime(2022, 2, 2), "local")
print(zn5)

zn6 = ztime.get(2022, 2, 2)
print(zn6)

zn7 = ztime.get(2022, 2, 2, 11, 11, 11)
zn7 = zn7.to("local")
print(zn7)

zn8 = ztime.get("2022-02-02 11:11:11", "YYYY-MM-DD HH:mm:ss")
zn8 = zn8.to("local")
print(zn8)

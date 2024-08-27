from ztime import dateutil

s1 = "2024-02-16"
s2 = "2024-02-16 09:44:33"
s3 = "2024-02-16T09:44:33"

d1 = dateutil.parser.parse(s1)
print("s1=", s1, type(s1))
print("d1=", d1, type(d1))

d2 = dateutil.parser.parse(s2)
print("s2=", s2, type(s2))
print("d2=", d2, type(d2))

d3 = dateutil.parser.parse(s3)
print("s3=", s3, type(s3))
print("d3=", d3, type(d3))

# 01 解析日期字符串
from ztime import dateutil

date_string = '2022-01-01'
date = dateutil.parser.parse(date_string)
print('Parsed Date:', date)

date_string = '2022-01-01 12:13:14'
date = dateutil.parser.parse(date_string)
print('Parsed Date:', date)

date_string = '2022-01-02T12:13:14'
date = dateutil.parser.parse(date_string)
print('Parsed Date:', date)

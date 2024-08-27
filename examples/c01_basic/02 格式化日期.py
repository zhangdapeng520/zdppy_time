# 02 格式化日期
from ztime import dateutil

date_string = '2022-01-01 11:12:13'
date = dateutil.parser.parse(date_string)
print('Parsed Date:', date)

formatted_date = date.strftime('%Y-%m-%d %H:%M:%S')
print('Formatted Date:', formatted_date)

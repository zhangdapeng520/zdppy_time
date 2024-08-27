# 03 日期的加减
import datetime
from ztime import dateutil

date_string = '2022-01-01 11:12:13'
date = dateutil.parser.parse(date_string)
print('Parsed Date:', date)

# 加上10天
new_date = date + datetime.timedelta(days=10)
formatted_date = new_date.strftime('%Y-%m-%d %H:%M:%S')
print('Formatted Date:', formatted_date)

# 减去10天
new_date = date + datetime.timedelta(days=-10)
formatted_date = new_date.strftime('%Y-%m-%d %H:%M:%S')
print('Formatted Date:', formatted_date)

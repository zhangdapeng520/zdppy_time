# 04 日期的替换
from ztime import dateutil

date_string = '2022-01-01 11:12:13'
date = dateutil.parser.parse(date_string)
print('Parsed Date:', date)

# 替换年份为2023
# 其他参数：year,month,day,hour,minute,second,microsecond,tzinfo
new_date = date.replace(year=2023)
formatted_date = new_date.strftime('%Y-%m-%d %H:%M:%S')
print('Formatted Date:', formatted_date)

new_date = date.replace(hour=23)
formatted_date = new_date.strftime('%Y-%m-%d %H:%M:%S')
print('Formatted Date:', formatted_date)

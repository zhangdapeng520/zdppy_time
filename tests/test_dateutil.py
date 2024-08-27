import unittest
import datetime
from ztime import dateutil


class TestDateutil(unittest.TestCase):
    def test_parse(self):
        """测试解析日期字符串"""
        date_string = '2022-01-01'
        date = dateutil.parser.parse(date_string)
        print('Parsed Date:', date)

    def test_format(self):
        date_string = '2022-01-01'
        date = dateutil.parser.parse(date_string)
        formatted_date = date.strftime('%Y-%m-%d')
        print('Formatted Date:', formatted_date)

    def test_add(self):
        date_string = '2022-01-01'
        date = dateutil.parser.parse(date_string)
        # 加上10天
        new_date = date + datetime.timedelta(days=10)
        print('New Date:', new_date.strftime('%Y-%m-%d'))

    def test_replace(self):
        date_string = '2022-01-01'
        date = dateutil.parser.parse(date_string)
        # 替换年份为2023
        new_date = date.replace(year=2023)
        print('New Date:', new_date.strftime('%Y-%m-%d'))

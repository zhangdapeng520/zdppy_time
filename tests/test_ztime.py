import unittest
import ztime


class TestZTime(unittest.TestCase):
    def test_now(self):
        utc = ztime.utcnow()
        utc = utc.to("local")
        print(utc)

    def test_timestamp(self):
        utc = ztime.utcnow()
        utc = utc.to("local")
        print(utc)
        print(utc.timestamp())

    def test_format(self):
        utc = ztime.utcnow()
        utc = utc.to("local")
        print(utc)
        print(utc.format("YYYY-MM-DD HH:mm:ss"))

    def test_humanize(self):
        utc = ztime.utcnow()
        utc = utc.to("local")
        print(utc)
        print(utc.humanize())
        print(utc.humanize(locale="zh-cn"))

    def test_now2(self):
        print(ztime.now())
        print(ztime.now('US/Pacific'))
        print(ztime.now('+02:00'))
        print(ztime.now('local'))

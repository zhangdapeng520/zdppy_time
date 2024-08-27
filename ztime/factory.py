import calendar
from datetime import date, datetime
from datetime import tzinfo as dt_tzinfo
from decimal import Decimal
from time import struct_time
from typing import Any, List, Optional, Tuple, Type, Union, overload

from .dateutil import tz as dateutil_tz

from . import parser
from .ztime import ZTime
from .constants import DEFAULT_LOCALE
from .util import is_timestamp, iso_to_gregorian


class ZTimeFactory:
    """
    工厂类
    :param type: 类型
    """

    type: Type[ZTime]

    def __init__(self, type: Type[ZTime] = ZTime) -> None:
        self.type = type

    @overload
    def get(
            self,
            *,
            locale=DEFAULT_LOCALE,
            tzinfo=None,
            normalize_whitespace=False,
    ):
        ...  # pragma: no cover

    @overload
    def get(
            self,
            __obj,
            *,
            locale=DEFAULT_LOCALE,
            tzinfo=None,
            normalize_whitespace=False,
    ):
        ...  # pragma: no cover

    @overload
    def get(
            self,
            __arg1,
            __arg2,
            *,
            locale=DEFAULT_LOCALE,
            tzinfo=None,
            normalize_whitespace=False,
    ):
        ...  # pragma: no cover

    @overload
    def get(
            self,
            __arg1,
            __arg2,
            *,
            locale=DEFAULT_LOCALE,
            tzinfo=None,
            normalize_whitespace=False,
    ):
        ...  # pragma: no cover

    def get(self, *args, **kwargs):
        """
        获取ZTime对象
        :param locale: 地区默认 'en-us'.
        :param tzinfo: 时区，默认 UTC.
        :param normalize_whitespace: 默认false
            arw = arrow.utcnow()
            arrow.get(arw)
            arrow.get(1367992474.293378)
            arrow.get(1367992474)
            arrow.get('2013-09-29T01:26:43.830580')
            arrow.get('20160413T133656.456289')
            arrow.get(tz.tzlocal())
            arrow.get(datetime(2013, 5, 5))
            arrow.get(datetime(2013, 5, 5, tzinfo=tz.tzlocal()))
            arrow.get(date(2013, 5, 5))
            arrow.get(gmtime(0))
            arrow.get((2013, 18, 7))
            arrow.get(datetime(2013, 5, 5), 'US/Pacific')
            arrow.get(date(2013, 5, 5), 'US/Pacific')
            arrow.get('2013-05-05 12:30:45 America/Chicago', 'YYYY-MM-DD HH:mm:ss ZZZ')
            arrow.get('2013-05-05 12:30:45', ['MM/DD/YYYY', 'YYYY-MM-DD HH:mm:ss'])
            arrow.get(2013, 5, 5, 12, 30, 45)
        """

        arg_count = len(args)
        locale = kwargs.pop("locale", DEFAULT_LOCALE)
        tz = kwargs.get("tzinfo", None)
        normalize_whitespace = kwargs.pop("normalize_whitespace", False)

        # if kwargs given, send to constructor unless only tzinfo provided
        if len(kwargs) > 1:
            arg_count = 3

        # tzinfo kwarg is not provided
        if len(kwargs) == 1 and tz is None:
            arg_count = 3

        # () -> now, @ tzinfo or utc
        if arg_count == 0:
            if isinstance(tz, str):
                tz = parser.TzinfoParser.parse(tz)
                return self.type.now(tzinfo=tz)

            if isinstance(tz, dt_tzinfo):
                return self.type.now(tzinfo=tz)

            return self.type.utcnow()

        if arg_count == 1:
            arg = args[0]
            if isinstance(arg, Decimal):
                arg = float(arg)

            # (None) -> raises an exception
            if arg is None:
                raise TypeError("Cannot parse argument of type None.")

            # try (int, float) -> from timestamp @ tzinfo
            elif not isinstance(arg, str) and is_timestamp(arg):
                if tz is None:
                    # set to UTC by default
                    tz = dateutil_tz.tzutc()
                return self.type.fromtimestamp(arg, tzinfo=tz)

            # (ZTime) -> from the object's datetime @ tzinfo
            elif isinstance(arg, ZTime):
                return self.type.fromdatetime(arg.datetime, tzinfo=tz)

            # (datetime) -> from datetime @ tzinfo
            elif isinstance(arg, datetime):
                return self.type.fromdatetime(arg, tzinfo=tz)

            # (date) -> from date @ tzinfo
            elif isinstance(arg, date):
                return self.type.fromdate(arg, tzinfo=tz)

            # (tzinfo) -> now @ tzinfo
            elif isinstance(arg, dt_tzinfo):
                return self.type.now(tzinfo=arg)

            # (str) -> parse @ tzinfo
            elif isinstance(arg, str):
                dt = parser.DateTimeParser(locale).parse_iso(arg, normalize_whitespace)
                return self.type.fromdatetime(dt, tzinfo=tz)

            # (struct_time) -> from struct_time
            elif isinstance(arg, struct_time):
                return self.type.utcfromtimestamp(calendar.timegm(arg))

            # (iso calendar) -> convert then from date @ tzinfo
            elif isinstance(arg, tuple) and len(arg) == 3:
                d = iso_to_gregorian(*arg)
                return self.type.fromdate(d, tzinfo=tz)

            else:
                raise TypeError(f"Cannot parse single argument of type {type(arg)!r}.")

        elif arg_count == 2:
            arg_1, arg_2 = args[0], args[1]

            if isinstance(arg_1, datetime):
                # (datetime, tzinfo/str) -> fromdatetime @ tzinfo
                if isinstance(arg_2, (dt_tzinfo, str)):
                    return self.type.fromdatetime(arg_1, tzinfo=arg_2)
                else:
                    raise TypeError(
                        f"Cannot parse two arguments of types 'datetime', {type(arg_2)!r}."
                    )

            elif isinstance(arg_1, date):
                # (date, tzinfo/str) -> fromdate @ tzinfo
                if isinstance(arg_2, (dt_tzinfo, str)):
                    return self.type.fromdate(arg_1, tzinfo=arg_2)
                else:
                    raise TypeError(
                        f"Cannot parse two arguments of types 'date', {type(arg_2)!r}."
                    )

            # (str, format) -> parse @ tzinfo
            elif isinstance(arg_1, str) and isinstance(arg_2, (str, list)):
                dt = parser.DateTimeParser(locale).parse(
                    args[0], args[1], normalize_whitespace
                )
                return self.type.fromdatetime(dt, tzinfo=tz)

            else:
                raise TypeError(
                    f"Cannot parse two arguments of types {type(arg_1)!r} and {type(arg_2)!r}."
                )

        # 3+ args -> datetime-like via constructor
        else:
            return self.type(*args, **kwargs)

    def utcnow(self) -> ZTime:
        """
        获取基于UTC的当前时间
        """
        return self.type.utcnow()

    def now(self, tz=None):
        """
        获取当前时间.
        :param tz: 时区，默认local.
            arrow.now()
            arrow.now('US/Pacific')
            arrow.now('+02:00')
            arrow.now('local')
        """

        if tz is None:
            tz = dateutil_tz.tzlocal()
        elif not isinstance(tz, dt_tzinfo):
            tz = parser.TzinfoParser.parse(tz)

        return self.type.now(tz)

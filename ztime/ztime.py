import calendar
import re
import sys
from datetime import date
from datetime import datetime as dt_datetime
from datetime import time as dt_time
from datetime import timedelta
from datetime import tzinfo as dt_tzinfo
from math import trunc
from time import struct_time
from typing import (
    Any,
    ClassVar,
    Generator,
    Iterable,
    List,
    Mapping,
    Optional,
    Tuple,
    Union,
    cast,
    overload,
)

from .dateutil import tz as dateutil_tz
from .dateutil.relativedelta import relativedelta
from . import formatter, parser, util
from . import locales
from .constants import DEFAULT_LOCALE, DEHUMANIZE_LOCALES
from .locales import TimeFrameLiteral

# 日期格式
_T_FRAMES = [
    "year",
    "years",
    "month",
    "months",
    "day",
    "days",
    "hour",
    "hours",
    "minute",
    "minutes",
    "second",
    "seconds",
    "microsecond",
    "microseconds",
    "week",
    "weeks",
    "quarter",
    "quarters",
]

_BOUNDS = ["[)", "()", "(]", "[]"]

# 用于增长的单位
_GRANULARITY = [
    "auto",
    "second",
    "minute",
    "hour",
    "day",
    "week",
    "month",
    "quarter",
    "year",
]


class ZTime:
    """
    日期时间类
    :param year: 年
    :param month: 月
    :param day: 日
    :param hour: 时
    :param minute: 分
    :param second: 秒
    :param microsecond: 微妙
    :param tzinfo: 时区
    :param fold: 用于消除重复的墙壁次数
    """

    resolution: ClassVar[timedelta] = dt_datetime.resolution
    min: ClassVar["ZTime"]
    max: ClassVar["ZTime"]

    _ATTRS = [
        "year",
        "month",
        "day",
        "hour",
        "minute",
        "second",
        "microsecond",
    ]
    _ATTRS_PLURAL = [f"{a}s" for a in _ATTRS]
    _MONTHS_PER_QUARTER = 3
    _SECS_PER_MINUTE = 60
    _SECS_PER_HOUR = 60 * 60
    _SECS_PER_DAY = 60 * 60 * 24
    _SECS_PER_WEEK = 60 * 60 * 24 * 7
    _SECS_PER_MONTH = 60 * 60 * 24 * 30.5
    _SECS_PER_QUARTER = 60 * 60 * 24 * 30.5 * 3
    _SECS_PER_YEAR = 60 * 60 * 24 * 365

    _SECS_MAP = {
        "second": 1.0,
        "minute": _SECS_PER_MINUTE,
        "hour": _SECS_PER_HOUR,
        "day": _SECS_PER_DAY,
        "week": _SECS_PER_WEEK,
        "month": _SECS_PER_MONTH,
        "quarter": _SECS_PER_QUARTER,
        "year": _SECS_PER_YEAR,
    }

    _datetime: dt_datetime

    def __init__(
            self,
            year: int,
            month: int,
            day: int,
            hour: int = 0,
            minute: int = 0,
            second: int = 0,
            microsecond: int = 0,
            tzinfo=None,
            **kwargs: Any,
    ) -> None:
        if tzinfo is None:
            tzinfo = dateutil_tz.tzutc()
        # detect that tzinfo is a pytz object (issue #626)
        elif (
                isinstance(tzinfo, dt_tzinfo)
                and hasattr(tzinfo, "localize")
                and hasattr(tzinfo, "zone")
                and tzinfo.zone
        ):
            tzinfo = parser.TzinfoParser.parse(tzinfo.zone)
        elif isinstance(tzinfo, str):
            tzinfo = parser.TzinfoParser.parse(tzinfo)

        fold = kwargs.get("fold", 0)

        self._datetime = dt_datetime(
            year, month, day, hour, minute, second, microsecond, tzinfo, fold=fold
        )

    # factories: single object, both original and from datetime.

    @classmethod
    def now(cls, tzinfo=None):
        """
        获取当前时间
        :param tzinfo: 时区，比如local
        """

        if tzinfo is None:
            tzinfo = dateutil_tz.tzlocal()

        dt = dt_datetime.now(tzinfo)

        return cls(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            dt.tzinfo,
            fold=getattr(dt, "fold", 0),
        )

    @classmethod
    def utcnow(cls):
        """
        获取当前时间
        """

        dt = dt_datetime.now(dateutil_tz.tzutc())

        return cls(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            dt.tzinfo,
            fold=getattr(dt, "fold", 0),
        )

    @classmethod
    def fromtimestamp(
            cls,
            timestamp,
            tzinfo=None,
    ):
        """
        通过时间戳创建日期对象
        :param timestamp: 时间戳
        :param tzinfo: 时区
        """

        if tzinfo is None:
            tzinfo = dateutil_tz.tzlocal()
        elif isinstance(tzinfo, str):
            tzinfo = parser.TzinfoParser.parse(tzinfo)

        if not util.is_timestamp(timestamp):
            raise ValueError(f"The provided timestamp {timestamp!r} is invalid.")

        timestamp = util.normalize_timestamp(float(timestamp))
        dt = dt_datetime.fromtimestamp(timestamp, tzinfo)

        return cls(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            dt.tzinfo,
            fold=getattr(dt, "fold", 0),
        )

    @classmethod
    def utcfromtimestamp(cls, timestamp):
        """
        根据时间戳生成UTC时间
        :param timestamp: 时间戳
        """

        if not util.is_timestamp(timestamp):
            raise ValueError(f"The provided timestamp {timestamp!r} is invalid.")

        timestamp = util.normalize_timestamp(float(timestamp))
        dt = dt_datetime.utcfromtimestamp(timestamp)

        return cls(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            dateutil_tz.tzutc(),
            fold=getattr(dt, "fold", 0),
        )

    @classmethod
    def fromdatetime(cls, dt, tzinfo=None):
        """
        根据datetime日期时间对象生成ZTime对象
        :param dt: datetime日期时间对象
        :param tzinfo: 时区，比如local
        """

        if tzinfo is None:
            if dt.tzinfo is None:
                tzinfo = dateutil_tz.tzutc()
            else:
                tzinfo = dt.tzinfo

        return cls(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            tzinfo,
            fold=getattr(dt, "fold", 0),
        )

    @classmethod
    def fromdate(cls, date, tzinfo=None):
        """
        根据date日期对象生成ZTime对象
        :param date: date日期对象
        :param tzinfo: 时区，默认使用UTC，可以使用local等
        """

        if tzinfo is None:
            tzinfo = dateutil_tz.tzutc()
        return cls(date.year, date.month, date.day, tzinfo=tzinfo)

    @classmethod
    def strptime(
            cls,
            date_str,
            fmt,
            tzinfo=None
    ):
        """
        格式化日期字符串
        :param date_str: 日期字符串
        :param fmt: 日期格式化字符串
        :param tzinfo: 时区
        :return ZTime对象
        ztime.ZTime.strptime('20-01-2019 15:49:10', '%d-%m-%Y %H:%M:%S')
        """

        dt = dt_datetime.strptime(date_str, fmt)
        if tzinfo is None:
            tzinfo = dt.tzinfo

        return cls(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            tzinfo,
            fold=getattr(dt, "fold", 0),
        )

    @classmethod
    def fromordinal(cls, ordinal):
        """
        使用一个序数生成ZTime对象
        :param ordinal: 与格列高利序数相对应的' ' int ' '。
        :return ZTime对象
        ztime.fromordinal(737741)
        """

        util.validate_ordinal(ordinal)
        dt = dt_datetime.fromordinal(ordinal)
        return cls(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            dt.tzinfo,
            fold=getattr(dt, "fold", 0),
        )

    @classmethod
    def range(
            cls,
            frame,
            start,
            end=None,
            tz=None,
            limit=None,
    ):
        """
        返回start和end之间的时间序列
        :param frame: 日期格式，可以是day, hour, minute等
        :param start: 开始时间，是一个datetime对象
        :param end: 结束时间，是一个datetime对象
        :param tz: 时区
        :param limit: 限制返回的个数，默认不限制
        Supported frame values: year, quarter, month, week, day, hour, minute, second, microsecond.

        Recognized datetime expressions:

            - An :class:`ZTime <arrow.arrow.ZTime>` object.
            - A ``datetime`` object.

        Usage::

            >>> start = datetime(2013, 5, 5, 12, 30)
            >>> end = datetime(2013, 5, 5, 17, 15)
            >>> for r in arrow.ZTime.range('hour', start, end):
            ...     print(repr(r))
            ...
            <ZTime [2013-05-05T12:30:00+00:00]>
            <ZTime [2013-05-05T13:30:00+00:00]>
            <ZTime [2013-05-05T14:30:00+00:00]>
            <ZTime [2013-05-05T15:30:00+00:00]>
            <ZTime [2013-05-05T16:30:00+00:00]>

        **NOTE**: Unlike Python's ``range``, ``end`` *may* be included in the returned iterator::

            >>> start = datetime(2013, 5, 5, 12, 30)
            >>> end = datetime(2013, 5, 5, 13, 30)
            >>> for r in arrow.ZTime.range('hour', start, end):
            ...     print(repr(r))
            ...
            <ZTime [2013-05-05T12:30:00+00:00]>
            <ZTime [2013-05-05T13:30:00+00:00]>

        """

        _, frame_relative, relative_steps = cls._get_frames(frame)

        tzinfo = cls._get_tzinfo(start.tzinfo if tz is None else tz)

        start = cls._get_datetime(start).replace(tzinfo=tzinfo)
        end, limit = cls._get_iteration_params(end, limit)
        end = cls._get_datetime(end).replace(tzinfo=tzinfo)

        current = cls.fromdatetime(start)
        original_day = start.day
        day_is_clipped = False
        i = 0

        while current <= end and i < limit:
            i += 1
            yield current

            values = [getattr(current, f) for f in cls._ATTRS]
            current = cls(*values, tzinfo=tzinfo).shift(  # type: ignore[misc]
                **{frame_relative: relative_steps}
            )

            if frame in ["month", "quarter", "year"] and current.day < original_day:
                day_is_clipped = True

            if day_is_clipped and not cls._is_last_day_of_month(current):
                current = current.replace(day=original_day)

    def span(
            self,
            frame: _T_FRAMES,
            count: int = 1,
            bounds: _BOUNDS = "[)",
            exact: bool = False,
            week_start: int = 1,
    ) -> Tuple["ZTime", "ZTime"]:
        """Returns a tuple of two new :class:`ZTime <arrow.arrow.ZTime>` objects, representing the timespan
        of the :class:`ZTime <arrow.arrow.ZTime>` object in a given timeframe.

        :param frame: the timeframe.  Can be any ``datetime`` property (day, hour, minute...).
        :param count: (optional) the number of frames to span.
        :param bounds: (optional) a ``str`` of either '()', '(]', '[)', or '[]' that specifies
            whether to include or exclude the start and end values in the span. '(' excludes
            the start, '[' includes the start, ')' excludes the end, and ']' includes the end.
            If the bounds are not specified, the default bound '[)' is used.
        :param exact: (optional) whether to have the start of the timespan begin exactly
            at the time specified by ``start`` and the end of the timespan truncated
            so as not to extend beyond ``end``.
        :param week_start: (optional) only used in combination with the week timeframe. Follows isoweekday() where
            Monday is 1 and Sunday is 7.

        Supported frame values: year, quarter, month, week, day, hour, minute, second.

        Usage::

            >>> arrow.utcnow()
            <ZTime [2013-05-09T03:32:36.186203+00:00]>

            >>> arrow.utcnow().span('hour')
            (<ZTime [2013-05-09T03:00:00+00:00]>, <ZTime [2013-05-09T03:59:59.999999+00:00]>)

            >>> arrow.utcnow().span('day')
            (<ZTime [2013-05-09T00:00:00+00:00]>, <ZTime [2013-05-09T23:59:59.999999+00:00]>)

            >>> arrow.utcnow().span('day', count=2)
            (<ZTime [2013-05-09T00:00:00+00:00]>, <ZTime [2013-05-10T23:59:59.999999+00:00]>)

            >>> arrow.utcnow().span('day', bounds='[]')
            (<ZTime [2013-05-09T00:00:00+00:00]>, <ZTime [2013-05-10T00:00:00+00:00]>)

            >>> arrow.utcnow().span('week')
            (<ZTime [2021-02-22T00:00:00+00:00]>, <ZTime [2021-02-28T23:59:59.999999+00:00]>)

            >>> arrow.utcnow().span('week', week_start=6)
            (<ZTime [2021-02-20T00:00:00+00:00]>, <ZTime [2021-02-26T23:59:59.999999+00:00]>)

        """
        if not 1 <= week_start <= 7:
            raise ValueError("week_start argument must be between 1 and 7.")

        util.validate_bounds(bounds)

        frame_absolute, frame_relative, relative_steps = self._get_frames(frame)

        if frame_absolute == "week":
            attr = "day"
        elif frame_absolute == "quarter":
            attr = "month"
        else:
            attr = frame_absolute

        floor = self
        if not exact:
            index = self._ATTRS.index(attr)
            frames = self._ATTRS[: index + 1]

            values = [getattr(self, f) for f in frames]

            for _ in range(3 - len(values)):
                values.append(1)

            floor = self.__class__(*values, tzinfo=self.tzinfo)  # type: ignore[misc]

            if frame_absolute == "week":
                # if week_start is greater than self.isoweekday() go back one week by setting delta = 7
                delta = 7 if week_start > self.isoweekday() else 0
                floor = floor.shift(days=-(self.isoweekday() - week_start) - delta)
            elif frame_absolute == "quarter":
                floor = floor.shift(months=-((self.month - 1) % 3))

        ceil = floor.shift(**{frame_relative: count * relative_steps})

        if bounds[0] == "(":
            floor = floor.shift(microseconds=+1)

        if bounds[1] == ")":
            ceil = ceil.shift(microseconds=-1)

        return floor, ceil

    def floor(self, frame: _T_FRAMES) -> "ZTime":
        """Returns a new :class:`ZTime <arrow.arrow.ZTime>` object, representing the "floor"
        of the timespan of the :class:`ZTime <arrow.arrow.ZTime>` object in a given timeframe.
        Equivalent to the first element in the 2-tuple returned by
        :func:`span <arrow.arrow.ZTime.span>`.

        :param frame: the timeframe.  Can be any ``datetime`` property (day, hour, minute...).

        Usage::

            >>> arrow.utcnow().floor('hour')
            <ZTime [2013-05-09T03:00:00+00:00]>

        """

        return self.span(frame)[0]

    def ceil(self, frame: _T_FRAMES) -> "ZTime":
        """Returns a new :class:`ZTime <arrow.arrow.ZTime>` object, representing the "ceiling"
        of the timespan of the :class:`ZTime <arrow.arrow.ZTime>` object in a given timeframe.
        Equivalent to the second element in the 2-tuple returned by
        :func:`span <arrow.arrow.ZTime.span>`.

        :param frame: the timeframe.  Can be any ``datetime`` property (day, hour, minute...).

        Usage::

            >>> arrow.utcnow().ceil('hour')
            <ZTime [2013-05-09T03:59:59.999999+00:00]>

        """

        return self.span(frame)[1]

    @classmethod
    def span_range(
            cls,
            frame,
            start,
            end,
            tz=None,
            limit=None,
            bounds="[)",
            exact=False,
    ):
        """Returns an iterator of tuples, each :class:`ZTime <arrow.arrow.ZTime>` objects,
        representing a series of timespans between two inputs.

        :param frame: The timeframe.  Can be any ``datetime`` property (day, hour, minute...).
        :param start: A datetime expression, the start of the range.
        :param end: (optional) A datetime expression, the end of the range.
        :param tz: (optional) A :ref:`timezone expression <tz-expr>`.  Defaults to
            ``start``'s timezone, or UTC if ``start`` is naive.
        :param limit: (optional) A maximum number of tuples to return.
        :param bounds: (optional) a ``str`` of either '()', '(]', '[)', or '[]' that specifies
            whether to include or exclude the start and end values in each span in the range. '(' excludes
            the start, '[' includes the start, ')' excludes the end, and ']' includes the end.
            If the bounds are not specified, the default bound '[)' is used.
        :param exact: (optional) whether to have the first timespan start exactly
            at the time specified by ``start`` and the final span truncated
            so as not to extend beyond ``end``.

        **NOTE**: The ``end`` or ``limit`` must be provided.  Call with ``end`` alone to
        return the entire range.  Call with ``limit`` alone to return a maximum # of results from
        the start.  Call with both to cap a range at a maximum # of results.

        **NOTE**: ``tz`` internally **replaces** the timezones of both ``start`` and ``end`` before
        iterating.  As such, either call with naive objects and ``tz``, or aware objects from the
        same timezone and no ``tz``.

        Supported frame values: year, quarter, month, week, day, hour, minute, second, microsecond.

        Recognized datetime expressions:

            - An :class:`ZTime <arrow.arrow.ZTime>` object.
            - A ``datetime`` object.

        **NOTE**: Unlike Python's ``range``, ``end`` will *always* be included in the returned
        iterator of timespans.

        Usage:

            >>> start = datetime(2013, 5, 5, 12, 30)
            >>> end = datetime(2013, 5, 5, 17, 15)
            >>> for r in arrow.ZTime.span_range('hour', start, end):
            ...     print(r)
            ...
            (<ZTime [2013-05-05T12:00:00+00:00]>, <ZTime [2013-05-05T12:59:59.999999+00:00]>)
            (<ZTime [2013-05-05T13:00:00+00:00]>, <ZTime [2013-05-05T13:59:59.999999+00:00]>)
            (<ZTime [2013-05-05T14:00:00+00:00]>, <ZTime [2013-05-05T14:59:59.999999+00:00]>)
            (<ZTime [2013-05-05T15:00:00+00:00]>, <ZTime [2013-05-05T15:59:59.999999+00:00]>)
            (<ZTime [2013-05-05T16:00:00+00:00]>, <ZTime [2013-05-05T16:59:59.999999+00:00]>)
            (<ZTime [2013-05-05T17:00:00+00:00]>, <ZTime [2013-05-05T17:59:59.999999+00:00]>)

        """

        tzinfo = cls._get_tzinfo(start.tzinfo if tz is None else tz)
        start = cls.fromdatetime(start, tzinfo).span(frame, exact=exact)[0]
        end = cls.fromdatetime(end, tzinfo)
        _range = cls.range(frame, start, end, tz, limit)
        if not exact:
            for r in _range:
                yield r.span(frame, bounds=bounds, exact=exact)

        for r in _range:
            floor, ceil = r.span(frame, bounds=bounds, exact=exact)
            if ceil > end:
                ceil = end
                if bounds[1] == ")":
                    ceil += relativedelta(microseconds=-1)
            if floor == end:
                break
            elif floor + relativedelta(microseconds=-1) == end:
                break
            yield floor, ceil

    @classmethod
    def interval(
            cls,
            frame,
            start,
            end,
            interval=1,
            tz=None,
            bounds="[)",
            exact=False,
    ):
        """Returns an iterator of tuples, each :class:`ZTime <arrow.arrow.ZTime>` objects,
        representing a series of intervals between two inputs.

        :param frame: The timeframe.  Can be any ``datetime`` property (day, hour, minute...).
        :param start: A datetime expression, the start of the range.
        :param end: (optional) A datetime expression, the end of the range.
        :param interval: (optional) Time interval for the given time frame.
        :param tz: (optional) A timezone expression.  Defaults to UTC.
        :param bounds: (optional) a ``str`` of either '()', '(]', '[)', or '[]' that specifies
            whether to include or exclude the start and end values in the intervals. '(' excludes
            the start, '[' includes the start, ')' excludes the end, and ']' includes the end.
            If the bounds are not specified, the default bound '[)' is used.
        :param exact: (optional) whether to have the first timespan start exactly
            at the time specified by ``start`` and the final interval truncated
            so as not to extend beyond ``end``.

        Supported frame values: year, quarter, month, week, day, hour, minute, second

        Recognized datetime expressions:

            - An :class:`ZTime <arrow.arrow.ZTime>` object.
            - A ``datetime`` object.

        Recognized timezone expressions:

            - A ``tzinfo`` object.
            - A ``str`` describing a timezone, similar to 'US/Pacific', or 'Europe/Berlin'.
            - A ``str`` in ISO 8601 style, as in '+07:00'.
            - A ``str``, one of the following:  'local', 'utc', 'UTC'.

        Usage:

            >>> start = datetime(2013, 5, 5, 12, 30)
            >>> end = datetime(2013, 5, 5, 17, 15)
            >>> for r in arrow.ZTime.interval('hour', start, end, 2):
            ...     print(r)
            ...
            (<ZTime [2013-05-05T12:00:00+00:00]>, <ZTime [2013-05-05T13:59:59.999999+00:00]>)
            (<ZTime [2013-05-05T14:00:00+00:00]>, <ZTime [2013-05-05T15:59:59.999999+00:00]>)
            (<ZTime [2013-05-05T16:00:00+00:00]>, <ZTime [2013-05-05T17:59:59.999999+00:0]>)
        """
        if interval < 1:
            raise ValueError("interval has to be a positive integer")

        spanRange = iter(
            cls.span_range(frame, start, end, tz, bounds=bounds, exact=exact)
        )
        while True:
            try:
                intvlStart, intvlEnd = next(spanRange)
                for _ in range(interval - 1):
                    try:
                        _, intvlEnd = next(spanRange)
                    except StopIteration:
                        continue
                yield intvlStart, intvlEnd
            except StopIteration:
                return

    # representations

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} [{self.__str__()}]>"

    def __str__(self) -> str:
        return self._datetime.isoformat()

    def __format__(self, formatstr: str) -> str:
        if len(formatstr) > 0:
            return self.format(formatstr)

        return str(self)

    def __hash__(self) -> int:
        return self._datetime.__hash__()

    # attributes and properties

    def __getattr__(self, name: str) -> int:
        if name == "week":
            return self.isocalendar()[1]

        if name == "quarter":
            return int((self.month - 1) / self._MONTHS_PER_QUARTER) + 1

        if not name.startswith("_"):
            value: Optional[int] = getattr(self._datetime, name, None)

            if value is not None:
                return value

        return cast(int, object.__getattribute__(self, name))

    @property
    def tzinfo(self) -> dt_tzinfo:
        """Gets the ``tzinfo`` of the :class:`ZTime <arrow.arrow.ZTime>` object.

        Usage::

            >>> arw=arrow.utcnow()
            >>> arw.tzinfo
            tzutc()

        """

        # In ZTime, `_datetime` cannot be naive.
        return cast(dt_tzinfo, self._datetime.tzinfo)

    @property
    def datetime(self) -> dt_datetime:
        """Returns a datetime representation of the :class:`ZTime <arrow.arrow.ZTime>` object.

        Usage::

            >>> arw=arrow.utcnow()
            >>> arw.datetime
            datetime.datetime(2019, 1, 24, 16, 35, 27, 276649, tzinfo=tzutc())

        """

        return self._datetime

    @property
    def naive(self) -> dt_datetime:
        """Returns a naive datetime representation of the :class:`ZTime <arrow.arrow.ZTime>`
        object.

        Usage::

            >>> nairobi = arrow.now('Africa/Nairobi')
            >>> nairobi
            <ZTime [2019-01-23T19:27:12.297999+03:00]>
            >>> nairobi.naive
            datetime.datetime(2019, 1, 23, 19, 27, 12, 297999)

        """

        return self._datetime.replace(tzinfo=None)

    def timestamp(self):
        """
        将arrow对象转换为浮点数类型的时间戳
        """
        return self._datetime.timestamp()

    @property
    def int_timestamp(self):
        """
        将arrow对象转换为整数类型的时间戳
        """
        return int(self.timestamp())

    @property
    def float_timestamp(self):
        """
        以属性的方式获取浮点数类型的时间戳
        """
        return self.timestamp()

    @property
    def fold(self) -> int:
        """Returns the ``fold`` value of the :class:`ZTime <arrow.arrow.ZTime>` object."""
        return self._datetime.fold

    @property
    def ambiguous(self) -> bool:
        """Indicates whether the :class:`ZTime <arrow.arrow.ZTime>` object is a repeated wall time in the current
        timezone.

        """

        return dateutil_tz.datetime_ambiguous(self._datetime)

    @property
    def imaginary(self) -> bool:
        """Indicates whether the :class: `ZTime <arrow.arrow.ZTime>` object exists in the current timezone."""

        return not dateutil_tz.datetime_exists(self._datetime)

    # mutation and duplication.

    def clone(self):
        """
        深拷贝一个arrow对象
        """
        return self.fromdatetime(self._datetime)

    def replace(self, **kwargs):
        """
        替换掉指定的时间值
        arw.replace(year=2014, month=6)
        支持：year、month、day、hour、minute、second
        """

        absolute_kwargs = {}

        for key, value in kwargs.items():
            if key in self._ATTRS:
                absolute_kwargs[key] = value
            elif key in ["week", "quarter"]:
                raise ValueError(f"Setting absolute {key} is not supported.")
            elif key not in ["tzinfo", "fold"]:
                raise ValueError(f"Unknown attribute: {key!r}.")

        current = self._datetime.replace(**absolute_kwargs)

        tzinfo = kwargs.get("tzinfo")

        if tzinfo is not None:
            tzinfo = self._get_tzinfo(tzinfo)
            current = current.replace(tzinfo=tzinfo)

        fold = kwargs.get("fold")

        if fold is not None:
            current = current.replace(fold=fold)

        return self.fromdatetime(current)

    def shift(self, **kwargs: Any) -> "ZTime":
        """
        对日期做计算，支持的计算有：
        years：年份
        months：月份
        hours：小时
        weekday：指定星期几
        """

        relative_kwargs = {}
        additional_attrs = ["weeks", "quarters", "weekday"]

        for key, value in kwargs.items():
            if key in self._ATTRS_PLURAL or key in additional_attrs:
                relative_kwargs[key] = value
            else:
                supported_attr = ", ".join(self._ATTRS_PLURAL + additional_attrs)
                raise ValueError(
                    f"Invalid shift time frame. Please select one of the following: {supported_attr}."
                )

        # core datetime does not support quarters, translate to months.
        relative_kwargs.setdefault("months", 0)
        relative_kwargs["months"] += (
                relative_kwargs.pop("quarters", 0) * self._MONTHS_PER_QUARTER
        )

        current = self._datetime + relativedelta(**relative_kwargs)

        if not dateutil_tz.datetime_exists(current):
            current = dateutil_tz.resolve_imaginary(current)

        return self.fromdatetime(current)

    def to(self, tz):
        """
        转换到指定的时区
        tc.to('US/Pacific')
        utc.to(tz.tzlocal())
        utc.to('-07:00')
        utc.to('local')
        utc.to('local').to('utc')
        """

        if not isinstance(tz, dt_tzinfo):
            tz = parser.TzinfoParser.parse(tz)

        dt = self._datetime.astimezone(tz)

        return self.__class__(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            dt.tzinfo,
            fold=getattr(dt, "fold", 0),
        )

    # string output and formatting

    def format(
            self,
            fmt: str = "YYYY-MM-DD HH:mm:ss",
            locale: str = DEFAULT_LOCALE
    ):
        """
        日期格式化为标准的字符串
        :param fmt: 格式化字符串
        :param locale: 格式化地区
        arrow.utcnow().format('YYYY-MM-DD HH:mm:ss ZZ')
        """
        return formatter.DateTimeFormatter(locale).format(self._datetime, fmt)

    def humanize(
            self,
            other: Union["ZTime", dt_datetime, None] = None,
            locale: str = DEFAULT_LOCALE,
            only_distance: bool = False,
            granularity="auto",
    ) -> str:
        """
        转换为人性化的时间格式
        :param other: 另一个arrow对象
        :param locale: 地区
        :param only_distance: 是否只显示时间距离
        :param granularity: 距离格式，支持 'second', 'minute', 'hour', 'day', 'week', 'month', 'year'
        earlier = arrow.utcnow().shift(hours=-2)
        earlier.humanize()
        later = earlier.shift(hours=4)
        later.humanize(earlier)
        """

        locale_name = locale
        locale = locales.get_locale(locale)

        if other is None:
            utc = dt_datetime.utcnow().replace(tzinfo=dateutil_tz.tzutc())
            dt = utc.astimezone(self._datetime.tzinfo)

        elif isinstance(other, ZTime):
            dt = other._datetime

        elif isinstance(other, dt_datetime):
            if other.tzinfo is None:
                dt = other.replace(tzinfo=self._datetime.tzinfo)
            else:
                dt = other.astimezone(self._datetime.tzinfo)

        else:
            raise TypeError(
                f"Invalid 'other' argument of type {type(other).__name__!r}. "
                "Argument must be of type None, ZTime, or datetime."
            )

        if isinstance(granularity, list) and len(granularity) == 1:
            granularity = granularity[0]

        _delta = int(round((self._datetime - dt).total_seconds()))
        sign = -1 if _delta < 0 else 1
        delta_second = diff = abs(_delta)

        try:
            if granularity == "auto":
                if diff < 10:
                    return locale.describe("now", only_distance=only_distance)

                if diff < self._SECS_PER_MINUTE:
                    seconds = sign * delta_second
                    return locale.describe(
                        "seconds", seconds, only_distance=only_distance
                    )

                elif diff < self._SECS_PER_MINUTE * 2:
                    return locale.describe("minute", sign, only_distance=only_distance)
                elif diff < self._SECS_PER_HOUR:
                    minutes = sign * max(delta_second // self._SECS_PER_MINUTE, 2)
                    return locale.describe(
                        "minutes", minutes, only_distance=only_distance
                    )

                elif diff < self._SECS_PER_HOUR * 2:
                    return locale.describe("hour", sign, only_distance=only_distance)
                elif diff < self._SECS_PER_DAY:
                    hours = sign * max(delta_second // self._SECS_PER_HOUR, 2)
                    return locale.describe("hours", hours, only_distance=only_distance)
                elif diff < self._SECS_PER_DAY * 2:
                    return locale.describe("day", sign, only_distance=only_distance)
                elif diff < self._SECS_PER_WEEK:
                    days = sign * max(delta_second // self._SECS_PER_DAY, 2)
                    return locale.describe("days", days, only_distance=only_distance)

                elif diff < self._SECS_PER_WEEK * 2:
                    return locale.describe("week", sign, only_distance=only_distance)
                elif diff < self._SECS_PER_MONTH:
                    weeks = sign * max(delta_second // self._SECS_PER_WEEK, 2)
                    return locale.describe("weeks", weeks, only_distance=only_distance)

                elif diff < self._SECS_PER_MONTH * 2:
                    return locale.describe("month", sign, only_distance=only_distance)
                elif diff < self._SECS_PER_YEAR:
                    # TODO revisit for humanization during leap years
                    self_months = self._datetime.year * 12 + self._datetime.month
                    other_months = dt.year * 12 + dt.month

                    months = sign * max(abs(other_months - self_months), 2)

                    return locale.describe(
                        "months", months, only_distance=only_distance
                    )

                elif diff < self._SECS_PER_YEAR * 2:
                    return locale.describe("year", sign, only_distance=only_distance)
                else:
                    years = sign * max(delta_second // self._SECS_PER_YEAR, 2)
                    return locale.describe("years", years, only_distance=only_distance)

            elif isinstance(granularity, str):
                granularity = cast(TimeFrameLiteral, granularity)  # type: ignore[assignment]

                if granularity == "second":
                    delta = sign * float(delta_second)
                    if abs(delta) < 2:
                        return locale.describe("now", only_distance=only_distance)
                elif granularity == "minute":
                    delta = sign * delta_second / self._SECS_PER_MINUTE
                elif granularity == "hour":
                    delta = sign * delta_second / self._SECS_PER_HOUR
                elif granularity == "day":
                    delta = sign * delta_second / self._SECS_PER_DAY
                elif granularity == "week":
                    delta = sign * delta_second / self._SECS_PER_WEEK
                elif granularity == "month":
                    delta = sign * delta_second / self._SECS_PER_MONTH
                elif granularity == "quarter":
                    delta = sign * delta_second / self._SECS_PER_QUARTER
                elif granularity == "year":
                    delta = sign * delta_second / self._SECS_PER_YEAR
                else:
                    raise ValueError(
                        "Invalid level of granularity. "
                        "Please select between 'second', 'minute', 'hour', 'day', 'week', 'month', 'quarter' or 'year'."
                    )

                if trunc(abs(delta)) != 1:
                    granularity += "s"  # type: ignore[assignment]
                return locale.describe(granularity, delta, only_distance=only_distance)

            else:
                if not granularity:
                    raise ValueError(
                        "Empty granularity list provided. "
                        "Please select one or more from 'second', 'minute', 'hour', 'day', 'week', 'month', 'quarter', 'year'."
                    )

                timeframes: List[Tuple[TimeFrameLiteral, float]] = []

                def gather_timeframes(_delta: float, _frame: TimeFrameLiteral) -> float:
                    if _frame in granularity:
                        value = sign * _delta / self._SECS_MAP[_frame]
                        _delta %= self._SECS_MAP[_frame]
                        if trunc(abs(value)) != 1:
                            timeframes.append(
                                (cast(TimeFrameLiteral, _frame + "s"), value)
                            )
                        else:
                            timeframes.append((_frame, value))
                    return _delta

                delta = float(delta_second)
                frames: Tuple[TimeFrameLiteral, ...] = (
                    "year",
                    "quarter",
                    "month",
                    "week",
                    "day",
                    "hour",
                    "minute",
                    "second",
                )
                for frame in frames:
                    delta = gather_timeframes(delta, frame)

                if len(timeframes) < len(granularity):
                    raise ValueError(
                        "Invalid level of granularity. "
                        "Please select between 'second', 'minute', 'hour', 'day', 'week', 'month', 'quarter' or 'year'."
                    )

                return locale.describe_multi(timeframes, only_distance=only_distance)

        except KeyError as e:
            raise ValueError(
                f"Humanization of the {e} granularity is not currently translated in the {locale_name!r} locale. "
                "Please consider making a contribution to this locale."
            )

    def dehumanize(self, input_string: str, locale: str = "en_us") -> "ZTime":
        """
        解析人性化的时间格式
        :param timestring: 人性化的时间字符串
        :param locale: 地区
        arw = arrow.utcnow()
        earlier = arw.dehumanize("2 days ago")
        later = arw.dehumanize("in a month")
        """

        # Create a locale object based off given local
        locale_obj = locales.get_locale(locale)

        # Check to see if locale is supported
        normalized_locale_name = locale.lower().replace("_", "-")

        if normalized_locale_name not in DEHUMANIZE_LOCALES:
            raise ValueError(
                f"Dehumanize does not currently support the {locale} locale, please consider making a contribution to add support for this locale."
            )

        current_time = self.fromdatetime(self._datetime)

        # Create an object containing the relative time info
        time_object_info = dict.fromkeys(
            ["seconds", "minutes", "hours", "days", "weeks", "months", "years"], 0
        )

        # Create an object representing if unit has been seen
        unit_visited = dict.fromkeys(
            ["now", "seconds", "minutes", "hours", "days", "weeks", "months", "years"],
            False,
        )

        # Create a regex pattern object for numbers
        num_pattern = re.compile(r"\d+")

        # Search input string for each time unit within locale
        for unit, unit_object in locale_obj.timeframes.items():
            # Need to check the type of unit_object to create the correct dictionary
            if isinstance(unit_object, Mapping):
                strings_to_search = unit_object
            else:
                strings_to_search = {unit: str(unit_object)}

            # Search for any matches that exist for that locale's unit.
            # Needs to cycle all through strings as some locales have strings that
            # could overlap in a regex match, since input validation isn't being performed.
            for time_delta, time_string in strings_to_search.items():
                # Replace {0} with regex \d representing digits
                search_string = str(time_string)
                search_string = search_string.format(r"\d+")

                # Create search pattern and find within string
                pattern = re.compile(rf"(^|\b|\d){search_string}")
                match = pattern.search(input_string)

                # If there is no match continue to next iteration
                if not match:
                    continue

                match_string = match.group()
                num_match = num_pattern.search(match_string)

                # If no number matches
                # Need for absolute value as some locales have signs included in their objects
                if not num_match:
                    change_value = (
                        1 if not time_delta.isnumeric() else abs(int(time_delta))
                    )
                else:
                    change_value = int(num_match.group())

                # No time to update if now is the unit
                if unit == "now":
                    unit_visited[unit] = True
                    continue

                # Add change value to the correct unit (incorporates the plurality that exists within timeframe i.e second v.s seconds)
                time_unit_to_change = str(unit)
                time_unit_to_change += (
                    "s" if (str(time_unit_to_change)[-1] != "s") else ""
                )
                time_object_info[time_unit_to_change] = change_value
                unit_visited[time_unit_to_change] = True

        # Assert error if string does not modify any units
        if not any([True for k, v in unit_visited.items() if v]):
            raise ValueError(
                "Input string not valid. Note: Some locales do not support the week granularity in ZTime. "
                "If you are attempting to use the week granularity on an unsupported locale, this could be the cause of this error."
            )

        # Sign logic
        future_string = locale_obj.future
        future_string = future_string.format(".*")
        future_pattern = re.compile(rf"^{future_string}$")
        future_pattern_match = future_pattern.findall(input_string)

        past_string = locale_obj.past
        past_string = past_string.format(".*")
        past_pattern = re.compile(rf"^{past_string}$")
        past_pattern_match = past_pattern.findall(input_string)

        # If a string contains the now unit, there will be no relative units, hence the need to check if the now unit
        # was visited before raising a ValueError
        if past_pattern_match:
            sign_val = -1
        elif future_pattern_match:
            sign_val = 1
        elif unit_visited["now"]:
            sign_val = 0
        else:
            raise ValueError(
                "Invalid input String. String does not contain any relative time information. "
                "String should either represent a time in the future or a time in the past. "
                "Ex: 'in 5 seconds' or '5 seconds ago'."
            )

        time_changes = {k: sign_val * v for k, v in time_object_info.items()}

        return current_time.shift(**time_changes)

    # query functions

    def is_between(
            self,
            start: "ZTime",
            end: "ZTime",
            bounds: _BOUNDS = "()",
    ) -> bool:
        """返回一个布尔值，表示:class: ' ZTime &lt;arrow.arrow.ZTime&gt; '对象是否在开始和结束限制之间。

        :param start: ZTime对象。
        :param end: ZTime对象。
        :param bounds: (可选)由'()'，'(]'，'[)'或'[]'组成的' ' str ' '
            用于指定是否包含或排除范围中的开始值和结束值。
            '('不包括开始，'['包括开始，')'不包括结束，']'包括结束。
            如果未指定边界，则使用默认的边界'()'。
                start = arrow.get(datetime(2013, 5, 5, 12, 30, 10))
                end = arrow.get(datetime(2013, 5, 5, 12, 30, 36))
                arrow.get(datetime(2013, 5, 5, 12, 30, 27)).is_between(start, end)

                start = arrow.get(datetime(2013, 5, 5))
                end = arrow.get(datetime(2013, 5, 8))
                arrow.get(datetime(2013, 5, 8)).is_between(start, end, '[]')

                start = arrow.get(datetime(2013, 5, 5))
                end = arrow.get(datetime(2013, 5, 8))
                arrow.get(datetime(2013, 5, 8)).is_between(start, end, '[)')
        """

        util.validate_bounds(bounds)

        if not isinstance(start, ZTime):
            raise TypeError(
                f"Cannot parse start date argument type of {type(start)!r}."
            )

        if not isinstance(end, ZTime):
            raise TypeError(f"Cannot parse end date argument type of {type(start)!r}.")

        include_start = bounds[0] == "["
        include_end = bounds[1] == "]"

        target_ts = self.float_timestamp
        start_ts = start.float_timestamp
        end_ts = end.float_timestamp

        return (
                (start_ts <= target_ts <= end_ts)
                and (include_start or start_ts < target_ts)
                and (include_end or target_ts < end_ts)
        )

    # datetime methods

    def date(self) -> date:
        """
        返回具有相同年，月和日的' date '对象。
            arrow.utcnow().date()
        """
        return self._datetime.date()

    def time(self) -> dt_time:
        """
        返回具有相同时，分，秒，微秒的' time '对象。
            arrow.utcnow().time()
        """

        return self._datetime.time()

    def timetz(self):
        """
        返回具有相同时、分、秒、微秒和tzinfo值的' time '对象。
            arrow.utcnow().timetz()
        """
        return self._datetime.timetz()

    def astimezone(self, tz: Optional[dt_tzinfo]) -> dt_datetime:
        """
        返回一个' ' datetime ' '对象，转换为指定的时区。
        :param tz: tzinfo对象

        pacific=arrow.now('US/Pacific')
        nyc=arrow.now('America/New_York').tzinfo
        pacific.astimezone(nyc)
        """

        return self._datetime.astimezone(tz)

    def utcoffset(self):
        """
        返回一个' ' timedelta ' '对象，表示与UTC时间相差的整分钟数。
            arrow.now('US/Pacific').utcoffset()
        """
        return self._datetime.utcoffset()

    def dst(self) -> Optional[timedelta]:
        """
        返回夏令时调整值。
            arrow.utcnow().dst()
        """
        return self._datetime.dst()

    def timetuple(self) -> struct_time:
        """
        返回一个 time.Struct_time ，在当前时区中。
            arrow.utcnow().timetuple()
        """
        return self._datetime.timetuple()

    def utctimetuple(self) -> struct_time:
        """
        返回一个 time.struct_time， UTC时间。
            arrow.utcnow().utctimetuple()
        """

        return self._datetime.utctimetuple()

    def toordinal(self) -> int:
        """
        返回日期的预知格列高利历序数。

        arrow.utcnow().toordinal()
        """

        return self._datetime.toordinal()

    def weekday(self):
        """
        以整数(0-6)的形式返回星期几。
            arrow.utcnow().weekday()
        """

        return self._datetime.weekday()

    def isoweekday(self) -> int:
        """
        以整数(1-7)的形式返回一周中的ISO星期。
            arrow.utcnow().isoweekday()
        """

        return self._datetime.isoweekday()

    def isocalendar(self) -> Tuple[int, int, int]:
        """Returns a 3-tuple, (ISO year, ISO week number, ISO weekday).

        Usage::

            >>> arrow.utcnow().isocalendar()
            (2019, 3, 6)

        """

        return self._datetime.isocalendar()

    def isoformat(self, sep: str = "T", timespec: str = "auto") -> str:
        """Returns an ISO 8601 formatted representation of the date and time.

        Usage::

            >>> arrow.utcnow().isoformat()
            '2019-01-19T18:30:52.442118+00:00'

        """

        return self._datetime.isoformat(sep, timespec)

    def ctime(self) -> str:
        """Returns a ctime formatted representation of the date and time.

        Usage::

            >>> arrow.utcnow().ctime()
            'Sat Jan 19 18:26:50 2019'

        """

        return self._datetime.ctime()

    def strftime(self, format: str) -> str:
        """Formats in the style of ``datetime.strftime``.

        :param format: the format string.

        Usage::

            >>> arrow.utcnow().strftime('%d-%m-%Y %H:%M:%S')
            '23-01-2019 12:28:17'

        """

        return self._datetime.strftime(format)

    def for_json(self) -> str:
        """Serializes for the ``for_json`` protocol of simplejson.

        Usage::

            >>> arrow.utcnow().for_json()
            '2019-01-19T18:25:36.760079+00:00'

        """

        return self.isoformat()

    # math

    def __add__(self, other: Any) -> "ZTime":
        if isinstance(other, (timedelta, relativedelta)):
            return self.fromdatetime(self._datetime + other, self._datetime.tzinfo)

        return NotImplemented

    def __radd__(self, other: Union[timedelta, relativedelta]) -> "ZTime":
        return self.__add__(other)

    @overload
    def __sub__(self, other: Union[timedelta, relativedelta]) -> "ZTime":
        pass  # pragma: no cover

    @overload
    def __sub__(self, other: Union[dt_datetime, "ZTime"]) -> timedelta:
        pass  # pragma: no cover

    def __sub__(self, other: Any) -> Union[timedelta, "ZTime"]:
        if isinstance(other, (timedelta, relativedelta)):
            return self.fromdatetime(self._datetime - other, self._datetime.tzinfo)

        elif isinstance(other, dt_datetime):
            return self._datetime - other

        elif isinstance(other, ZTime):
            return self._datetime - other._datetime

        return NotImplemented

    def __rsub__(self, other: Any) -> timedelta:
        if isinstance(other, dt_datetime):
            return other - self._datetime

        return NotImplemented

    # comparisons

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, (ZTime, dt_datetime)):
            return False

        return self._datetime == self._get_datetime(other)

    def __ne__(self, other: Any) -> bool:
        if not isinstance(other, (ZTime, dt_datetime)):
            return True

        return not self.__eq__(other)

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, (ZTime, dt_datetime)):
            return NotImplemented

        return self._datetime > self._get_datetime(other)

    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, (ZTime, dt_datetime)):
            return NotImplemented

        return self._datetime >= self._get_datetime(other)

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, (ZTime, dt_datetime)):
            return NotImplemented

        return self._datetime < self._get_datetime(other)

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, (ZTime, dt_datetime)):
            return NotImplemented

        return self._datetime <= self._get_datetime(other)

    # internal methods
    @staticmethod
    def _get_tzinfo(tz_expr):
        """Get normalized tzinfo object from various inputs."""
        if tz_expr is None:
            return dateutil_tz.tzutc()
        if isinstance(tz_expr, dt_tzinfo):
            return tz_expr
        else:
            try:
                return parser.TzinfoParser.parse(tz_expr)
            except parser.ParserError:
                raise ValueError(f"{tz_expr!r} not recognized as a timezone.")

    @classmethod
    def _get_datetime(
            cls, expr: Union["ZTime", dt_datetime, int, float, str]
    ) -> dt_datetime:
        """Get datetime object from a specified expression."""
        if isinstance(expr, ZTime):
            return expr.datetime
        elif isinstance(expr, dt_datetime):
            return expr
        elif util.is_timestamp(expr):
            timestamp = float(expr)
            return cls.utcfromtimestamp(timestamp).datetime
        else:
            raise ValueError(f"{expr!r} not recognized as a datetime or timestamp.")

    @classmethod
    def _get_frames(cls, name: _T_FRAMES) -> Tuple[str, str, int]:
        """Finds relevant timeframe and steps for use in range and span methods.

        Returns a 3 element tuple in the form (frame, plural frame, step), for example ("day", "days", 1)

        """
        if name in cls._ATTRS:
            return name, f"{name}s", 1
        elif name[-1] == "s" and name[:-1] in cls._ATTRS:
            return name[:-1], name, 1
        elif name in ["week", "weeks"]:
            return "week", "weeks", 1
        elif name in ["quarter", "quarters"]:
            return "quarter", "months", 3
        else:
            supported = ", ".join(
                [
                    "year(s)",
                    "month(s)",
                    "day(s)",
                    "hour(s)",
                    "minute(s)",
                    "second(s)",
                    "microsecond(s)",
                    "week(s)",
                    "quarter(s)",
                ]
            )
            raise ValueError(
                f"Range or span over frame {name} not supported. Supported frames: {supported}."
            )

    @classmethod
    def _get_iteration_params(cls, end: Any, limit: Optional[int]) -> Tuple[Any, int]:
        """Sets default end and limit values for range method."""
        if end is None:
            if limit is None:
                raise ValueError("One of 'end' or 'limit' is required.")

            return cls.max, limit

        else:
            if limit is None:
                return end, sys.maxsize
            return end, limit

    @staticmethod
    def _is_last_day_of_month(date: "ZTime") -> bool:
        """Returns a boolean indicating whether the datetime is the last day of the month."""
        return date.day == calendar.monthrange(date.year, date.month)[1]


ZTime.min = ZTime.fromdatetime(dt_datetime.min)
ZTime.max = ZTime.fromdatetime(dt_datetime.max)

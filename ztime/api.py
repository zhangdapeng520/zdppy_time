from typing import Type, overload

from .ztime import ZTime
from .constants import DEFAULT_LOCALE
from .factory import ZTimeFactory

_factory = ZTimeFactory()


@overload
def get(
        *,
        locale=DEFAULT_LOCALE,
        tzinfo=None,
        normalize_whitespace=False,
):
    ...  # pragma: no cover


@overload
def get(
        *args,
        locale=DEFAULT_LOCALE,
        tzinfo=None,
        normalize_whitespace=False,
) -> ZTime:
    ...  # pragma: no cover


@overload
def get(
        __obj,
        *,
        locale=DEFAULT_LOCALE,
        tzinfo=None,
        normalize_whitespace=False,
):
    ...  # pragma: no cover


@overload
def get(
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
        __arg1,
        __arg2,
        *,
        locale=DEFAULT_LOCALE,
        tzinfo=None,
        normalize_whitespace=False,
):
    ...  # pragma: no cover


def get(*args, **kwargs):
    """
    通过工厂构造ZTime对象
    :param args:
    :param kwargs:
    :return:
    """
    return _factory.get(*args, **kwargs)


def utcnow():
    """
    获取当前时间
    :return: ZTime实例对象
    """
    return _factory.utcnow()


def now_str(format="YYYY-MM-DD HH:mm:ss"):
    """获取当前时间的日期字符串"""
    return now().format(format)


def now(tz="local"):
    """
    获取当前时间
    :param tz: 时区
    :return: ZTime实例对象
    """
    return _factory.now(tz)


def factory(type):
    """
    获取工厂对象
    :param type: 类型
    """
    return ZTimeFactory(type)


__all__ = ["get", "utcnow", "now", "factory"]

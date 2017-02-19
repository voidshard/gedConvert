"""
Utils functions that aren't
"""

import datetime
import re


_DEFAULT_YEAR = "1000"
_DEFAULT_MONTH = "Jan"
_DEFAULT_DAY = "01"

_DEFAULT_OUTPUT_DATE_STR_IF_NONE = "None"
_DEFAULT_OUTPUT_DATE_INT_IF_NONE = 0

_EPOCH = datetime.datetime.utcfromtimestamp(0)


def date_to_string(date):
    """Turn date into some string we desire for output

    For undefined dates, we return _DEFAULT_OUTPUT_DATE_IF_NONE

    Args:
        date (datetime.Datetime): date to output

    Returns:
        str
    """
    if not date:
        return _DEFAULT_OUTPUT_DATE_STR_IF_NONE
    return str(date.date())


def date_to_epoch(date):
    """Return time (in seconds) since epoch given a datetime

    Args:
        date (datetime.Datetime:

    Returns:
        int
    """
    if not date:
        return 0
    return int((date - _EPOCH).total_seconds())


def default_datetime():
    """Return the default datetime

    Returns:
        datetime.Datetime
    """
    s = "%s %s %s 0:0:0" % (_DEFAULT_DAY, _DEFAULT_MONTH, _DEFAULT_YEAR)
    return datetime.datetime.strptime(s, "%d %b %Y %H:%M:%S")


def strip_alpha(val):
    """Strip out all non numeric chars from some string

    Args:
        val (str): value to coerce

    Returns:
        str
    """
    if not val:
        return ""
    return re.sub("[^0-9]", "", val)


def force_int(val):
    """Remove alpha from string and cast to int.

    Returns 0 if cast fails

    Args:
        val (str):

    Returns:
        int
    """
    try:
        return int(strip_alpha(val))
    except ValueError:
        pass
    return 0


def is_int(val):
    """Return if given string can be cast to an int

    Note: this is not "is this an int" ie: isinstance()
    but perhaps "could this represent an int"

    Args:
        val (str):

    Returns:
        bool
    """
    try:
        int(val)
        return True
    except ValueError:
        pass
    return False


def is_year(val):
    """Return if some part of a date string 'val' is likely
    to be a 'year'

    That is, if it's a number and is longer than 2 digits.

    Args:
        val (str):

    Returns:

    """
    return is_int(val) and len(val) > 2


def add_date_and_time(date, tyme):
    """Given two datetimes a and b, return the datetime that
    includes the date of the first and the time of the second.


    Args:
        date (datetime.Datetime): datetime to use date from
        tyme (datetime.Datetime): datetime to use time from

    Returns:
        datetime.Datetime
    """
    s = "%d %d %d %d %d %d" % (
        date.day,
        date.month,
        date.year,
        tyme.hour,
        tyme.minute,
        tyme.second,
    )
    return datetime.datetime.strptime(s, "%d %m %Y %H %M %S")


def parse_partial_date(date_parts):
    """Determine which of the day (int), month (str) and year (int)
    we have been given.

    Args:
        date_parts ([]str): parts of a date string split

    Returns:
        str, str, str
    """
    day = _DEFAULT_DAY
    month = _DEFAULT_MONTH
    year = _DEFAULT_YEAR

    for part in date_parts:
        if not is_int(part):
            # only the month is always a string
            month = part
        elif is_year(part):
            year = part
        else:
            day = part
    return day, month, year

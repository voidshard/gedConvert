"""
Utils functions that aren't
"""

import datetime
import re


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
        return None
    return str(date.date())


def date_to_epoch(date):
    """Return time (in seconds) since epoch given a datetime

    Args:
        date (datetime.Datetime:

    Returns:
        int or None
    """
    if not date:
        return None
    return int((date - _EPOCH).total_seconds())


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


def month_str_to_int(month):
    """

    Args:
        month (str):

    Returns:
        int

    Raises:
        ValueError
    """
    d = datetime.datetime.strptime(month, "%b")
    return d.month


def parse_partial_date(date_parts):
    """Determine which of the day (int), month (str) and year (int)
    we have been given.

    We've got quite a few

    Args:
        date_parts ([]str): parts of a date string split

    Returns:
        int, int, int
    """
    day = None
    month = None
    year = None

    for part in date_parts:
        stripped = strip_alpha(part)
        stripped_is_int = is_int(stripped)

        if stripped == "":
            # only the month is always a string with no numbers
            try:
                month = month_str_to_int(part)
            except ValueError:
                pass
        elif is_year(stripped):
            year = force_int(stripped)
        elif stripped_is_int:
            day = force_int(stripped)
    return day, month, year

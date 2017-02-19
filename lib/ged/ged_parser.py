"""
This handles parsing a .ged file into a generic internal form.
Form there it calls "save_family" or "save_person" on given
"Converter" objects which can each save out the given data.

It's smart enough to read the given file line by line and
doesn't try to store the entire thing in memory at once with
the expectation that the file may be incredibly large.
"""

import datetime
import sys

from ged import utils
from ged import converters as conv


_ERR_PARSING_DATE = ("Warning: Expected datetime as 'day month year' but got "
                     "'%s', using default values & continuing\n")
_GED_LIST_KEYS = ["CHIL", "_AKA"]


def _parse_key_value(line):
    """Parse raw line from .ged file and return key, value

    Each line is,
      <int> <str> <str>
    Thus,
        ?    KEY  value

    If you find out what the int is for, I'd be curious to know ..

    Args:
        line (str):

    Returns:
        str, str
    """
    bits = line.split(" ")
    key = bits[1].strip()

    val = ""
    if len(bits) > 2:
        val = " ".join(bits[2:])
    return key, val.strip()


def _handle_givennames(val):
    """Handle GIVN case

    Args:
        val (str): given name(s)

    Returns:
        []str
    """
    return val.split(" ")


def _handle_surname(val):
    """Handle SURN case

    Args:
        val (str): surname value

    Returns:
        str
    """
    return val.capitalize()


def _handle_married_name(val):
    """Return married name (new surname, if any)

    That is, the _MARNM case

    Args:
        val (str):

    Returns:
        str
    """
    surname = val.split(" ")[-1]
    return surname.capitalize()


def _handle_gender(val):
    """Handle SEX case, return if gender is male

    Args:
        val (str):

    Returns:
        bool
    """
    val = val.lower()
    return val in ["m"]


def _handle_date(val):
    """Return day, month, year (where given) from date str

    We need to handle edge cases:
        - %d %b %Y can be followed by (int)
            -> drop superfluous (int)
        - any of %d %b %Y may not be given
            -> print warning
            -> insert default values for missing bits
        - any of the args may include "c" or "approx"

    Args:
        val (str): date string (hopefully [%d %b %Y])

    Returns:
        int, int, int
    """
    bits = val.split(" ")
    return utils.parse_partial_date(bits)


def _handle_time(val):
    """Parse time string into ints

    Args:
        val (str): time string [HH:MM:SS]

    Returns:
        datetime.Datetime
    """
    return datetime.datetime.strptime(val, "%H:%M:%S")


def _handle_string(val):
    """Handle case where val is a generic string

    Suitable for PLAC, NOTE

    Args:
        val (str):

    Returns:
        str
    """
    return val


def _handle_link_id(val):
    """Handles parsing ID from
        SOMESTRING @id@

    Suitable for:
        HUSB
        WIFE
        CHIL
        FAMC
        FAMS

    Args:
        val (str):

    Returns:
        str
    """
    return val.replace("@", "")


def _extract_datetime(record):
    """Turn the DATE and TIME keys into a python datetime

    If any of the date is not provided None will be returned.
    The time is will be returned a 0:0:0 if not defined.

    Args:
        record (dict): dict that includes a DATE and/or TIME

    Returns:
        datetime.Datetime or None
    """
    d_day, d_month, d_year = record.get("DATE")
    ctime = record.get("TIME") or datetime.datetime.strptime("0:0:0", "%H:%M:%S")
    if all([d_day, d_month, d_year]):
        s = "%s %s %s %d %d %d" % (
            d_day,
            d_month,
            d_year,
            ctime.hour,
            ctime.minute,
            ctime.second,
        )
        return datetime.datetime.strptime(s, "%d %m %Y %H %M %S")
    return None


# end handlers -- start classes
class _DBObj(object):
    ERR_LOCKED = "You may not set values on this obj now"

    def __init__(self, oid):
        self._id = oid
        self._allow_changes = True

        # the last recorded special multi line key
        self._multiline_key = None

        # multi-line key data goes here
        # Eg: BIRT
        #     DATE
        #     PLAC
        self._multi_data = {}

        # single line data fields go here
        #  Eg: SEX M
        self._data = {}

    def lock(self):
        self._allow_changes = False

    def to_string(self):
        return {
            "id": self._id,
            "type": self.__class__.__name__,
            "data": self._data,
            "mdata": self._multi_data,
        }

    def set_multiline_key(self, key):
        if not self._allow_changes:
            raise ValueError(self.ERR_LOCKED)
        self._multiline_key = key

    def set_data(self, key, parsed_data):
        if not self._allow_changes:
            raise ValueError(self.ERR_LOCKED)

        if self._multiline_key:
            tmp = self._multi_data.get(self._multiline_key, {})
            tmp[key] = parsed_data
            self._multi_data[self._multiline_key] = tmp
            return

        if key in _GED_LIST_KEYS:  # in some cases we can have a list of things
            ls = self._data.get(key, [])
            ls.append(parsed_data)
            self._data[key] = ls
        else:
            self._data[key] = parsed_data

    @property
    def uid(self):
        """Return (str) UID"""
        return self._data.get("_UID")

    @property
    def id(self):
        """Return (str) ID"""
        return self._id

    @property
    def note(self):
        """Return 'note' attached to record, if any

        Returns:
            str
        """
        return self._data.get("NOTE", "")

    def _get_date(self, key, num):
        """Internal func to get one of day, month year
        of a given event (key)

        Args:
            key (str):
            num (int): index in day, month, year tuple

        Returns:
            int or None

        Raises:
            ValueError if 0, 1, 2 not given for num
        """
        if num not in [0, 1, 2]:
            raise ValueError("Require 0, 1 or 2, given %s", num)

        rec = self._multi_data.get(key, {}).get("DATE")
        if rec:
            return rec[num]


class _Family(_DBObj):
    @property
    def children_ids(self):
        """Return IDs of children

        Returns:
            []str
        """
        return self._data.get("CHIL", [])

    @property
    def num_children(self):
        """Return the number of children in the family

        Returns:
            int
        """
        return len(self.children_ids)

    @property
    def husband_id(self):
        """Return (str) ID of husband (or None)"""
        return self._data.get("HUSB")

    @property
    def wife_id(self):
        """Return (str) ID of wife (or None)"""
        return self._data.get("WIFE")

    @property
    def marriage_day(self):
        """Return marriage date

        Returns:
            int or None
        """
        return self._get_date("MARR", 0)

    @property
    def marriage_month(self):
        """Return marriage date

        Returns:
            int or None
        """
        return self._get_date("MARR", 1)

    @property
    def marriage_year(self):
        """Return marriage date

        Returns:
            int or None
        """
        return self._get_date("MARR", 2)

    @property
    def marriage_place(self):
        """Return location of marriage

        Returns:
            str or None
        """
        marr = self._multi_data.get("MARR", {})
        return marr.get("PLAC")


class _Person(_DBObj):
    @property
    def is_male(self):
        """Return if the person is male or not

        Returns:
            bool
        """
        return self._data.get("SEX", True)

    @property
    def nicknames(self):
        """Return known nicknames of the person

        Returns:
            []str
        """
        return self._data.get("_AKA", [])

    @property
    def firstname(self):
        """Return the person's given name

        Returns:
            str
        """
        names = self.given_names
        if not names:
            return ""
        return names[0]

    @property
    def surname(self):
        """Return the person's surname (family name)

        Returns:
            str
        """
        return self._data.get("SURN", "")

    @property
    def adult_family_id(self):
        """Return the id of the family the person married into.

        That is, upon marriage two people become a new family

        Returns:
            str or None
        """
        return self._data.get("FAMS")

    @property
    def childhood_family_id(self):
        """Return the id of the family the person was born into

        Returns:
            str or None
        """
        return self._data.get("FAMC")

    @property
    def last_updated(self):
        """Return the last time the record was updated

        Returns:
            datetime.Datetime or None
        """
        change_record = self._multi_data.get("CHAN", {})
        if change_record:
            return _extract_datetime(change_record)

    @property
    def birth_place(self):
        """Return where the person was born (if recorded)

        Returns:
            str
        """
        birth_record = self._multi_data.get("BIRT", {})
        return birth_record.get("PLAC", "")

    @property
    def birth_year(self):
        """Return the person's birth year

        Returns:
            int or None
        """
        return self._get_date("BIRT", 2)
        
    @property
    def death_year(self):
        """Return the person's date of death

        Returns:
            int or None
        """
        return self._get_date("DEAT", 2)

    @property
    def burial_year(self):
        """Return the person's date of burial

        Any of these values may be None if data is incomplete

        Returns:
            int or None
        """
        return self._get_date("BURI", 2)

    @property
    def birth_month(self):
        """Return the person's birth month

        Returns:
            int or None
        """
        return self._get_date("BIRT", 1)

    @property
    def death_month(self):
        """Return the month the person died in

        Returns:
            int or None
        """
        return self._get_date("DEAT", 1)

    @property
    def burial_month(self):
        """Return the month the person was buried in

        Returns:
            int or None
        """
        return self._get_date("BURI", 1)
    
    @property
    def birth_day(self):
        """Return the person's birth day

        Returns:
            int or None
        """
        return self._get_date("BIRT", 0)

    @property
    def death_day(self):
        """Return the day the person died in

        Returns:
            int or None
        """
        return self._get_date("DEAT", 0)

    @property
    def burial_day(self):
        """Return the day the person was buried in

        Returns:
            int or None
        """
        return self._get_date("BURI", 0)

    @property
    def death_place(self):
        """Return where the person died

        Returns:
            str
        """
        d_record = self._multi_data.get("DEAT", {})
        return d_record.get("PLAC", "")

    @property
    def burial_place(self):
        """Return where the person was buried

        Returns:
            str
        """
        d_record = self._multi_data.get("BURI", {})
        return d_record.get("PLAC", "")

    @property
    def given_names(self):
        """Return the person's given name(s)

        Note: This includes the first name

        Returns:
            []str
        """
        return self._data.get("GIVN", [])

    @property
    def married_name(self):
        """Return the surname of the person after marriage.

        If the person didn't change their name, returns surname

        Returns:
            str
        """
        return self._data.get("_MARNM", self.surname)


# -- end classes
_TYPE = {
    "INDI": _Person,
    "FAM": _Family,
}

_KEY_STOP = "TRLR"


_HANDLERS = {  # our set of handlers VS their KEY(s) to parse lines
    "GIVN": (_handle_givennames, False),
    "DATE": (_handle_date, True),
    "TIME": (_handle_time, True),
    "PLAC": (_handle_string, True),
    "NOTE": (_handle_string, False),
    "SEX": (_handle_gender, False),
    "SURN": (_handle_surname, False),
    "_MARNM": (_handle_married_name, False),
    "HUSB": (_handle_link_id, False),
    "WIFE": (_handle_link_id, False),
    "CHIL": (_handle_link_id, False),
    "_AKA": (_handle_string, False),
    "FAMC": (_handle_link_id, False),
    "FAMS": (_handle_link_id, False),
    "_UID": (_handle_link_id, False),
}


def _decide_next_obj(key, val):
    """Handle case where we're given a new obj

    Ie, lines that start with
        @id@ class

    Returns class Obj

    Args:
        val (str):

    Returns:
        Object or None
    """
    obj_id = key.replace("@", "")
    some_class = _TYPE.get(val)
    if not some_class:
        return None
    return some_class(obj_id)


def _is_new_obj_line(key):
    """Return if this line is starting a new object

    Args:
        key (str):

    Returns:
        bool
    """
    return key.count("@") == 2


def _save(converters, some_obj):
    """Call appropriate save func on all given converters

    Args:
        converters ([]Converter): list of converters to run
        some_obj (_DBObj subclass): object to save

    Raises:
        ?
    """
    for c in converters:
        if isinstance(some_obj, _Family):
            c.save_family(some_obj)
        else:
            c.save_person(some_obj)


def parse_ged_file(converters, filepath):
    """Convert a .ged file found at filepath to the formats
    decided by our given converters.

    Args:
        converters ([]Converter): Converter objects (to write output)
        filepath (str):

    Raises:
        IOError: if unable to find / read file
    """
    for c in converters:
        if not issubclass(c.__class__, conv.BaseConverter):
            raise ValueError("All converters must inherit from BaseConverter")

    last_obj = None
    with open(filepath, "r") as f:
            line = " "  # initialize the line to be non-empty
            while line:
                # read one line at a time
                line = f.readline()

                # parse the line into segments
                key, value = _parse_key_value(line)

                # we've reached the definition of a new obj,
                # out with the old, in with the new
                if _is_new_obj_line(key) or key == _KEY_STOP:
                    if last_obj:
                        # Stop downstream converters from changing our obj
                        last_obj.lock()

                        # Call relevant save func of each obj
                        _save(converters, last_obj)

                    if key == _KEY_STOP:
                        break

                    last_obj = _decide_next_obj(key, value)
                    continue

                # probably we're still in the file header
                if not last_obj:
                    continue

                # look up the handler in our handler definitions dicts
                handler, is_multi = _HANDLERS.get(key, (None, None))
                if not handler:
                    last_obj.set_multiline_key(key)
                    continue

                if not is_multi:
                    last_obj.set_multiline_key(None)

                parsed = handler(value)
                last_obj.set_data(key, parsed)

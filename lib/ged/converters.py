import abc
import time
import os
from pprint import pprint
import sqlite3 as lite

from ged import utils


# size limit for the number of objects to hold at once
# before writing out
_CHUNK_SIZE = 100
_NULL_STRING = "None"


class BaseConverter(object):
    """Abstract converter base class"""
    @abc.abstractmethod
    def save_family(self, family):
        """Write out some family obj

        Args:
            family (_Family): obj to save
        """
        pass

    @abc.abstractmethod
    def save_person(self, person):
        """Write out some person obj

        Args:
            person (_Person): obj to save
        """
        pass

    @abc.abstractmethod
    def clear_existing_data(self):
        """Remove any existing data in the output file

        By default implementations should append not remove.

        This function is optional for the user(s) to force "replace"
        behaviour in the output over "append"
        """
        pass

    @staticmethod
    def help_string():
        """Cli help string for this converter

        Returns:
            str
        """
        return ""

    @staticmethod
    def needs_arg():
        """Whether or not this class requires an arg

        Returns:
            bool
        """
        return False

    def load_arg(self, arg):
        """When instantiated the given commadline arg (str)
        will be handed to the class.

        What this means (if anything) is up to the class author.

        Args:
            arg (str):
        """
        pass

    def flush(self):
        pass


class FamilyCsv(BaseConverter):
    """
    FamilyCSV outputs only family data as:
        FamilyID,HusbandId,WifeId,marriage_date
    """
    def __init__(self):
        self._outfile = ""
        self._chunk_size = _CHUNK_SIZE
        self._rows = []
        self._filehandler = None

    def clear_existing_data(self):
        """Remove output file if it exists

        Raises:
            IOError if unable to remove file
        """
        if not self._outfile:
            return

        if not os.path.exists(self._outfile):
            return

        self.flush()
        os.remove(self._outfile)
        self._initialize()

    def flush(self):
        """
        Save any remaining data in memory and close file handler
        """
        if self._rows:
            self._save_current_rows()

        try:
            self._filehandler.close()
        except IOError as e:
            print("Error closing CSV file-handler", e)

    def _initialize(self):
        """
        Open output file
        """
        self._filehandler = open(self._outfile, "a+")

    def _save_current_rows(self):
        """
        Write currently held family data in memory to disk
        """
        self._filehandler.writelines(self._rows)
        self._rows = []

    @staticmethod
    def _family_row(family):
        """Extract csv row of family data from given family

        Args:
            family (_Family): family to extract data from

        Returns:
            str
        """
        return "%s\n" % ",".join([
            family.id or _NULL_STRING,
            family.husband_id or _NULL_STRING,
            family.wife_id or _NULL_STRING,
            "%s-%s-%s" % (
                family.marriage_day,
                family.marriage_month,
                family.marriage_year
            )
        ])

    def save_family(self, family):
        """Write family to disk

        NB, this writes to the csv file in batches of _CHUNKSIZE
        rather than on-demand

        Args:
            family (_Family): family to save

        Raises:
            IOError
        """
        self._rows.append(self._family_row(family))

        if len(self._rows) >= self._chunk_size:
            self._save_current_rows()

    def save_person(self, person):
        pass

    @staticmethod
    def needs_arg():
        return True

    @staticmethod
    def help_string():
        return "Output file path for family csv data (created if doesn't exist)"

    def load_arg(self, arg):
        """When instantiated the given commadline arg (str)
        will be handed to the class.

        What this means (if anything) is up to the class author.

        Args:
            arg (str):
        """
        self._outfile = arg
        self._initialize()


class SqliteConverter(BaseConverter):
    """
    Write out sqlite file
    """
    _CREATE_TABLE_PERSON = """CREATE TABLE IF NOT EXISTS "main"."people" (
        "id" INTEGER PRIMARY KEY NOT NULL,
        "firstname" TEXT NOT NULL,
        "surname" TEXT NOT NULL,
        "married_name" TEXT,
        "aliases" TEXT,
        "given_names" TEXT,
        "is_male" TINYINT NOT NULL,
        "note" TEXT,
        "childhood_family_id" INTEGER,
        "last_updated" INTEGER,
        "birth_place" TEXT,
        "death_place" TEXT,
        "burial_place" TEXT,

        "birth_date_day" INTEGER,
        "birth_date_month" INTEGER,
        "birth_date_year" INTEGER,

        "death_date_day" INTEGER,
        "death_date_month" INTEGER,
        "death_date_year" INTEGER,

        "burial_date_day" INTEGER,
        "burial_date_month" INTEGER,
        "burial_date_year" INTEGER
    );"""

    _INSERT_PERSON = """INSERT OR REPLACE INTO people
      VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? , ? , ?)"""

    _CREATE_TABLE_FAMILY = """CREATE TABLE IF NOT EXISTS "main"."families" (
        "id" INTEGER PRIMARY KEY NOT NULL,
        "husband_id" INTEGER NOT NULL,
        "wife_id" INTEGER NOT NULL,
        "marriage_day" INTEGER,
        "marriage_month" INTEGER,
        "marriage_year" INTEGER,
        "marriage_place" TEXT,
        "note" TEXT
    );"""

    _CREATE_TABLE_HASH = """CREATE TABLE IF NOT EXISTS "main"."hash" (
        "date_unix_epoch" INTEGER NOT NULL,
        "source" TEXT PRIMARY KEY NOT NULL,
        "hash" TEXT NOT NULL
    );"""

    _INSERT_FAMILY = """INSERT OR REPLACE INTO families
      VALUES(?, ?, ?, ?, ?, ?, ?, ?)"""

    _CLEAR_TABLE_PERSON = """DROP TABLE people;"""
    _CLEAR_TABLE_FAMILY = """DROP TABLE families;"""

    def __init__(self):
        self._outfile = ""
        self._chunk_size = _CHUNK_SIZE
        self._f_rows = []
        self._p_rows = []

        self._conn = None
        self._cur = None

    def clear_existing_data(self):
        """Remove output file if it exists

        Raises:
            IOError if unable to remove file
        """
        if not self._outfile:
            return

        if not os.path.exists(self._outfile):
            return

        self._cur.execute(self._CLEAR_TABLE_PERSON)
        self._cur.execute(self._CLEAR_TABLE_FAMILY)
        self._conn.commit()
        self._create_tables()

    def last_hash(self, filename):
        """
        """
        self._cur.execute("""SELECT date_unix_epoch,
                                    source,
                                    hash
            FROM hash
            WHERE source=?
            LIMIT 1;
            """, (filename,))
        rows = self._cur.fetchall()
        if len(rows) == 1:
            return rows[0][2]
        return None

    def set_last_hash(self, filename, hash):
        """save filename, hash, current time tuple
        """
        self._cur.execute(
                'INSERT OR REPLACE INTO hash VALUES (?, ?, ?);',
                (int(time.time()), filename, hash),
        )
        self._conn.commit()

    def flush(self):
        """
        Flush all remaining data to disk, close db connection
        """
        if self._p_rows:
            self._save_current_people()

        if self._f_rows:
            self._save_current_families()

        try:
            self._conn.close()
        except IOError as e:
            print("Error closing sqlite connection", e)

    def _create_tables(self):
        """
        Creates our required tables if they don't already exist
        """
        self._cur.execute(self._CREATE_TABLE_PERSON)
        self._cur.execute(self._CREATE_TABLE_FAMILY)
        self._cur.execute(self._CREATE_TABLE_HASH)

    def _initialize(self):
        """
        Open connection to db, create tables if they don't exist
        """
        self._conn = lite.connect(self._outfile)
        self._cur = self._conn.cursor()
        self._create_tables()

    @staticmethod
    def help_string():
        return "Output file path (created if doesn't exist)"

    @staticmethod
    def needs_arg():
        return True

    @staticmethod
    def _family_values(family):
        """Extract sql row data from family

        Args:
            family (_Family):

        Returns:
            []Object
        """
        return [
            utils.force_int(family.id),
            utils.force_int(family.husband_id),
            utils.force_int(family.wife_id),
            family.marriage_day,
            family.marriage_month,
            family.marriage_year,
            family.marriage_place,
            ""
        ]

    @staticmethod
    def _person_values(person):
        """Extract sql row data from person

        Args:
            person (_Person): obj to extract values from

        Returns:
            []Object
        """
        gender = 0
        if person.is_male:
            gender = 1

        return [
            utils.force_int(person.id),
            person.firstname,
            person.surname,
            person.married_name,
            "|".join(person.nicknames),
            "|".join(person.given_names),
            gender,
            person.note,

            utils.force_int(person.childhood_family_id),
            utils.date_to_epoch(person.last_updated),

            person.birth_place,
            person.death_place,
            person.burial_place,

            person.birth_day,
            person.birth_month,
            person.birth_year,

            person.death_day,
            person.death_month,
            person.death_year,

            person.burial_day,
            person.burial_month,
            person.burial_year,
        ]

    def _save_current_people(self):
        """
        Flush person data currently held in memory to disk
        """
        self._cur.executemany(
            self._INSERT_PERSON,
            self._p_rows
        )
        self._conn.commit()
        self._p_rows = []

    def _save_current_families(self):
        """
        Flush family data currently held in memory to disk
        """
        self._cur.executemany(
            self._INSERT_FAMILY,
            self._f_rows
        )
        self._conn.commit()
        self._f_rows = []

    def save_family(self, family):
        """Queue up family row to be saved

        Args:
            family (_Family): family to save
        """
        self._f_rows.append(self._family_values(family))
        if len(self._f_rows) >= self._chunk_size:
            self._save_current_families()

    def save_person(self, person):
        """Queue up person row to be saved

        Args:
            person (_Person): person to save
        """
        self._p_rows.append(self._person_values(person))
        if len(self._p_rows) >= self._chunk_size:
            self._save_current_people()

    def load_arg(self, arg):
        """When instantiated the given commadline arg (str)
        will be handed to the class.

        What this means (if anything) is up to the class author.

        Args:
            arg (str):
        """
        self._outfile = arg
        self._initialize()


class PrintConverter(BaseConverter):
    """
    The 'hello world' converter: reads in ged file & prints to stdout
    """
    def save_family(self, family):
        pprint(family.to_string())

    def save_person(self, person):
        pprint(person.to_string())

    @staticmethod
    def help_string():
        return "Print data to shell [default if no converter selected]"

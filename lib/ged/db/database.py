import os

import sqlite3 as lite

from ged.db import classes


class Database:
    """Simple object to wrap our db logic
    """

    def __init__(self, input):
        """Create new db given some db input filepath
        """
        self._conn = lite.connect(input)
        self._cur = self._conn.cursor()

    def get_families(self):
        """Fetch families, joining People to fill in names / birth / death dates.
        """
        self._cur.execute("""SELECT
	    f.id as mrin,
	    f.husband_id,
    	    f.wife_id,
	    f.marriage_day,
	    f.marriage_month,
	    f.marriage_year,
	    ph.firstname,
	    ph.surname,
	    ph.birth_date_day,
	    ph.birth_date_month,
	    ph.birth_date_year,
	    ph.birth_place,
	    ph.death_date_day,
	    ph.death_date_month,
	    ph.death_date_year,
	    ph.death_place,
	    pw.firstname,
	    pw.surname,
	    pw.birth_date_day,
	    pw.birth_date_month,
	    pw.birth_date_year,
	    pw.birth_place,
	    pw.death_date_day,
	    pw.death_date_month,
	    pw.death_date_year,
	    pw.death_place
        FROM "main"."families" as f
        JOIN "main"."people" as ph ON (f.husband_id == ph.id)
        JOIN "main"."people" as pw ON (f.wife_id == pw.id)
        """)
        return[classes.Family(row) for row in self._cur.fetchall()]

    def get_people_by_id(self, ids):
        """Fetch people by their IDs
        """
        pids = ", ".join([str(i) for i in ids])
        self._cur.execute("""SELECT id,
                                    firstname,
                                    surname,
                                    childhood_family_id
                                    birth_date_day,
                                    birth_date_month,
                                    birth_date_year
            FROM "main"."people"
            WHERE id IN (%s)""" % pids)
        return self._cur.fetchall()

    def get_children_by_families(self, ids):
        """Get the children of the given family ID(s).
        """
        pids = ", ".join([str(i) for i in ids])
        self._cur.execute(
            """SELECT id,firstname,surname,childhood_family_id
               FROM "main"."people"
               WHERE childhood_family_id IN (%s)
               """ % (pids))
        return self._cur.fetchall()

    def get_children_by_parents(self, ids):
        """Get the children (if any) of the given people
        """
        pids = ", ".join([str(i) for i in ids])
        self._cur.execute(
            """SELECT id,firstname,surname,married_name,childhood_family_id,birth_date_day,birth_date_month,birth_date_year
               FROM "main"."people"
               WHERE childhood_family_id IN (
                  SELECT id
                  FROM "main"."families"
                  WHERE husband_id in (%s)
                  OR wife_id in (%s)
               )""" % (pids, pids))
        return self._cur.fetchall()

    def get_families_by_parents(self, ids):
        """Get families by the ids of their parents (husband / wife)
        """
        pids = ", ".join([str(i) for i in ids])
        self._cur.execute(
            """SELECT fam.id,fam.husband_id,fam.wife_id,hus.firstname,hus.surname,wif.firstname,wif.surname
                FROM "main"."families" as fam
                JOIN "main"."people" as hus ON (fam.husband_id == hus.id)
                JOIN "main"."people" as wif ON (fam.wife_id == wif.id)
                WHERE husband_id in (%s) OR wife_id in (%s)
            """ % (pids, pids))
        return self._cur.fetchall()

    def close(self):
        """Close db file
        """
        try:
            self._cur.close()
        except:
            pass


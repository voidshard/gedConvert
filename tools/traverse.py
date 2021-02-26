#!/usr/bin/python
"""Traverse a family SQLite database file for all descendants of given people.
"""

from argparse import ArgumentParser

import os
import sqlite3 as lite


class Trawler:
    """Simple object to wrap our db logic
    """

    def __init__(self, input):
        """Create new trawler given some db input filepath
        """
        self._conn = lite.connect(args.input)
        self._cur = self._conn.cursor()

    def _get_people(self, ids):
        """Fetch people by their IDs
        """
        pids = ", ".join([str(i) for i in ids])
        self._cur.execute("""SELECT id,
                                    firstname,
                                    surname,
                                    married_name,
                                    childhood_family_id
            FROM "main"."people"
            WHERE childhood_family_id IN (%s)""" % pids)
        return self._cur.fetchall()

    def _get_children(self, ids):
        """Get the children (if any) of the given people
        """
        pids = ", ".join([str(i) for i in ids])
        self._cur.execute(
            """SELECT id,firstname,surname,married_name,childhood_family_id
               FROM "main"."people"
               WHERE childhood_family_id IN (
                  SELECT id
                  FROM "main"."families"
                  WHERE husband_id in (%s)
                  OR wife_id in (%s)
               )""" % (pids, pids))
        return self._cur.fetchall()

    def trawl(self, ids):
        """Find all descendants of the given people (by their IDs)
        """
        # first, get information on the given starting people
        for p in self._get_people(ids):
            print(k)

        # prep a stack that we'll use to track who we should check next
        stack = ids

        while stack:
            # fetch children on those currently on the stack
            kids = self._get_children(stack)

            # reset the stack
            stack = []

            # add everyone we just found to the stack as we print them out
            for k in kids:
                stack.append(k[0])
                print(k)

    def close(self):
        """Close db file
        """
        try:
            self._cur.close()
        except:
            pass


def readfile(fpath):
    """Read nonblank lines from a file
    """
    with open(fpath, "r") as f:
        return [l.strip() for l in f.readlines() if l.strip()]


def parse_args():
    """Parse cli args
    """
    ps = ArgumentParser(description=__doc__)
    ps.add_argument("-i", "--input", help="SQLite database file")
    ps.add_argument("--ids", help="File of person ID(s), one per line")
    return ps.parse_args()


if __name__ == "__main__":
    # parse commmand line args
    args = parse_args()

    # instantiate a new trawler & pass in the database file path
    t = Trawler(args.input)

    # ask it to trawl & pass the starting person ids
    t.trawl(readfile(args.ids))

    # close the db connection
    t.close()

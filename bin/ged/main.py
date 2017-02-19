#!/usr/bin/python
"""
"""
import glob
import os
import sys
import hashlib
import warnings

from argparse import ArgumentParser

warnings.simplefilter("ignore") # squash warnings from inside evol.parser
import ete3
warnings.simplefilter("default")


def _dirname(count, src):
    for i in range(count):
        src = os.path.dirname(src)
    return src

sys.path.insert(0, os.path.join(_dirname(3, __file__), "lib"))
from ged.db import database
from ged import converters as conv
from ged import utils
from ged import ged_parser


_BLOCKSIZE = 5000

# Available "converters" arranged
# str: (class, bool)
# where,
#  str: converter name
#  class: converer class (sub class of _DBObj)
#  bool: whether or not it needs arguments given to it
# Note, names will need to be alpha only
_CONVERTERS = {
    "print": (conv.PrintConverter, conv.PrintConverter.needs_arg()),
    "sqlite": (conv.SqliteConverter, conv.SqliteConverter.needs_arg()),
    "familyCsv": (conv.FamilyCsv, conv.FamilyCsv.needs_arg()),
}

# The prefix used to make the cli arg
_CONV_ARG_PREFIX = "to"

# By default, we use this to print data to shell
_DEFAULT_CONVERTER = conv.PrintConverter


def parse_args():
    """Parse sys.argv for our arguments
    """
    ps = ArgumentParser(description=__doc__)
    ps.add_argument("--input", help="Input .ged (.paf) file. If not given we search the current directory.")

    subparsers = ps.add_subparsers(help="")

    # -- tree command
    tree = subparsers.add_parser("tree", help="Generate family trees starting with some person ID")
    tree.add_argument("-i", "--id", required=True, type=int, help="ID of person to start with")
    tree.add_argument("-g", "--generations", default=0, type=int, help="Number of generations tree should span. By default: all")
    tree.add_argument("-o", "--output", help="name of output image (.png)")
    tree.add_argument("--height", type=int, help="height of output image in pixels")
    tree.add_argument("--width", type=int, help="width of output image in pixels")
    tree.set_defaults(func=cmd_tree)

    # -- parse / convert command
    parse = subparsers.add_parser("convert", help="Convert input ancestory data file to various formats.")
    parse.add_argument(
        "-r",
        "--replace",
        action="store_true",
        help="Remove data in output files (if any) rather than append. WARNING: DESTROYS DATA."
    )
    # Add our Converter args dynamically
    for conv_name in _CONVERTERS:
        clas, needs_arg = _CONVERTERS.get(conv_name)
        arg = '--%s-%s' % (_CONV_ARG_PREFIX, conv_name)
        hlp = clas.help_string()
        if needs_arg:
            parse.add_argument(arg, help=hlp)
        else:
            parse.add_argument(arg, action='store_true', help=hlp)
    parse.set_defaults(func=cmd_convert)

    # -- "pioneer" command
    pio = subparsers.add_parser("pioneer", help="Print all data as a custom tsv")
    pio.set_defaults(func=cmd_pioneer)

    # -- "traverse" command
    trav = subparsers.add_parser("traverse", help="Traverse all descendants of given people")
    trav.add_argument("--ids", help="File of person ID(s), one per line", required=True)
    trav.set_defaults(func=cmd_traverse)

    args = ps.parse_args()

    if not args.input:
        # if input not given, attempt to discover it
        args.input = discover()
        if not args.input:
            sys.exit(0)

    return args


def readfile(fpath):
    """Read nonblank lines from a file
    """
    with open(fpath, "r") as f:
        return [l.strip() for l in f.readlines() if l.strip()]


def cmd_traverse(args):
    """
    """
    ids = readfile(args.ids)
    if len(ids) == 0:
        return

    dbfile = ensure_database(args.input)
    dbase = database.Database(dbfile)

    def _print_row(r):
        birthdate = f"{r[-3]}-{r[-2]}-{r[-1]}"
        fields = [str(i) for i in list(r)[0:-3]]
        print("%s,%s" % (",".join(fields), birthdate))

    # first, get information on the given starting people
    for p in dbase.get_people_by_id(ids):
        _print_row(p)

    # prep a stack that we'll use to track who we should check next
    stack = ids

    while stack:
        # fetch children on those currently on the stack
        kids = dbase.get_children_by_parents(stack)

        # reset the stack
        stack = []

        # add everyone we just found to the stack as we print them out
        for k in kids:
            stack.append(k[0])
            _print_row(k)

def cmd_pioneer(args):
    """
    """
    dbfile = ensure_database(args.input)
    dbase = database.Database(dbfile)

    fams = dbase.get_families()
    if len(fams) == 0:
        return

    print(fams[0].row_header())
    for f in fams:
        print(f.tsv())


def cmd_tree(args):
    """argparser 'tree' command
    """
    dbfile = ensure_database(args.input)

    if args.generations > 0:
        print(f"building tree starting with {args.id} for {args.generations} generations")
    else:
        print(f"building tree starting with {args.id}")

    tree, style = build_tree(dbfile, [args.id], args.generations)

    opts = {"units": "px", "tree_style": style}
    if args.height:
        opts["h"] = args.height
    if args.width:
        opts["w"] = args.width
    if not args.output:
        args.output = f"familytree.{args.id}.{args.generations}.png"

    warnings.simplefilter("ignore") # squash warnings about int vs float in ete3.evol
    tree.render(args.output, **opts)
    warnings.simplefilter("default")

    print(f"rendered {args.output}")


def cmd_convert(args):
    """argparser 'convert' command
    """
    converters = []
    for name in _CONVERTERS:
        arg = getattr(args, "%s_%s" % (_CONV_ARG_PREFIX, name))
        clas, needs_arg = _CONVERTERS.get(name)

        if not arg:
            continue

        # instantiate new converter
        converter = clas()

        # load given arg & initialize class
        converter.load_arg(arg)

        # possibly trigger the --replace function
        if args.replace:
            converter.clear_existing_data()

        # add to our list of converters
        converters.append(converter)

    # if we have nothing selected, we'll just print
    if not converters:
        converters = [_DEFAULT_CONVERTER()]

    try:
        # parse the file and pass in our converters to do their stuff
        ged_parser.parse_ged_file(converters, args.input)
    finally:
        # flush the converters so they can finish what they're doing
        for converter in converters:
            converter.flush()


def discover():
    """Tries to find an input .ged / .paf file
    """
    print(f"Data file not specified, searching current directory ({os.getcwd()}) for .ged & .paf files")

    found = glob.glob("*.paf") + glob.glob("*.ged")
    if found:
        print(f"\tfound: {found}")

    if len(found) == 0:
        print(f"No data files? Perhaps try:\n\t{sys.argv[0]} --input my_paf_file.paf")
        return None
    elif len(found) > 1:
        print(f"Found {len(found)} data files. You'll need to pick one, for example:")
        print(f"\t{sys.argv[0]} --input {found[0]}")
        return None

    print(f"Assuming you want to use data file {found[0]}")
    return found[0]


def hash_file(filename):
    """Generate an md5 hash for some file (by it's contents)
    """
    hasher = hashlib.md5()
    with open(filename, 'rb') as afile:
        buf = afile.read(_BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(_BLOCKSIZE)
    return hasher.hexdigest()


def main(args):
    if not hasattr(args, "func"):
        # if the user doesn't pick a function, we'll call "parse"
        cmd_parse(args)
        return

    args.func(args)


def build_tree(dbfile, seed_ids, generations):
    """Find all descendants of the given people (by their IDs) and
    build into a lovely tree.
    """
    dbase = database.Database(dbfile)

    tree = ete3.Tree()

    nodes_people = {}
    nodes_families = {}

    # first, get information on the given starting people
    ids = []
    for p in dbase.get_people_by_id(seed_ids):
        nodes_people[p[0]] = tree.add_child(name=f"{p[1]} {p[2]}")
        ids.append(p[0])

    gens = 0
    while ids:
        # look up families
        family_ids = []
        families = dbase.get_families_by_parents(ids)
        for f in families:
            husband = nodes_people.get(f[1])
            wife = nodes_people.get(f[2])

            if husband:
                fn = husband.add_child(name=f"+{f[5]} {f[6]}")
            elif wife:
                fn = wife.add_child(name=f"+{f[3]} {f[4]}")

            nodes_families[f[0]] = fn
            family_ids.append(f[0])

        # fetch children on those currently on the stack
        kids = dbase.get_children_by_families(family_ids)

        # reset the stack
        ids = []

        # add everyone we just found to the stack as we print them out
        for k in kids:
            ids.append(k[0])

            fam = nodes_families[k[3]]
            nodes_people[k[0]] = fam.add_child(name=f"{k[1]} {k[2]}")

        # check if we should quit
        gens += 1
        if generations > 0 and gens >= generations:
            break

    ts = ete3.treeview.TreeStyle()
    ts.show_leaf_name = False
    ts.mode = "c"
    ts.arc_start = -180 # 0 degrees = 3 o'clock
    ts.arc_span = 180

    def my_layout(node):
        face = ete3.TextFace(node.name, tight_text=True)
        ete3.add_face_to_node(face, node, column=0, position="branch-right")

    ts.layout_fn = my_layout
    dbase.close()

    return tree, ts


def ensure_database(datafile):
    """read the given datafile (.ged / .paf) and write us an .sqlite db file.
    """
    # load up the corresponding database file (if any)
    dbfile = datafile + ".sqlite"

    slite = conv.SqliteConverter()
    slite.load_arg(dbfile)

    # check if our db file is up to date
    current_hash = hash_file(datafile)
    last_read_hash = slite.last_hash(datafile)

    # if not up to date, re-parse the data
    if current_hash != last_read_hash:
        print(f"Looks like {datafile} has changed since I last read it, reparsing...")
        try:
            ged_parser.parse_ged_file([slite], datafile)
            slite.set_last_hash(datafile, current_hash)
        finally:
            slite.flush()
        print("- done")
    else:
        print(f"Database looks to be up-to-date with {datafile}, skipping reparsing")

    return dbfile


if __name__ == "__main__":
    main(parse_args())

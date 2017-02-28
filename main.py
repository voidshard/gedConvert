#!/usr/bin/python
"""
Parse a .ged file into other format(s).

Feel free to add your own classes to convert to (a "Converter" class).
"""

from argparse import ArgumentParser

from ged_parser import parse_ged_file
import converters as conv


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
    """
    Parse sys.argv for our arguments
    """
    ps = ArgumentParser(description=__doc__)
    ps.add_argument("-i", "--input", required=True, help="Input .ged file [required]")
    ps.add_argument(
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
            ps.add_argument(arg, help=hlp)
        else:
            ps.add_argument(arg, action='store_true', help=hlp)

    return ps.parse_args()


def main(args):
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
        parse_ged_file(converters, args.input)
    finally:
        # flush the converters so they can finish what they're doing
        for converter in converters:
            converter.flush()


if __name__ == "__main__":
    main(parse_args())

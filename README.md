Simple script to read / convert family ancestral data files (.ged) to other format(s)


Example of reading in "all.ged" and writing out an sqlite db file "all.sqlite"
```
python ./main.py -i all.ged --to-sqlite all.sqlite
```

```
usage: main.py [-h] -i INPUT [-r] [--to-print] [--to-familyCsv TO_FAMILYCSV]
               [--to-sqlite TO_SQLITE]

Parse a .ged file into other format(s). Feel free to add your own classes to
convert to (a "Converter" class).

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input .ged file [required]
  -r, --replace         Remove data in output files (if any) rather than
                        append. WARNING: DESTROYS DATA.
  --to-print            Print data to shell [default if no converter selected]
  --to-familyCsv TO_FAMILYCSV
                        Output file path for family csv data (created if
                        doesn't exist)
  --to-sqlite TO_SQLITE
                        Output file path (created if doesn't exist)
```

You can write to multiple output(s) at once.


There is also the ability to extend the script with your own classes using an interface provided if
you need some other form of output.


Notes,
- Dates are kept internally as int or None values for each of 'day' 'month' and 'year' to combat incomplete data
- Parser only keeps small chunks of the input in memory at any one time so it should handle large data sets

Please push code up if,
- You add more classes to extend functionality
- You improve anything!
- You find bugs (Please also send the err(s) & some (small) test datafile to repro the bug with)


Bugs fixed,
- Bug where the last obj record would not be saved
- Parser using silly defaults instead of simply 'None' (whose idea WAS that anyway ..)

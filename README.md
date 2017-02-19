Simple script to read / convert family ancestral data files (.ged) to other format(s)


Example of reading in "all.ged" and writing out an sqlite db file "all.sqlite"
{code: python}
python ./main.py -i all.ged --to-sqlite all.sqlite
{code}

{code: python}
usage: main.py [-h] -i INPUT [--to-print] [--to-familyCsv TO_FAMILYCSV]
               [--to-sqlite TO_SQLITE]

Parse a .ged file into other format(s). Feel free to add your own classes to
convert to (a "Converter" class).

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input .ged file [required]
  --to-print            Print data to shell [default if no converter selected]
  --to-familyCsv TO_FAMILYCSV
                        Output file path for family csv data (created if
                        doesn't exist)
  --to-sqlite TO_SQLITE
                        Output file path (created if doesn't exist)
{code}

You can write to multiple output(s) at once.


There is also the ability to extend the script with your own classes using an interface provided if
you need some other form of output.


Notes,
- Parser attempts to continue when incomplete data is provided using default values, results may be strange
  and require fixing - I can change what the script defaults to but 'null' is hard to extract data from
- Parser only keeps small chunks of the input in memory at any one time so it should handle large data sets
- If you add more classes, please push the code up
- If you find bugs, please send the err(s) & some (small) test datafile to repro the bug with

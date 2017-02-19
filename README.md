Simple script to read / convert family ancestral data files (.ged) to other format(s)


Example of reading in "all.ged" and writing out an sqlite db file "all.sqlite"
```
python ./bin/ged/main.py -i all.ged convert --to-sqlite all.sqlite
```
You can write to multiple output(s) at once.

There is also the ability to extend the script with your own classes using an interface provided if
you need some other form of output.


Example of generating a family tree (.png) from some data (starting with person ID 2301, going 4 generations)
```
python ./bin/ged/main.py tree --id 2301 --generations 4
```


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
- Bug where a list and int were compared rather than len(list)
- Fix edge case where a family record can be missing a husband / wife id (???)

Improvements,
- Rolled multiple tools into a single main as sub commands
- Added ability to draw family trees (requires ete3 package)
- Added ability to auto detect ancestory data files if not given

# mgit

Handle multiple git repositories at the same time with a single command.


## Installation

Clone the repository on your computer and initialize Git submodules by running the following command:
```bash
git submodule init
git submodule update
```

Finally, simply put the cloned directory in your PATH.
You will need python 3.6 or newer installed too.


## Usage

Go in the directory where multiple GIT repos reside and then invoke this script instead of `git`.
For instance, you can fetch all repos in directory `SRC` using this command:
```bash
cd SRC
mgit.py fetch
```

You can use any git command arguments freely as the aim of this script is simply to invoke git with your options in all subdirectories that are git repos.

You can also pass some arguments to the script by separating them using `--`.
For instance, the same command than above can be ran anywhere using:
```bash
mgit.py SRC -- fetch
```

# Filtering

To specify `mgit` scope, one can create a filtering file and pass it to `mgit` using `--filtering-file` option.

Content must be repositories to handle, one per line.
It support comments using `#`, what follows this sign will be removed (line by line).
All spaces will be trimmed, so you can indent it as you want.

For instance:
```
# A comment can be here.
repo1
repo2
# not handled repo3 because...
```

It is possible to disable the filtering using the `--no-filtering` option; and it is possible to invert filter by using `--invert-filtering` option.

If you want a more "permanent" behavior, one can create a `.mgit_filter` file at the root of your repositories. This file will be loaded automatically unless `--no-filtering` or an explicit `--filter-file`  is specified. When using `.mgit_filter` file, `mget` will always ask for confirmation before starting (WIP).

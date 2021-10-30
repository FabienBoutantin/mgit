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

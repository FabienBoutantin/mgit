#!/usr/bin/env python3
# -*- coding:utf-8 -*-


import pathlib
import subprocess
import sys
import os
import shutil
import contextlib
from collections import defaultdict
import argparse


@contextlib.contextmanager
def working_directory(path):
    """Changes working directory and returns to previous on exit."""
    prev_cwd = pathlib.Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def get_cli_arguments(arguments, print_usage=False):
    parser = argparse.ArgumentParser(
        usage='%(prog)s [options] [DIR [DIR]] -- GIT_ARGUMENTS',
        epilog="If no option needed, simply use: %(prog)s GIT_ARGUMENTS"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true", dest="verbose", help="make lots of noise"
    )
    parser.add_argument(
        "directories", metavar="DIR", nargs="+", help="Directory to analyze."
    )
    arguments = parser.parse_args(arguments)
    if len(arguments.directories) == 0:
        arguments.directories = [".", ]
    if print_usage:
        parser.print_usage()
        print("For more help, use the -h/--help argument.")
        exit(1)
    return arguments


def get_split_arguments():
    git_cmd = ["git", ]
    if "--" in sys.argv:
        script_args = sys.argv[:sys.argv.index("--")]
        git_cmd += sys.argv[sys.argv.index("--") + 1:]
    else:
        if "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
            script_args = sys.argv[1:]
            git_cmd += []
        else:
            script_args = ["."]
            git_cmd += sys.argv[1:]
    return script_args, git_cmd


def main():
    returned_codes = defaultdict(list)
    script_args, git_cmd = get_split_arguments()

    options = get_cli_arguments(script_args, len(git_cmd) <= 1)
    dirs_to_handle = list()
    for root_dir in options.directories:
        root_dir = pathlib.Path(root_dir)

        if (root_dir / ".git").is_dir():
            dirs_to_handle.append(root_dir)

        for d in sorted(root_dir.glob("*")):
            if not (d / ".git").is_dir():
                continue
            dirs_to_handle.append(d)

    print(f"Run this command on {len(dirs_to_handle)} directories: {' '.join(git_cmd)}")
    for d in dirs_to_handle:
        print("=" * shutil.get_terminal_size((80, 20)).columns)
        print(f"handling {d}", flush=True)
        with working_directory(d):
            r = subprocess.run(git_cmd)
            print(f"Command finished with return code: {r.returncode}")
            returned_codes[r.returncode].append(d)
    print("#" * shutil.get_terminal_size((80, 20)).columns)
    print("Summary per return code:")
    for x in sorted(returned_codes):
        print(f" * {x}: {len(returned_codes[x])} repos")
    return 0


if __name__ == "__main__":
    exit(main())

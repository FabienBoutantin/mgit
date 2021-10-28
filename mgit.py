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
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "-v", "--verbose",
        action="store_true", dest="verbose", help="make lots of noise"
    )
    verbosity_group.add_argument(
        "-q", "--quiet",
        action="store_true", dest="quiet",
        help="display output of failing commands only"
    )
    parser.add_argument(
        "directories",
        metavar="DIR", nargs="+",
        help="Directory to analyze."
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

    if options.verbose:
        print(f"Run this command on {len(dirs_to_handle)} directories: {' '.join(git_cmd)}")
    for d in dirs_to_handle:
        msg = f"handling {d}"
        if options.quiet:
            print("* ", end="")
        elif options.verbose:
            print("~" * shutil.get_terminal_size((80, 20)).columns)
        else:
            print("~" * len(msg))
        print(msg, flush=True)
        with working_directory(d):
            if options.quiet:
                try:
                    subprocess.check_output(git_cmd, stderr=subprocess.STDOUT)
                    r = 0
                except subprocess.CalledProcessError as e:
                    r = e.returncode
                    print(e.output.decode("utf-8"), end="")
            else:
                r = subprocess.run(git_cmd).returncode
            if options.verbose or (r != 0):
                print(f">>> return code: {r}")
            returned_codes[r].append(d)
    if not options.quiet:
        msg = "Summary per return code:"
        print()
        if options.verbose:
            print("=" * shutil.get_terminal_size((80, 20)).columns)
        else:
            print("=" * len(msg))
        print(msg)
        for x in sorted(returned_codes):
            if options.verbose:
                print(f" * {x}: {', '.join(map(str, returned_codes[x]))}")
            else:
                print(f" * {x}: {len(returned_codes[x])} repo(s)")
    return 0


if __name__ == "__main__":
    exit(main())

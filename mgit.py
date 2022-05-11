#!/usr/bin/env python3
# -*- coding:utf-8 -*-


from pathlib import Path
import subprocess
import sys
import os
import shutil
import contextlib
from collections import defaultdict
from argparse import ArgumentParser

import PythonColorConsole.color_console as color_console


@contextlib.contextmanager
def working_directory(path):
    """Changes working directory and returns to previous on exit."""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def _get_cli_parser():
    """Returns an argument Parser ready to parse command line"""
    parser = ArgumentParser(
        usage='%(prog)s [options] [DIR [DIR]] -- GIT_ARGUMENTS',
        epilog="If no option needed, simply use: %(prog)s GIT_ARGUMENTS"
    )
    filtering_group = parser.add_argument_group("Filtering")
    filtering_group.add_argument(
        "-f", "--filtering-file",
        action="append", dest="filtering_files",
        help="Filtering File(s)"
    )
    filtering_group.add_argument(
        "-F", "--no-filtering",
        action="store_true", dest="no_filtering",
        help="Not using Filtering"
    )
    filtering_group.add_argument(
        "-I", "--invert-filtering",
        action="store_true", dest="invert_filtering",
        help="Invert Filtering behavior"
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
    return parser


def _process_args_directories(arguments):
    """Creates a consolidated list of directories to handle"""
    # Check directories:
    if len(arguments.directories) == 0:
        arguments.directories = [".", ]
    # convert to pathlib objects
    arguments.directories = tuple(
        map(Path, arguments.directories)
    )
    return arguments


def _process_args_filtering_files(arguments):
    """Creates a consolidated list of filtering files"""
    if not arguments.filtering_files:
        arguments.filtering_files = []
    else:
        arguments.filtering_files = tuple(
            map(Path, arguments.filtering_files)
        )
        arguments.filtering_elements = set()
        for f in arguments.filtering_files:
            if not f.is_file():
                print(f"Error: filtering file {f} does not exist")
                exit(1)
    return arguments


def get_cli_arguments(command_arguments: list, print_usage=False):
    """Parses given mgit command_arguments"""
    parser = _get_cli_parser()
    try:
        arguments = parser.parse_intermixed_args(command_arguments)
    except AttributeError:
        arguments = parser.parse_args(command_arguments)

    if print_usage:
        parser.print_usage()
        print("For more help, use the -h/--help argument.")
        exit(1)

    arguments = _process_args_directories(arguments)
    arguments = _process_args_filtering_files(arguments)

    return arguments


def get_split_arguments():
    """Splits the command line in 2: the mgit options and the git command"""
    git_cmd = ["git", ]
    if "--" in sys.argv:
        script_args = sys.argv[1:sys.argv.index("--")]
        git_cmd += sys.argv[sys.argv.index("--") + 1:]
    else:
        if "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
            script_args = sys.argv[1:]
            git_cmd += []
        else:
            script_args = ["."]
            git_cmd += sys.argv[1:]
    return script_args, git_cmd


def handle_directory(
    directory: Path,
    cc: color_console,
    options,
    git_cmd: list
):
    """Runs the given git_cmd on the given directory"""
    msg = f"handling {directory}"
    cc.cyan()
    if options.quiet:
        print("* ", end="")
    elif options.verbose:
        print("~" * shutil.get_terminal_size((80, 20)).columns)
    else:
        print("~" * len(msg))
    cc.bold()
    cc.blue()
    print(msg, flush=True)
    cc.reset()
    with working_directory(directory):
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
            if r == 0:
                cc.green()
            else:
                cc.bold()
                cc.red()
            print(f">>> return code: {r}")
            cc.reset()
    return r


def read_filtering_files(list_of_files: list):
    """Returns a set of all items to filter defined in given files."""
    result = set()
    for f in list_of_files:
        with open(f, "rt") as fd:
            for line in fd:
                # remove comments and strip line
                line = line.split("#")[0].strip()
                if line != "":
                    result.add(line)
    return result


def _filter_directory(d: Path, filtering_rules: set, options):
    """According to options, tells if a file must be filtered or not."""
    if not filtering_rules or options.no_filtering:
        return False
    if options.invert_filtering:
        return d.parts[-1] in filtering_rules
    else:
        return d.parts[-1] not in filtering_rules


def compute_list_of_dirs_to_handle(options, cc: color_console):
    """Yields a list of directories to handle, given the CLI and filtering"""
    for root_dir in options.directories:
        # Compute filtering stuff
        filtering_elements = read_filtering_files(options.filtering_files)
        default_filtering_file = root_dir / ".mgit_filter"
        if not options.filtering_files and default_filtering_file.is_file():
            if not cc.acknowledgment(
                f"default filtering file found in '{root_dir}', continue?"
            ):
                exit(1)
            filtering_elements = read_filtering_files(
                [default_filtering_file]
            )

        # Loop on all possible sub items:
        items = [root_dir, ] + sorted(root_dir.glob("*"))
        for d in items:
            if not (d / ".git").is_dir():
                continue
            if not _filter_directory(d, filtering_elements, options):
                yield d


def print_summary(returned_codes: dict, cc: color_console, options):
    """According to options, prints the summary of the execution"""
    cc.bold()
    msg = "Summary per return code:"
    print()
    if options.verbose:
        print("=" * shutil.get_terminal_size((80, 20)).columns)
    else:
        print("=" * len(msg))
    print(msg)
    cc.reset()
    for x in sorted(returned_codes):
        if x == 0:
            cc.green()
        else:
            cc.red()
        if options.verbose or x != 0:
            print(f" * {x}: {', '.join(map(str, returned_codes[x]))}")
        else:
            print(f" * {x}: {len(returned_codes[x])} repo(s)")
    cc.reset()


def main():
    cc = color_console.ColorConsole()
    returned_codes = defaultdict(list)
    script_args, git_cmd = get_split_arguments()

    options = get_cli_arguments(script_args, len(git_cmd) <= 1)
    dirs_to_handle = list(
        compute_list_of_dirs_to_handle(options, cc)
    )

    if options.verbose:
        cc.yellow()
        print(
            f"Run this command on {len(dirs_to_handle)} directories:",
            f"{' '.join(git_cmd)}"
        )
        cc.reset()
    for d in dirs_to_handle:
        r = handle_directory(d, cc, options, git_cmd)
        returned_codes[r].append(d)
    if not options.quiet:
        print_summary(returned_codes, cc, options)
    return 0


if __name__ == "__main__":
    exit(main())

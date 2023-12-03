import sys
import argparse
from pathlib import Path

from .split import split_file_into_module


def argparser():
    parser = argparse.ArgumentParser(
        description="Split a Python file into separate modules"
    )
    parser.add_argument("filename", help="The Python file to split")
    return parser


def main():
    args = argparser().parse_args()
    created_filenames = split_file_into_module(args.filename)
    print(
        f"Created files: {', '.join(map(str, created_filenames))} from {args.filename}."
    )

    # create a new dir now named after the original file
    directory = Path(args.filename).stem
    Path(directory).mkdir(exist_ok=True)
    print(f"Created directory: {directory}")

    # move the original file into the new dir
    for name in created_filenames:
        Path(name).rename(Path(directory) / name)
    print(f"Moved {created_filenames} into {directory}")


if __name__ == "__main__":
    main()

import sys
from argparse import ArgumentParser, Namespace

from skactiveml_annotation import util
from skactiveml_annotation import commands


def parse_args() -> tuple[Namespace, list[str]]:
    parser = ArgumentParser(
        prog="python -m skactiveml_annotation",
        description="Data Annotation tool for active machine learning pipelines."
    )
    subparsers = parser.add_subparsers(dest="command")

    commands.run.register(subparsers)
    commands.embed.register(subparsers)
    commands.install_dataset.register(subparsers)
    commands.dev.register(subparsers)

    args, remaining = parser.parse_known_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    return args, remaining


def main():
    util.logging.configure_logging()
    args, remaining_args = parse_args()
    args.func(args, remaining_args)


if __name__ == "__main__":
    main()

import argparse


def register(subparsers: argparse._SubParsersAction):
    embed_parser = subparsers.add_parser("embed", help="Compute embeddings for a dataset.")
    # TODO:


import argparse

import load_torchvision_images

def _get_mapping() -> dict:
    # TODO:
    return load_torchvision_images.DATASET_CONFIGS

def register(subparsers: argparse._SubParsersAction):
    choices = _get_mapping().keys()
    install_parser = subparsers.add_parser(
        "install-dataset",
        help="Install a demo dataset to get started quickly",
        description=(
            "Downloads and installs a dataset for which a precomputed embeddings is supplied "
            "Intended for quickstart purposes"
        )
    )
    install_parser.add_argument(
        "dataset",
        choices=choices,
        metavar="DATASET",
        help=f"Dataset to install. Choices: [{', '.join(choices)}]",
    )

    # TODO: need to select right execute function bases on the dataset selected
    install_parser.set_defaults(func=load_torchvision_images.execute)

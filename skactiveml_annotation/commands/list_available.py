import sys
import logging
import argparse


def register(subparsers: argparse._SubParsersAction):
    list_parser = subparsers.add_parser(
        "list-available",
        help="List available datasets or embedding methods for a specific dataset.",
        description=(
            "Without arguments:\n"
            "   lists all available datasets and their installation status.\n"
            "With a dataset:\n"
            "   lists all embedding methods compatible with the specified dataset "
            " and whether the embedding is computed."
        ),
        epilog=(
            "Examples:\n"
            "   %(prog)s             List all available datasets\n"
            "   %(prog)s cifar10     List embedding methods for dataset 'cifar10'"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    list_parser.add_argument(
        "dataset",
        nargs="?",
        default=None,
        help="Dataset to list embedding methods for (omit to list datasets)",
    )
    list_parser.set_defaults(func=list_dispatch)

    
def list_dispatch(args: argparse.Namespace, extra: list[str]):
    if args.dataset is None:
        list_datasets(args, extra)
    else:
        list_embedding_methods(args, extra)


def list_datasets(_arg: argparse.Namespace, _extra: list[str]):
    """List all available datasets and their installation status."""
    from skactiveml_annotation.core import api

    dataset_cfgs = api.get_dataset_config_options()
    
    if not dataset_cfgs:
        print("No datasets available.")
        sys.exit(0)

    print("Available datasets:")
    max_len = max(len(cfg.id) for cfg in dataset_cfgs)
    for cfg in dataset_cfgs:
        installed = api.is_dataset_installed(cfg)
        status = "installed" if installed else "not installed"
        print(f"    {cfg.id:<{max_len}}     [{status}]")


def list_embedding_methods(args: argparse.Namespace, _extra: list[str]):
    """List embedding methods compatible with a given dataset."""
    from skactiveml_annotation.core import api

    dataset_id = args.dataset
    
    try:
        dataset_cfg = api.get_dataset_config_from_id(dataset_id)
    except FileNotFoundError:
        logging.error(f"Dataset with id '{dataset_id}' does not exist.")
        sys.exit(1)
    except Exception:
        logging.exception(f"Dataset config '{dataset_id}' failed to be parsed.")
        sys.exit(1)

    embedding_cfgs = api.get_embedding_options_for_dataset(dataset_cfg)
    if not embedding_cfgs:
        print(f"No Embedding method available to embed dataset: {dataset_id}")
        sys.exit(0)

    print(f"Available embedding methods for dataset: {dataset_id}.")
    max_len = max(len(cfg.id) for cfg in embedding_cfgs)
    for emb_cfg in embedding_cfgs:
        is_cached = api.is_dataset_embedded(dataset_id, emb_cfg.id)
        status = "computed" if is_cached else "not computed"
        print(f"    {emb_cfg.id:<{max_len}}     [{status}]")

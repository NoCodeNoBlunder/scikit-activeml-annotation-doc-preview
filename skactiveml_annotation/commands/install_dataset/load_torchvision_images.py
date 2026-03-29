from __future__ import annotations
import sys
import logging
from typing import Any, TYPE_CHECKING

import skactiveml_annotation.paths as sap

if TYPE_CHECKING:
    import argparse
    from torchvision.datasets import VisionDataset
    from skactiveml_annotation.hydra_schema import DatasetConfig


DATASET_CONFIGS = {
    'cifar100':      ("CIFAR100",      {'train': True, 'download': True}),
    'cifar10':       ("CIFAR10",       {'train': True, 'download': True}),
    'mnist':         ("MNIST",         {'train': True, 'download': True}),
    'fashion-mnist': ("FashionMNIST",  {'train': True, 'download': True}),
    'stl10':         ("STL10",         {'split': 'unlabeled', 'download': True}),
}


def _install_torchvision_images(
    dataset_cfg: DatasetConfig,
    dataset_cls: type[VisionDataset],
    kwargs: dict[str, Any],
):
    # TODO: put it in the requirements
    from tqdm import tqdm
    from concurrent.futures import ThreadPoolExecutor

    output_dir = dataset_cfg.data_path
    if not output_dir.is_absolute():
        output_dir = sap.ROOT_PATH / output_dir

    logging.info(f"Downloading Dataset {dataset_cfg.display_name} ...")

    dataset = dataset_cls(
        root=output_dir.parent / 'temp',
        **kwargs,
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    def _save_image(idx: int) -> None:
        image, _ = dataset[idx]
        image.save(output_dir / f'{dataset_cfg.id}_{idx}.png')

    logging.info("Encoding and saving images ...")

    # --- Multi thread ---
    # Save each image as a PNG file. Each entry is a tuple (image, label)
    with ThreadPoolExecutor() as executor:
        futures = executor.map(_save_image, range(len(dataset)))
        for _ in tqdm(futures, total=len(dataset)):
            pass

    logging.info(f"Saved {len(dataset)} images at '{output_dir}'")


def execute(args: argparse.Namespace, _: list[str]):
    from skactiveml_annotation.core import api

    dataset_id = args.dataset

    try:
        dataset_cfg = api.get_dataset_config_from_id(dataset_id)
    except:
        logging.error(
            f"No .yaml config file exists for dataset {dataset_id}."
            "A dataset can only be installed if a config file for it exists."
        )
        exit(1)

    if api.is_dataset_installed(dataset_cfg):
        logging.info(
            f"Dataset {dataset_id} is installed already at. Nothing to do."
        )
        sys.exit(0)

    # Optional dependency
    try:
        from torchvision import datasets
    except:
        logging.error(f"torchvision is required to download dataset: {dataset_id}")
        sys.exit(1)
        
    class_name, kwargs = DATASET_CONFIGS[dataset_id]
    dataset_cls = getattr(datasets, class_name, None)

    if dataset_cls is None:
        logging.error("Dataset class %s not found in torchvision.datasets", class_name)
        sys.exit(1)

    _install_torchvision_images(
        dataset_cfg,
        dataset_cls,
        kwargs,
    )

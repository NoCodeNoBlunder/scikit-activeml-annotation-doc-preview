import logging
from pathlib import Path
from typing import Callable, cast, override

import numpy as np
import numpy.typing as npt

from PIL import Image


try:
    import torch # pyright: ignore[reportMissingImports]
    from torch.utils.data import DataLoader # pyright: ignore[reportMissingImports]
    import torchvision.transforms as transforms # pyright: ignore[reportMissingImports]
except ImportError as e:
    logging.error(e)
    raise

from .base import (
    ProgressFunc,
    relative_to_root,
    EmbeddingBaseAdapter,
)


class ImageDataset(torch.utils.data.Dataset):
    def __init__(self, data_path: Path, transform: Callable):
        self.transform = transform
        self.image_paths =  [
            path for path in data_path.iterdir()
            if path.is_file()
        ]

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx) -> tuple[torch.Tensor, str]:
        image_path = self.image_paths[idx]

        try:
            # Open the image using Pillow
            image = Image.open(image_path).convert('RGB')
        except Exception as e:
            logging.error(f"Unexpected error loading image {image_path}: {e}")
            raise

        # Transform pil image to a tensor of shape (3, h, w), containg raw data
        image_tensor: torch.Tensor = self.transform(image)
        return image_tensor, relative_to_root(image_path)


class TorchVisionAdapter(EmbeddingBaseAdapter):
    def __init__(
            self,
            batch_size: int = 16,
            model_variant: str = "dinov2_vitb14"
        ):
        self.model_variant = model_variant
        self.batch_size = batch_size
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ])

        try:
            # Load the pretrained model from PyTorch Hub
            self.model = cast(
                torch.nn.Module,
                torch.hub.load("facebookresearch/dinov2", self.model_variant)
            )
        except Exception as e:
            raise RuntimeError("DINOv2 model is not available") from e

        # Move the model to the appropriate device (GPU or CPU)
        self.model = self.model.to(self.device)
        # Set the model to evaluation mode
        self.model.eval()

    @override
    def compute_embeddings(
        self,
        data_path: Path,
        progress_func: ProgressFunc,
    ) -> tuple[npt.NDArray, list[str]]:
        logging.info(f"Compute Torchvision embedding using device: {self.device} ...")

        dataset = ImageDataset(data_path, self.transform)
        dataloader = DataLoader(
            dataset,
            batch_size=self.batch_size,
            num_workers=4,
        )

        embeddings: npt.NDArray | None = None
        num_samples = len(dataset)
        file_paths = [""] * num_samples
        progress = 0

        with torch.inference_mode():
            for batch_tensor, batch_paths in dataloader:

                batch_tensor = batch_tensor.to(self.device)
                X = self.model(batch_tensor).cpu().numpy()

                if embeddings is None:
                    embeddings = np.empty((num_samples, X.shape[1]), dtype=X.dtype)

                next_progress = progress + X.shape[0]
                embeddings[progress: next_progress] = X
                file_paths[progress: next_progress] = batch_paths
                progress = next_progress

                progress_func(progress, num_samples)

        if embeddings is None:
            raise RuntimeError("No embeddings were computed. Dataset was empty.")

        return embeddings, file_paths

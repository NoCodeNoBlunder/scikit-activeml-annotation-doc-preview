import logging
from typing import override

from PIL import Image
from pathlib import Path

import numpy as np

from .base import (
    EmbeddingBaseAdapter,
    ProgressFunc,
    relative_to_root,
    ProgressFunc,
)


class SimpleFlattenAdapter(EmbeddingBaseAdapter):
    @override
    def compute_embeddings(
        self,
        data_path: Path,
        progress_func: ProgressFunc,
    ) -> tuple[np.ndarray, list[str]]:
        """
        Load images one by one from the directory, flatten them,
        and return the stacked feature matrix.
        """
        feature_list = []
        file_path_list = []
        # iterdir does not ensure order of files in dir.
        files = [file for file in data_path.iterdir() if file.is_file()]

        n_files = len(files)

        for progress, file in enumerate(files):
            try:
                # img = Image.open(file).convert("RGB")
                img = Image.open(file)
                if img.mode == "L":
                    # Greyscale image
                    img_data = np.array(img)  # Shape (H, W)
                else:
                    # RGB image
                    img_data = np.array(img.convert("RGB"))  # Shape (H, W, 3)

                feature = img_data.flatten().reshape(1, -1)
                feature_list.append(feature)
                file_path_list.append(relative_to_root(file))

                progress_func(progress, n_files)

            except Exception as e:
                logging.error(f"Error processing {file}: {e}")

        try:
            feature_matrix = np.concatenate(feature_list, axis=0)
        except Exception as e:
            raise RuntimeError(f"Some images are RBG while others are Greyscale: {e}")

        return feature_matrix, file_path_list

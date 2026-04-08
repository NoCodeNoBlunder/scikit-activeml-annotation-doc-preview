from pathlib import Path
from typing import Callable
from abc import (
    ABC,
    abstractmethod,
)

import numpy.typing as npt

import skactiveml_annotation.paths as sap

ProgressFunc = Callable[[int, int], None]

def relative_to_root(path: str | Path) -> str:
    """
    Convert a path to be relative to the project root.

    Parameters
    ----------
    path : str or Path
        Path to convert.

    Returns
    -------
    str
        Path relative to the project root.
    """
    if isinstance(path, str):
        path = Path(path)
    return str(path.relative_to(sap.ROOT_PATH))


class EmbeddingBaseAdapter(ABC):
    """Interface for implementing embedding methods.

    Implementors define how raw dataset samples are transformed into
    numerical embeddings for use in machine learning.
    """

    @abstractmethod
    def compute_embeddings(
        self,
        data_path: Path,
        progress_func: ProgressFunc,
    ) -> tuple[npt.NDArray, list[str]]:
        """Compute embeddings for all samples in the given dataset directory.

        Parameters
        ----------
        data_path : Path
            Absolute path to the dataset directory containing all samples.

        progress_func : Callable[[int, int], None]
            Callback function to report progress during embedding computation.

            Signature:
                progress_func(processed: int, total: int) -> None

            Where:
                processed : int
                    Number of samples that have already been processed.
                total : int
                    Total number of samples in the dataset.

        Returns
        -------
        embeddings : numpy.ndarray
            Array of computed embeddings with shape (n_samples, n_features).

        file_paths : list of str
            List of file paths corresponding to each embedding.

            Paths should be **relative to the project root** to ensure
            portability. Implementors can use :func:`relative_to_root` to
            construct these paths.

        Notes
        -----
        The ordering of ``embeddings`` and ``file_paths`` must be consistent.
        That is, for all ``i``, ``file_paths[i]`` corresponds to
        ``embeddings[i]``.
        """
        ...

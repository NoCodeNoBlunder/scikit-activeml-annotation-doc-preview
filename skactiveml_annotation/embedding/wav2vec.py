import logging
from pathlib import Path
from typing import override

try:
    import torch  # pyright: ignore[reportMissingImports]
    from torch.utils.data import DataLoader # pyright: ignore[reportMissingImports]
    from transformers import Wav2Vec2Processor, Wav2Vec2Model  # pyright: ignore[reportMissingImports]
    from transformers import TensorType
except ImportError as e:
    logging.error(e)
    raise

import numpy as np
import numpy.typing as npt

import librosa

from .base import (
    ProgressFunc,
    relative_to_root,
    EmbeddingBaseAdapter,
)


class AudioDataset(torch.utils.data.Dataset):
    def __init__(self, data_path: Path, sample_rate: int):
        self.sample_rate = sample_rate
        self.file_paths = sorted(
            path for path in data_path.iterdir()
            if path.is_file() and path.suffix.lower() == ".wav"
        )

    def __len__(self) -> int:
        return len(self.file_paths)

    def __getitem__(self, idx: int) -> tuple[np.ndarray, str]:
        path = self.file_paths[idx]
        try:
            # Resample to the sampling rate required by the model
            waveform, _ = librosa.load(path, sr=self.sample_rate, mono=True)
        except Exception as e:
            logging.error(f"Unexpected error loading audio {path}: {e}")
            raise
        return waveform, relative_to_root(path)

def _collate_audio(
    batch: list[tuple[np.ndarray, str]]
) -> tuple[list[np.ndarray], list[str]]:
    waveforms, paths = zip(*batch)
    return list(waveforms), list(paths)


class Wav2Vec2EmbeddingAdapter(EmbeddingBaseAdapter):
    def __init__(
        self,
        model_name: str = "facebook/wav2vec2-base",
        batch_size: int = 8,
    ):
        self.sample_rate = 16000 # facebook/wav2vec2 was trained on 16kHz
        self.batch_size = batch_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = Wav2Vec2Processor.from_pretrained(model_name)
        self.model = Wav2Vec2Model.from_pretrained(model_name)
        self.model.to(self.device)  # pyright: ignore[reportArgumentType]
        self.model.eval()

    @override
    def compute_embeddings(
        self,
        data_path: Path,
        progress_func: ProgressFunc,
    ) -> tuple[npt.NDArray, list[str]]:
        logging.info(f"Compute Wav2Vec2 embedding using device: {self.device} ...")

        dataset = AudioDataset(data_path, self.sample_rate)
        dataloader = DataLoader(
            dataset,
            batch_size=self.batch_size,
            num_workers=4,
            # Use custom collate func to prevent PyTorch from stacking
            # variable lenght waveforms
            collate_fn=_collate_audio,
        )

        embeddings: torch.Tensor | None = None
        num_samples = len(dataset)
        file_paths = [""] * num_samples
        progress = 0

        with torch.inference_mode():
            for batch_waveforms, batch_paths in dataloader:
                # Preprocessing
                inputs = self.processor(
                    audio=batch_waveforms,
                    common_kwargs={
                        "return_tensors": TensorType.PYTORCH,
                    },
                    audio_kwargs={
                        # Pad variable length audio so it can be batched
                        "padding": True,
                        # Make the processor return attention mask to allow
                        # to allow the model to ignore shorter samples.
                        "return_attention_mask": True,
                        "sampling_rate": self.sample_rate,
                    },
                ).to(self.device)

                # Inference
                outputs = self.model(**inputs)

                # [batch_size, time_steps, hidden_size]
                last_hidden = outputs.last_hidden_state

                # [batch_size, num_samples]
                input_mask = inputs["attention_mask"]

                # [batch_size, time_steps]
                feature_mask = self.model._get_feature_vector_attention_mask(
                    last_hidden.shape[1],
                    input_mask
                )

                # [batch_size, time_steps, 1]
                feature_mask = feature_mask.unsqueeze(-1)

                masked_hidden = last_hidden * feature_mask

                # [batch_size, hidden_size]
                #  masked mean pooling
                batch_embeddings = masked_hidden.sum(dim=1) / feature_mask.sum(dim=1).clamp(min=1)

                if embeddings is None:
                    # Preallocate memory
                    embeddings = torch.empty(
                        (num_samples, batch_embeddings.shape[1]),
                        dtype=batch_embeddings.dtype,
                    )

                next_progress = progress + batch_embeddings.shape[0]

                embeddings[progress:next_progress] = batch_embeddings
                file_paths[progress:next_progress] = list(batch_paths)

                progress = next_progress
                progress_func(progress, num_samples)

        if embeddings is None:
            raise RuntimeError("No embeddings were computed. Dataset was empty.")

        return embeddings.cpu().numpy(), file_paths

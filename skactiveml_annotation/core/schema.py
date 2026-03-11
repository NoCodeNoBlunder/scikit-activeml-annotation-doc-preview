import json
from dataclasses import dataclass

import pydantic

MISSING_LABEL_MARKER = 'MISSING_LABEL'
DISCARD_MARKER = 'DISCARDED'


@dataclass
class SessionConfig:
    batch_size: int = 10  # How many samples to label before retraining
    subsampling: int | float | None = None

    def __post_init__(self):
        # Workarround Dash initialized it to emtpy str?
        if self.subsampling == '':
            self.subsampling = None


# Dont use pydantic because it does not serialize private fields
class Batch:
    def __init__(
        self,
        emb_indices: list[int],
        classes_sklearn: list[str],
        class_probas: list[list[float]] | None = None,
        progress: int = 0
    ):
        if not (0 <= progress <= len(emb_indices)):
            raise ValueError("Initial progress out of range")

        self.emb_indices = emb_indices
        self.class_probas = class_probas
        self.classes_sklearn = classes_sklearn

        self._progress = progress
        self._min_progress = progress
        self._max_progress = progress

    @property
    def progress(self) -> int:
        return self._progress

    def advance(self, step: int):
        if not self.is_advanceable(step):
            raise ValueError(
                f"Cannot advance batch by {step} because it would result out of bounds"
            )

        self._progress += step
        self._min_progress = min(self._min_progress, self.progress)
        self._max_progress = max(self._max_progress, self.progress)

    def _is_valid_progress(self, progress: int) -> bool:
        return 0 <= progress < len(self.emb_indices)

    def get_num_annotated(self) -> int:
        return self._max_progress - self._min_progress + 1

    def is_advanceable(self, step: int) -> bool:
        next_progress = self.progress + step
        return self._is_valid_progress(next_progress)

    def is_completed(self) -> bool:
        return not self._is_valid_progress(self.progress)

    def __len__(self) -> int:
        return len(self.emb_indices)

    # -- Serialization & Deserialization --
    def to_json(self) -> str:
        data = {
            "emb_indices": self.emb_indices,
            "class_probas": self.class_probas,
            "classes_sklearn": self.classes_sklearn,
            "_progress": self._progress,
            "_min_progress": self._min_progress,
            "_max_progress": self._max_progress
        }
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> "Batch":
        data = json.loads(json_str)
        batch = cls(
            emb_indices=data["emb_indices"],
            class_probas=data.get("class_probas", None),
            classes_sklearn=data.get("classes_sklearn", None),
            progress=data["_progress"]
        )
        batch._min_progress = data["_min_progress"]
        batch._max_progress = data["_max_progress"]
        return batch


class AnnotationMetaData(pydantic.BaseModel):
    first_view_time: str = '' # Time when the sample was first presented
    total_view_duration: str = '' # Total presentation time
    last_edit_time: str = '' # Last time when a change was made
    skip_intended_cnt: int = 0 # How many time the sample has been activly skipped


class Annotation(pydantic.BaseModel):
    embedding_idx: int
    label: str
    meta_data: AnnotationMetaData


class HistoryIdx(pydantic.BaseModel):
    idx: int


class AnnotationProgress(pydantic.BaseModel):
    num_annotated: int
    num_samples: int

    def is_all_annotated(self) -> bool:
        return self.num_annotated == self.num_samples

class AutomatedAnnotation(pydantic.BaseModel):
    embedding_idx: int
    label: str
    confidence: float

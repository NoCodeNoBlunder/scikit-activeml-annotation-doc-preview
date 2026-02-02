from enum import Enum, auto
from typing import Any


# TODO instead of this use a Pydantic Model
class StoreKey(Enum):
    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[Any]):
        return name  # Automatically use the name of the member as its value

    DATASET_SELECTION = auto()
    EMBEDDING_SELECTION = auto()
    QUERY_SELECTION = auto()
    MODEL_SELECTION = auto()

    BATCH_STATE = auto()
    ANNOTATIONS_STATE = auto()
    DATA_PRESENT_TIMESTAMP = auto()

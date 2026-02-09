from collections.abc import Sequence
from enum import Enum, auto
from typing import Callable

class SortOrder(Enum):
    ASC = auto()
    DESC = auto()
    UNSORTED = auto()


def is_all_numeric(seq: Sequence[str]) -> bool:
    return all(_is_number_like(s) for s in seq)


def _is_number_like(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def get_sort_order(seq: Sequence, key: Callable | None = None) -> SortOrder:
    if len(seq) < 2:
        return SortOrder.ASC

    if key is None:
        values = seq
    else:
        values = [key(x) for x in seq]

    if all(values[i] <= values[i+1] for i in range(len(values)-1)):
        return SortOrder.ASC
    if all(values[i] >= values[i+1] for i in range(len(values)-1)):
        return SortOrder.DESC

    return SortOrder.UNSORTED

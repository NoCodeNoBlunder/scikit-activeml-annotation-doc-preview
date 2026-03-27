from __future__ import annotations
import logging
from enum import Enum
from typing import (
    Any,
    TypeVar,
)

import hydra

import pydantic
from pydantic import Field

from skactiveml.base import (
    ClassifierMixin,
    SingleAnnotatorPoolQueryStrategy,
)
from skactiveml_annotation.embedding.base import EmbeddingBaseAdapter

T = TypeVar("T")


class Modality(Enum):
    """Modality of a dataset."""
    AUDIO = "Audio"
    TEXT = "Text"
    IMAGE = "Image"


class DatasetConfig(pydantic.BaseModel):
    """Configuration for a dataset available for annotation.

    The configuration file should be placed in the ``config/dataset/``
    directory. The filename (without ``.yaml``) is used as the dataset's
    unique ``id``.

    Parameters
    ----------
    id : str
        Unique identifier, automatically derived from the config filename.
    display_name : str
        Human-readable name shown in the UI, e.g. ``"CIFAR-10"``.
    classes : list[str]
        Ordered list of class labels the annotator can assign to a sample.
    data_path : str
        Path to the directory containing the raw sample files,
        relative to the project root.
    modality : Modality
        Modality of the dataset.
    """
    id: str
    display_name: str
    classes: list[str]
    data_path: str
    modality: Modality


class EmbeddingConfig(pydantic.BaseModel):
    """Configuration for an embedding method.

    The configuration file should be placed in the ``config/embedding/``
    directory. The filename (without ``.yaml``) is used as the embedding's
    unique ``id``.

    Parameters
    ----------
    id : str
        Unique identifier, automatically derived from the config filename.
    display_name : str
        Human-readable name shown in the UI, e.g. ``"DINOv2 ViT-S/14"``.
    definition : EmbeddingTarget
        Hydra-style instantiation target and constructor arguments.
    modalities : list[Modality]
        List of modalities this embedding supports. Valid values are
        ``Image``, ``Audio``, and ``Text``.
    """
    id: str
    display_name: str
    definition: EmbeddingTarget
    modalities: list[Modality]


# TODO:
class QueryStrategyConfig(pydantic.BaseModel):
    """Configuration for a pool-based active learning query strategy.

    The configuration file should be placed in the ``config/query_strategy/``
    directory. The filename (without ``.yaml``) is used as the strategy's
    unique ``id``.

    All pool-based active learning strategies for classification provided by
    `scikit-activeml <https://scikit-activeml.github.io/latest/generated/strategy_overview.html>`_
    are supported.

    Parameters
    ----------
    id : str
        Unique identifier, automatically derived from the config filename.
    display_name : str
        Human-readable name shown in the UI, e.g. ``"Uncertainty Sampling"``.
    definition : QueryStrategyTarget
        Hydra-style instantiation target and constructor arguments.
    """
    id: str
    display_name: str
    definition: QueryStrategyTarget


# TODO:
class ModelConfig(pydantic.BaseModel):
    """Configuration for a model available for evaluation and annotation.

    The configuration file should be placed in the ``config/model/`` directory.
    The filename (without ``.yaml``) is used as the model's unique ``id``.

    Parameters
    ----------
    id : str
        Unique identifier, automatically derived from the config filename.
    display_name : str
        Human-readable name shown in the UI, e.g. ``"Logistic Regression"``.
    definition : ModelTarget
        Hydra-style instantiation target and constructor arguments.
        See :class:`~yourpackage.config.ModelTarget`.
    """
    id: str
    display_name: str
    definition: ModelTarget


class ActiveMlConfig(pydantic.BaseModel):
    random_seed: int
    model: ModelConfig
    dataset: DatasetConfig
    query_strategy: QueryStrategyConfig
    embedding: EmbeddingConfig


class QueryStrategyTarget(pydantic.BaseModel):
    target_: str = pydantic.Field(..., alias="_target_")

    class Config:
        extra: str = "allow"

    def instantiate(self, **kwargs: Any) -> SingleAnnotatorPoolQueryStrategy:
        return _instantiate(self, SingleAnnotatorPoolQueryStrategy, **kwargs)


class ModelTarget(pydantic.BaseModel):
    target_: str = Field(..., alias="_target_")

    class Config:
        extra: str = "allow"

    def instantiate(self, **kwargs: Any) -> ClassifierMixin:
        return _instantiate(self, ClassifierMixin, **kwargs)


class EmbeddingTarget(pydantic.BaseModel):
    target_: str = Field(..., alias="_target_")

    class Config:
        extra: str = "allow"

    def instantiate(self, **kwargs: Any) -> EmbeddingBaseAdapter:
        return _instantiate(self, EmbeddingBaseAdapter, **kwargs)


def _instantiate(cfg: pydantic.BaseModel, expected_type: type[T], **kwargs: Any) -> T:
    try:
        cfg_dict = cfg.model_dump(by_alias=True)
        x = hydra.utils.instantiate(cfg_dict, **kwargs)
    except Exception as e:
        logging.error(
            "\n".join([
                f"Hydra failed to instantiate instance of: {expected_type.__name__}.",
                f"Config: {cfg.model_dump(by_alias=True)}",
                f"Exception: {e}",
            ])
        )
        raise

    if not isinstance(x, expected_type):
        logging.error("\n".join([
            "Hydra instantiated unexpected type:",
            f"Expected type: {expected_type.__name__}",
            f"Actual type:   {type(x).__name__}",
        ]))
        raise TypeError(
            f"Expected instance of {expected_type.__name__}, got {type(x).__name__}"
        )
    return x

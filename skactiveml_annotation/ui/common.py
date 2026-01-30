import logging
from typing import Any, Mapping

import dash
from dash.exceptions import PreventUpdate

import pydantic

from skactiveml_annotation.core.api import compose_config
from skactiveml_annotation.core.schema import ActiveMlConfig
from skactiveml_annotation.ui.hotkeys import HotkeyConfig
from skactiveml_annotation.ui.storekey import StoreKey

def compose_from_state(store_data) -> ActiveMlConfig:
    overrides = (
        ('dataset', store_data[StoreKey.DATASET_SELECTION.value]),
        ('query_strategy', store_data[StoreKey.QUERY_SELECTION.value]),
        ('embedding', store_data[StoreKey.EMBEDDING_SELECTION.value]),
        ('+model', store_data[StoreKey.MODEL_SELECTION.value])  # add model to default list
    )

    return compose_config(overrides)


def try_deserialize_hotkey_cfg(hotkey_cfg_json) -> HotkeyConfig: 
    if hotkey_cfg_json is None:
        logging.error(
            "Hotkey Config should be initialized allready but it is None"
        )
        raise PreventUpdate

    try:
        hotkey_cfg = HotkeyConfig.model_validate(hotkey_cfg_json)
    except pydantic.ValidationError as e:
        logging.error("Unexpected deserialization error occured \n%s", e)
        raise PreventUpdate

    return hotkey_cfg


def get_trigger_id() -> str:
    """
    Returns the ID of the component that triggered the callback.

    - If the ID is a normal string ID, returns it as is.
    - If the ID is a pattern-matching dict with an "index" key, returns that index.
    - Raises RuntimeError if triggered_id is None, not a string or mapping,
      or if "index" is missing or not a string.
    """
    trigger_id: str | Mapping[str, Any] | None = dash.callback_context.triggered_id

    if trigger_id is None:
        raise RuntimeError("Callback fired without a trigger")

    # normal string ID
    if isinstance(trigger_id, str):
        return trigger_id

    # dash pattern-matching ID (dict-like)
    # Convention is that is contains an "index" key to determine which
    # component was triggered
    if isinstance(trigger_id, Mapping):
        index = trigger_id.get("index")
        if not isinstance(index, str):
            raise RuntimeError(
                f"Expected a string for 'index' in pattern-matching ID, got {type(index).__name__}: {trigger_id}"
            )
        return index

    # any other type is invalid
    raise RuntimeError(
        f"Unexpected type for triggered_id: {type(trigger_id).__name__}"
    )



from dash import (
    Input,
    Output,
    State,
    callback 
)

from dash.exceptions import PreventUpdate

import dash_mantine_components as dmc

from skactiveml_annotation.core import api
from skactiveml_annotation.ui import common

from skactiveml_annotation.core.schema import Batch
from skactiveml_annotation.ui.storekey import StoreKey 

from . import ids

def create_auto_annotate_modal():
    return dmc.Modal(
        dmc.Stack(
            [

                dmc.NumberInput(
                    id=ids.AUTO_ANNOTATE_THRESHOLD,
                    min=0,
                    max=1,
                    hideControls=True,
                    label="Threshold",
                    placeholder="Enter a threshold",
                    value=0.99,
                    allowNegative=False,
                    w='35%',
                    required=True,
                    persistence=ids.AUTO_ANNOTATE_THRESHOLD,
                    persistence_type='session',
                ),

                dmc.Center(
                    dmc.Button(
                        'Confirm',
                        id=ids.AUTO_ANNOTATE_CONFIRM_BTN,
                        color='dark',
                    )
                )
            ],
        ),
        id=ids.AUTO_ANNOTATE_MODAL,
        title='Auto Annotate with Threshold',
        centered=True,
        shadow='xl',
        withCloseButton=False,
    )


@callback(
    Input(ids.AUTO_ANNOTATE_BTN, 'n_clicks'),
    output=dict(
        modal_open=Output(ids.AUTO_ANNOTATE_MODAL, 'opened', allow_duplicate=True),
    ),
    prevent_initial_call=True
)
def open_modal(
    clicks
):
    if clicks is None:
        raise PreventUpdate

    return dict(
        modal_open=True
    )


# TODO: this should be a background callback
@callback(
    Input(ids.AUTO_ANNOTATE_CONFIRM_BTN, 'n_clicks'),
    State('session-store', 'data'),
    State(ids.AUTO_ANNOTATE_THRESHOLD, 'value'),
    output=dict(
        auto_annot_modal_open=Output(ids.AUTO_ANNOTATE_MODAL, 'opened', allow_duplicate=True),
    ),
    prevent_initial_call=True,
)
def on_auto_annotate(
    click,
    session_data,
    threshold,
):
    if click is None:
        raise PreventUpdate

    # TODO: what happens with the current batch Write back all annoted before doing it?

    activeml_cfg = common.compose_from_state(session_data)
    X = api.load_embeddings(
        activeml_cfg.dataset.id,
        activeml_cfg.embedding.id
    )

    batch_json = session_data.pop(StoreKey.BATCH_STATE.value, None)
    dataset_id = session_data[StoreKey.DATASET_SELECTION.value]
    embedding_id = session_data[StoreKey.EMBEDDING_SELECTION.value]
    batch = Batch.from_json(batch_json)

    api.auto_annotate(X, activeml_cfg, threshold)

    return dict(
        auto_annot_modal_open=False,
    )

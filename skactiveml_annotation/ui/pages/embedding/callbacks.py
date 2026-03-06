
from dash import (
    Dash,
    Input,
    Output,
    State,
    callback_context,
)
from dash.exceptions import PreventUpdate

import dash_mantine_components as dmc

from skactiveml_annotation import ui
from skactiveml_annotation.core import api
from skactiveml_annotation.core.shared_types import DashProgressFunc
from skactiveml_annotation.ui.storekey import StoreKey
from skactiveml_annotation.util import logging


def register(app: Dash):
    @app.callback(
        Input('url-embedding-init', 'pathname'),
        State('session-store', 'data'),
        output=dict(
            embedding_selection_content=Output("embedding-selection-container", 'children')
        )
    )
    def setup_page(
        _,
        session_data
    ):
        return dict(
            embedding_selection_content=_create_selected_embedding_view(session_data)
        )
    _ = setup_page


    @app.callback(
        Input("embedding-button", 'n_clicks'),
        output=dict(
            title=Output('embedding-title', 'children'),
            # cancel_disabled=Output("cancel-embedding-button", 'disabled')
        ),
        prevent_initial_call=True,
    )
    def on_embedding_start(
        _,
    ):
        return dict(
            title="Embedding in progress...",
            # cancel_disabled=False
        )
    _ = on_embedding_start


    @app.callback(
        Input('cancel-embedding-button', 'n_clicks'),
        output=dict(
            title=Output('embedding-title', 'children', allow_duplicate=True),
            progress=Output('embedding-progress', 'value'),
            # cancel_disabled=Output("cancel-embedding-button", 'disabled', allow_duplicate=True)
        ),
        prevent_initial_call=True
    )
    def on_cancel(
        _,
    ):
        return dict(
            title="Embedding",
            progress=0,
            # cancel_disabled=True
        )
    _ = on_cancel


    @app.callback(
        Input("embedding-button", 'n_clicks'),
        State("session-store", 'data'),
        progress=Output('embedding-progress', 'value'),
        cancel=Input('cancel-embedding-button', 'n_clicks'),
        running=[
            (Output('embedding-button', 'loading'), True, False),
            (Output('cancel-embedding-button', 'disabled'), False, True),
            (Output('embedding-progress', 'animated'), True, False)
        ],
        output=dict(
            title=Output('embedding-title', 'children', allow_duplicate=True),
            embedding_button_container=Output('embedding-button-container', 'children')
        ),
        background=True,
        prevent_initial_call=True,
    )
    def compute_embedding(
        progress_func: DashProgressFunc, # Progress func gets passed as first arg
        n_clicks: int | None,
        store_data
    ):
        if n_clicks is None:
            raise PreventUpdate

        # The background Callback runs in a different process.
        # Logging needs to be initialized in this new context
        logging.setup_logging_background_callback()

        logging.debug15("compute embedding background callback")

        _compute_embedding(store_data, progress_func)

        return dict(
            title="Embedding completed!",
            embedding_button_container=_create_change_page_buttons()
        )
    _ = compute_embedding


    @app.callback(
        Input('go-home-button', 'n_clicks'),
        Input('go-annotating-button', 'n_clicks'),
        State('session-store', 'data'),
        output=dict(
            pathname=Output('url-embedding', 'pathname')
        ),
        prevent_initial_call=True
    )
    def change_page(
        home_clicks,
        annot_clicks,
        session_data
    ):
        if home_clicks is None and annot_clicks is None:
            raise PreventUpdate

        trigger_id = callback_context.triggered_id

        if trigger_id == 'go-home-button':
            pathname = '/'
        else:
            # go-annotating-button
            dataset_id = session_data[StoreKey.DATASET_SELECTION.value]
            pathname = f'/annotation/{dataset_id}'

        return dict(
            pathname=pathname
        )
    _ = change_page


def _compute_embedding(store_data, progress_func):
    activeml_cfg = ui.common.compose_from_state(store_data)
    api.compute_embeddings(activeml_cfg, progress_func)


def _create_selected_embedding_view(session_data):
    dataset_id = session_data[StoreKey.DATASET_SELECTION.value]
    embedding_id = session_data[StoreKey.EMBEDDING_SELECTION.value]

    return (
        dmc.Card(
            [
                dmc.Text(f'Dataset: {dataset_id}'),
                dmc.Text(f'Embedding: {embedding_id}'),
            ],
        )
    )


def _create_change_page_buttons():
    home_button = dmc.Button('Home', id='go-home-button')
    annot_button = dmc.Button("Annotation", id='go-annotating-button')
    return [home_button, annot_button]

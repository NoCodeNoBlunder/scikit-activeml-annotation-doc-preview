from dash import (
    ClientsideFunction,
    Dash,
    Input,
    Output,
    State,
    ctx,
    set_props,
    clientside_callback,
)
import dash
from dash.exceptions import PreventUpdate

import dash_mantine_components as dmc

from dash_iconify import DashIconify

from skactiveml_annotation.core import api
from skactiveml_annotation.core.schema import DatasetConfig
from skactiveml_annotation.ui.components import sampling_input
from skactiveml_annotation.ui.storekey import StoreKey
from skactiveml_annotation.util import logging

from . import (
    ids,
)

 
def register(app: Dash):
    @app.callback(
        Input(ids.CONFIRM_BUTTON, 'n_clicks'),
        Input(ids.BACK_BUTTON, 'n_clicks'),
        Input(ids.STEPPER, 'active'),
        State(ids.RADIO_SELECTION, 'value'),
        State(ids.STEPPER, 'active'),
        State('session-store', 'data'),
        output=dict(
            selection_content=Output(ids.UI_CONTAINER, 'children', allow_duplicate=True),
            session_data=Output('session-store', 'data', allow_duplicate=True),
            step=Output(ids.STEPPER, 'active', allow_duplicate=True),
            focus=Output('focus-el-trigger', 'data', allow_duplicate=True),
        ),
        prevent_initial_call=True
    )
    def update(
        confirm_clicks: int | None,
        back_clicks: int | None,
        new_active: int | None,
        radio_value: str,
        current_step: int,
        session_data: dict,
    ):
        if confirm_clicks is None and back_clicks is None and new_active is None:
            raise PreventUpdate

        trigger_id = ctx.triggered_id

        if trigger_id == ids.CONFIRM_BUTTON:
            return _handle_confirm(radio_value, current_step, session_data)

        elif trigger_id == ids.BACK_BUTTON:
            return _handle_back(current_step, session_data)

        elif trigger_id == ids.STEPPER:
            if new_active is None:
                logging.error("new_active is None when the trigger was the STEPPER. Should not occure")
                raise PreventUpdate
            return _handle_ui_stepper_clicked(new_active, session_data)
    _ = update


    @app.callback(
        Input('url_home_init', 'pathname'),
        State('session-store', 'data'),
        output=dict(
            selection_content=Output(ids.UI_CONTAINER, 'children', allow_duplicate=True),
            session_data=Output('session-store', 'data', allow_duplicate=True),
        ),
        prevent_initial_call='initial_duplicate',
    )
    def setup_page(
        _,
        session_data,
    ):
        logging.debug15("Setup page")

        if session_data is None:
            session_data = {}

        return dict(
            selection_content=_create_step_ui(0, session_data),
            session_data=session_data
        )
    _ = setup_page


    @app.callback(
        Input(ids.NEXT_PAGE_TRIGGER, 'data'),
        State('session-store', 'data'),
        output=dict(
            pathname=Output('url_home', 'pathname')
        ),
        prevent_initial_call=True
    )
    def go_to_next_page(
        _,
        session_data,
    ):
        dataset_id = session_data[StoreKey.DATASET_SELECTION.value]
        embedding_id = session_data[StoreKey.EMBEDDING_SELECTION.value]

        if api.is_dataset_embedded(dataset_id, embedding_id):
            logging.debug15("Home to annotation \n -------------------------- \n")
            pathname = f'/annotation/{dataset_id}'
        else:
            logging.debug15("Home to embedding \n -------------------------- \n")
            pathname = f'/embedding'

        return dict(pathname=pathname)
    _ = go_to_next_page


    clientside_callback(
        ClientsideFunction(namespace='clientside', function_name='validateConfirmButton'),
        Output(ids.CONFIRM_BUTTON, "disabled"),
        Input("radio-selection", "value"),
    )


def _handle_confirm(
    radio_value: str,
    current_step: int,
    session_data: dict,
):
    # logging.debug15(f"handle_confirm triggered at step {current_step} with radio_value: {radio_value}")
    # if current_step >= 4 or radio_value is None or n_clicks is None:
    #     raise PreventUpdate

    if current_step >= 4: # TODO: Hardcoded
        set_props(ids.NEXT_PAGE_TRIGGER, dict(data=True))
        return dict(
            selection_content=dash.no_update,
            session_data=dash.no_update,
            step=dash.no_update,
            focus=dash.no_update,
        )

    elif current_step == 0:
        prev_dataset_id = session_data.get(StoreKey.DATASET_SELECTION.value)
        was_dataset_changed = prev_dataset_id is not None and radio_value != prev_dataset_id
        if was_dataset_changed:
            session_data.pop(StoreKey.BATCH_STATE.value, None)

        session_data[StoreKey.DATASET_SELECTION.value] = radio_value

    elif current_step == 1:
        session_data[StoreKey.EMBEDDING_SELECTION.value] = radio_value

    elif current_step == 2:
        session_data[StoreKey.QUERY_SELECTION.value] = radio_value

    elif current_step == 3:
        session_data[StoreKey.MODEL_SELECTION.value] = radio_value

    new_step = current_step + 1
    return dict(
        selection_content=_create_step_ui(new_step, session_data),
        session_data=session_data,
        step=new_step,
        focus=ids.UI_CONTAINER,
    )


def _handle_back(
    current_step: int,
    session_data: dict,
):
    if current_step == 0:
        raise PreventUpdate

    next_step = current_step - 1

    return dict(
        selection_content=_create_step_ui(next_step, session_data),
        session_data=dash.no_update,
        step=next_step,
        focus=ids.UI_CONTAINER,
    )


def _handle_ui_stepper_clicked(
    new_active: int,
    session_data: dict,
):
    return dict(
        selection_content=_create_step_ui(new_active, session_data),
        session_data=dash.no_update,
        step=dash.no_update,
        focus=ids.UI_CONTAINER,
    )


# Helper function to build UI for different steps
def _create_step_ui(step: int, session_data):
    if step == 0:
        if session_data is None:
            preselect = None
        else:
            preselect = session_data.get(StoreKey.DATASET_SELECTION.value)
        content = _create_dataset_selection(preselect)
    elif step == 1:
        content = _create_embedding_radio_group(session_data)
    elif step == 2:
        content = _create_radio_group(api.get_qs_config_options(), session_data.get(StoreKey.QUERY_SELECTION.value))
    elif step == 3:
        content = _create_radio_group(api.get_model_config_options(), session_data.get(StoreKey.MODEL_SELECTION.value))
    elif step == 4:
        content = dmc.Stack(
            [
                *sampling_input.create_sampling_inputs(),
                # Dummy element to ensure this id exists in the layout at the last step
                dmc.RadioGroup([], id=ids.RADIO_SELECTION, display='none', readOnly=True)
            ],
            align="flex-start"
        )
    elif step == 5:
        return None
    else:
        raise RuntimeError("Step is not in {0,...,4}")

    return dmc.ScrollArea(
        content,
        offsetScrollbars='y',
        type='auto',
        scrollbars='y',
        styles=dict(
            viewport={
                'maxHeight': '90%'
            },
        )
    )


def _create_dataset_radio_item(cfg: DatasetConfig, cfg_display: str):
    dataset_exists = api.dataset_path_exits(cfg.data_path)

    radio_item = (
        dmc.Radio(
            label=cfg_display,
            value=cfg.id,
            disabled=not dataset_exists,
            size='md',
        )
    )

    if dataset_exists:
        return radio_item

    return dmc.Tooltip(
        radio_item,
        label=f'Dataset does not exist at path: {cfg.data_path}',
        openDelay=250,
    )


def _create_dataset_selection(preselect):
    dataset_options = api.get_dataset_config_options()
    data = [(cfg, f'{cfg.display_name} - ({cfg.data_type.instantiate().value})')
            for cfg in dataset_options]

    # TODO: Make it so the first none disabled element is preselected by default
    if preselect is None:
        # Preselect the first element
        preselect = data[1][0].id

    return (
        dmc.RadioGroup(
            id=ids.RADIO_SELECTION,
            children=dmc.Stack(
                [
                    _create_dataset_radio_item(cfg, cfg_display)
                    for cfg, cfg_display in data
                ]
            ),
            value=preselect,
            size="md",
            wrapperProps={"autoFocus": True},
            p="xs",
            # style={'border': '2px solid red'}
        )
    )


def _create_embedding_radio_group(session_data):
    # TODO only display embeddings that are valid for the selected dataset
    options = api.get_embedding_config_options()
    formatted_options = [(cfg.id, cfg.display_name) for cfg in options]

    preselect = session_data.get(StoreKey.EMBEDDING_SELECTION.value)

    return dmc.RadioGroup(
        id=ids.RADIO_SELECTION,
        children=dmc.Stack(
            [
                dmc.Group(
                    [
                        dmc.Radio(label=cfg_name, value=cfg_id, size='md'),
                        _create_bool_icon(api.is_dataset_embedded(
                            session_data[StoreKey.DATASET_SELECTION.value],
                            cfg_id
                        ))
                    ]
                )
                for cfg_id, cfg_name in formatted_options
            ]
        ),
        value=preselect,
        size="md",
        p="xs",
        # style={'border': '2px solid red'},
    )


def _create_bool_icon(val: bool):
    if val:
        icon = 'tabler:check'
        color = 'green'
        label = 'embedding is cached'
    else:
        icon = 'tabler:x'
        color = 'red'
        label = 'embedding has to be computed'

    return (
        dmc.Tooltip(
            dmc.ThemeIcon(
                DashIconify(icon=icon),
                variant='light',
                radius=20,
                color=color,
                size=25,
            ),
            label=label
        )
    )


# Helper function to create a radio group
def _create_radio_group(options, preselect):
    formatted_options = [(cfg.id, cfg.display_name) for cfg in options]
    return dmc.RadioGroup(
        id=ids.RADIO_SELECTION,
        children=dmc.Stack([dmc.Radio(label=l, value=k, size='md') for k, l in formatted_options]),
        value=preselect,
        size="md",
        p="xs",
        # style={'border': '2px solid red'},
    )

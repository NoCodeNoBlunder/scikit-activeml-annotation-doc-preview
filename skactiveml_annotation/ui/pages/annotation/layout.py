from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, cast

from dash_extensions import Keyboard
import pydantic
import isodate

import dash
from dash import (
    dcc,
    register_page,
    callback,
    Input,
    Output,
    State,
    clientside_callback,
    ClientsideFunction,
    set_props,
)
from dash.exceptions import PreventUpdate

from dash_iconify import DashIconify
import dash_mantine_components as dmc
import dash_loading_spinners as dls

from skactiveml_annotation.core.data_display_model import DataDisplaySetting
from skactiveml_annotation.ui import (
    common,
    hotkeys,
)
from skactiveml_annotation.core import api
from skactiveml_annotation.util import logging

from skactiveml_annotation.core.schema import (
    Batch,
    Annotation,
    AnnotationMetaData,
    SessionConfig,
    DISCARD_MARKER,
    MISSING_LABEL_MARKER,
)
from skactiveml_annotation.ui.storekey import StoreKey, AnnotProgress

from . import (
    ids,
    actions,
    components,
    auto_annotate_modal,
    label_setting_modal,
    data_presentation_settings,
)
from .label_setting_modal import SortBySetting

ANNOTATIONS_ADAPTER = (
    pydantic.TypeAdapter(list[Annotation | None])
)

register_page(
    __name__,
    path_template='/annotation/<dataset_name>',
    description='The main annotation page',
)

def layout(**kwargs):
    _ = kwargs
    return(
        dmc.Box(
            [
                dcc.Location(id='url-annotation', refresh=True),
                dcc.Location(id=ids.ANNOTATION_INIT, refresh=False),
                # Triggers
                dcc.Store(id=ids.UI_TRIGGER),
                dcc.Store(id=ids.QUERY_TRIGGER),
                dcc.Store(id=ids.START_TIME_TRIGGER),
                # Data
                dcc.Store(id=ids.DATA_DISPLAY_CFG_DATA, storage_type='session'),
                # TODO use a pydantic Model for this. Its not even clear what this is exactly
                # Why is there an extra Store for this? Just update UI properties?
                dcc.Store(id=ids.ANNOT_PROGRESS, storage_type='session'),
                dcc.Store(id=ids.ADDED_CLASS_NAME, storage_type='session'),

                Keyboard(id="keyboard"),

                label_setting_modal.create_label_settings_modal(),
                auto_annotate_modal.create_auto_annotate_modal(),

                # TODO: Try to use allowOptional instead
                dmc.Box(id='label-radio'),  # avoid id error

                dmc.AppShell(
                    [
                        dmc.AppShellNavbar(
                            id="sidebar-container-annotation",
                            children=components.create_sidebar(),
                            p="md",
                            # style={'border': '4px solid red'}
                        ),
                        dmc.Flex(
                            [
                                dmc.Box(
                                    [
                                        dmc.LoadingOverlay(
                                            id=ids.COMPUTING_OVERLAY,
                                            zIndex=10,
                                            loaderProps={
                                                'children': dmc.Stack(
                                                    [
                                                        dmc.Group(
                                                            [
                                                                dmc.Title("Computing next batch", order=2),
                                                                # Show 3 dots duruing query
                                                                dmc.Loader(
                                                                    size='xl',
                                                                    type='dots',
                                                                    # Type annotation incorrect valid css is supported
                                                                    color='var(--mantine-color-dark-7)',  # pyright: ignore[reportArgumentType]
                                                                ),
                                                            ],
                                                            justify='center',
                                                            wrap='wrap',
                                                            mb='5vh'  # pyright: ignore[reportArgumentType]
                                                        ),
                                                    ],
                                                    align='center',
                                                    # style=dict(border='red dashed 3px')
                                                )
                                            },
                                            overlayProps={
                                                'radius':'lg',
                                                'center': True,
                                                'blur': 7,
                                            },
                                            transitionProps={
                                                'transition':'fade',
                                                'duration': 150,
                                                'mounted': True,
                                                # 'exitDuration': 500,
                                            },
                                        ),

                                        dmc.Center(
                                            dcc.Loading(
                                                dmc.Box(
                                                    id=ids.DATA_DISPLAY_CONTAINER,
                                                    # TODO why did I fix the width and heigh here?
                                                    mih=15,
                                                    # w='250px',
                                                    # h='250px',
                                                    my=10,
                                                    # style=dict(border='4px dotted red')
                                                ),
                                                delay_hide=150,
                                                delay_show=150,
                                                custom_spinner=dls.ThreeDots(radius=7)
                                            ),
                                        ),

                                        dmc.Group(
                                            [
                                                dmc.Tooltip(
                                                    dmc.ActionIcon(
                                                        DashIconify(icon='tabler:plus',width=20),
                                                        variant='filled',
                                                        id=ids.ADD_CLASS_BTN,
                                                        color="dark"
                                                    ),
                                                    label="Add a new class by using current Search Input."
                                                ),

                                                dmc.Tooltip(
                                                    dmc.ActionIcon(
                                                        DashIconify(icon="clarity:settings-line", width=20),
                                                        variant="filled",
                                                        id=ids.LABEL_SETTING_BTN,
                                                        color='dark',
                                                    ),
                                                    label='Label settings',
                                                ),

                                                components.create_confirm_buttons(),

                                                dmc.TextInput(
                                                    placeholder='Select Label',
                                                    id=ids.LABEL_SEARCH_INPUT,
                                                    radius='sm',
                                                    w='150px',
                                                    # inputProps={
                                                    #     "autoFocus": True
                                                    # }
                                                ),
                                            ],
                                            mt=15,
                                            justify='center'
                                        ),
                                    ],
                                    p=10,
                                    pos="relative",
                                ),

                                dmc.Stack(
                                    id=ids.LABELS_CONTAINER,
                                    # h='400px'
                                    align='center'
                                ),
                                # create_confirm_buttons(),
                                components.create_progress_bar()
                            ],


                            style={
                                # 'border': '5px dotted blue',
                                'height': '100%',
                                'widht': '100%',
                            },
                            justify='center',
                            align='center',
                            direction='column',
                            wrap='nowrap',
                            gap=10,
                            py=0,
                            px=150,
                        ),

                        dmc.AppShellAside(
                            children=[
                                dmc.Stack(
                                    [
                                        dmc.Card(
                                            dmc.Stack(
                                                [
                                                    dmc.Center(
                                                        dmc.Title("Stats", order=3)
                                                    ),

                                                    dmc.Tooltip(
                                                        dmc.Group(
                                                            [
                                                                dmc.Text("Annotated:", style={"fontSize": "1vw"}),
                                                                dmc.Text(
                                                                    dmc.NumberFormatter(
                                                                        id=ids.ANNOT_PROGRESS_TEXT,
                                                                        thousandSeparator=' ',
                                                                    ),
                                                                    style={"fontSize": "1vw"}
                                                                ),
                                                            ],
                                                            gap=4
                                                        ),
                                                        label="Number of samples annotated."
                                                    ),

                                                    dmc.Tooltip(
                                                        dmc.Group(
                                                            [
                                                                dmc.Text("Total:", style={"fontSize": "1vw"}),
                                                                dmc.Text(
                                                                    dmc.NumberFormatter(
                                                                        id=ids.NUM_SAMPLES_TEXT,
                                                                        thousandSeparator=' '
                                                                    ),
                                                                    style={"fontSize": "1vw"}
                                                                )
                                                            ],
                                                            gap=4
                                                        ),
                                                        label='Total number of samples in dataset'
                                                    )

                                                ],
                                                gap=5
                                            )
                                        )
                                    ],
                                    # p='xs',
                                    # style={'border': '3px dashed green'},
                                    align='center'
                                )
                            ],
                            p="xs",
                            # style={'border': '4px solid red'}
                        ),
                    ],
                    navbar={  # pyright: ignore[reportArgumentType]
                        "width": '13vw',
                        "breakpoint": "sm",
                        "collapsed": {"mobile": True},
                    },
                    aside={  # pyright: ignore[reportArgumentType]
                        "width": '13vw',
                        "breakpoint": "sm",
                        "collapsed": {"mobile": True},
                    },
                    padding=0,
                    id="appshell",
                ),
            ],
            style={
                # 'height': '100%',
                # 'border': 'green dotted 5px'
            }
        )
    )


# Get initial browser config like dpr.
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='getDpr'),
    Output('browser-data', 'data'),
    Input(ids.ANNOTATION_INIT, 'pathname')
)


@callback(
    Input(ids.ANNOTATION_INIT, 'pathname'),
    State('session-store', 'data'),
    output=dict(
        ui_trigger=Output(ids.UI_TRIGGER, 'data', allow_duplicate=True),
        query_trigger=Output(ids.QUERY_TRIGGER, 'data', allow_duplicate=True),
        annot_progress=Output(ids.ANNOT_PROGRESS, 'data'),
        data_presentation_setting_children=Output(ids.DATA_PRESENTATION_SETTINGS_CONTAINER, "children"),
    ),
    prevent_initial_call='initial_duplicate'
)
def init(
    _,
    store_data,
):
    batch_json = store_data.get(StoreKey.BATCH_STATE.value)
    must_query = (
        batch_json is None or
        Batch.from_json(batch_json).is_completed()
    )
    
    if must_query:
        ui_trigger = dash.no_update
        query_trigger = True
    else:
        ui_trigger = True
        query_trigger = dash.no_update

    activeml_cfg = common.compose_from_state(store_data)
    data_type = activeml_cfg.dataset.data_type.instantiate()

    return dict(
        ui_trigger=ui_trigger,
        query_trigger=query_trigger,
        annot_progress=init_annot_progress(store_data),
        data_presentation_setting_children=data_presentation_settings.create_data_presentation_settings(data_type),
        # data_presentation_apply_children=data_presentation_settings.create_apply_button(data_type)
    )

def init_annot_progress(store_data):
    dataset_id = store_data.get(StoreKey.DATASET_SELECTION.value)
    embedding_id = store_data.get(StoreKey.EMBEDDING_SELECTION.value)

    return {
        AnnotProgress.PROGRESS.value: api.get_num_annotated(dataset_id),
        AnnotProgress.TOTAL_NUM.value: api.get_total_num_samples(dataset_id, embedding_id)
    }


def _get_annotation_context(store_data: dict, batch: Batch):
    start_time = datetime.fromisoformat(
        store_data[StoreKey.DATA_PRESENT_TIMESTAMP.value]
    )

    idx = batch.progress

    annotations_list = ANNOTATIONS_ADAPTER.validate_python(
        store_data[StoreKey.ANNOTATIONS_STATE.value]
    )

    annotation = annotations_list[idx]
    return idx, start_time, annotation, annotations_list


def _init_or_update_annot_metadata(
    old_annotation: Annotation | None, 
    start_time: datetime,
    end_time: datetime,
    updated_label: str | None = None,
) -> AnnotationMetaData:
    delta_time = end_time - start_time

    if old_annotation is None:
        # New Annotation
        first_view_time = start_time.isoformat()
        total_view_duration = isodate.duration_isoformat(delta_time)
        skip_intended_cnt = 0
        last_edit_time=end_time.isoformat()
    else:
        # Sample was annotated before. Update the metadata
        old_delta_time = isodate.parse_duration(old_annotation.meta_data.total_view_duration)
        first_view_time = old_annotation.meta_data.first_view_time
        total_view_duration = isodate.duration_isoformat(delta_time + old_delta_time)
        skip_intended_cnt = old_annotation.meta_data.skip_intended_cnt

        prev_label = old_annotation.label
        if prev_label != updated_label:
            last_edit_time = end_time.isoformat()
        else:
            last_edit_time = old_annotation.meta_data.last_edit_time

    return AnnotationMetaData(
        first_view_time=first_view_time,
        total_view_duration=total_view_duration,
        last_edit_time=last_edit_time,
        skip_intended_cnt=skip_intended_cnt,
    )


@callback(
    Input(actions.CONFIRM.btn_id, 'n_clicks'),
    Input(actions.DISCARD.btn_id, 'n_clicks'),
    Input(actions.SKIP.btn_id, 'n_clicks'),
    State('session-store', 'data'),
    State('label-radio', 'value', allow_optional=True), # avoid initial id error
    State(ids.ANNOT_PROGRESS, 'data'),
    output=dict(
        store_data=Output('session-store', 'data', allow_duplicate=True),
        annot_data=Output(ids.ANNOT_PROGRESS, 'data', allow_duplicate=True),
        search_text=Output(ids.LABEL_SEARCH_INPUT, 'value', allow_duplicate=True),
        focus_trigger=Output("focus-el-trigger", "data", allow_duplicate=True),
    ),
    prevent_initial_call=True
)
def on_confirm(
    confirm_click,  # TODO use patter matching instead.
    discard_click,
    skip_click,
    store_data,
    value: str,
    annot_data,
):
    end_time = datetime.now(timezone.utc)

    if all(x is None for x in (confirm_click, discard_click, skip_click)):
        raise PreventUpdate

    try:
        trigger_id = common.get_trigger_id()
    except RuntimeError as e:
        logging.error(e)
        raise PreventUpdate

    label = (
        MISSING_LABEL_MARKER if trigger_id == 'skip' else
        value if trigger_id == 'confirm' else
        DISCARD_MARKER
    )

    batch = Batch.from_json(store_data[StoreKey.BATCH_STATE.value])
    idx, start_time, annotation, annotations_list = _get_annotation_context(store_data, batch)
    annot_metadata = _init_or_update_annot_metadata(annotation, start_time, end_time)

    if trigger_id == "skip":
        annot_metadata.skip_intended_cnt += 1

    annotation = Annotation(
        embedding_idx=batch.emb_indices[idx],
        label=label,
        meta_data=annot_metadata,
    )
    annotations_list[idx] = annotation

    jsonable = ANNOTATIONS_ADAPTER.dump_python(
        annotations_list,
        mode="json"
    )
    store_data[StoreKey.ANNOTATIONS_STATE.value] = jsonable

    batch.advance(step=1)

    # Override existing batch
    # TODO serialize here?
    store_data[StoreKey.BATCH_STATE.value] = batch.to_json()

    if batch.is_completed():
        logging.info("Batch is completed")

        dataset_id = store_data[StoreKey.DATASET_SELECTION.value]
        embedding_id = store_data[StoreKey.EMBEDDING_SELECTION.value]

        # All samples in the batch should be annotated by now
        annotations = cast(list[Annotation], annotations_list)
        api.update_json_annotations(dataset_id, embedding_id, annotations, batch)

        # TODO: Could improve performance by adding how many have been added (not skipped in this batch)
        num_annotated = api.get_num_annotated_not_skipped(dataset_id)

        if num_annotated == annot_data[AnnotProgress.TOTAL_NUM.value]:
            logging.info("All Samples Annotated!")
            raise PreventUpdate

        annot_data[AnnotProgress.PROGRESS.value] = num_annotated

        set_props(ids.QUERY_TRIGGER, dict(data=True))
    else:
        set_props(ids.UI_TRIGGER, dict(data=True))

    return dict(
        store_data=store_data,
        annot_data=annot_data,
        search_text='',
        focus_trigger=ids.LABEL_SEARCH_INPUT,
    )


# TODO there should be a seperate store for the BATCH
@callback(
    Input(ids.UI_TRIGGER, 'data'),
    State('session-store', 'data'),
    State(ids.DATA_DISPLAY_CFG_DATA, 'data'),
    State('browser-data', 'data'),
    State(ids.ADDED_CLASS_NAME, 'data'),
    State(ids.LABEL_SETTING_SHOW_PROBAS, 'checked'),
    State(ids.LABEL_SETTING_SORTBY, 'value'),
    State(ids.ALL_ANNOTATION_BTNS, 'id'),
    output=dict(
        label_container=Output(ids.LABELS_CONTAINER, 'children'),
        show_container=Output(ids.DATA_DISPLAY_CONTAINER, 'children'),
        batch_progress=Output('batch-progress-bar', 'value'),
        data_display_data=Output(ids.DATA_DISPLAY_CFG_DATA, 'data'),
        is_computing_overlay=Output(ids.COMPUTING_OVERLAY, 'visible', allow_duplicate=True),
        data_width=Output(ids.DATA_DISPLAY_CONTAINER, 'w'),
        data_height=Output(ids.DATA_DISPLAY_CONTAINER, 'h'),
        annot_start_time_trigger=Output(ids.START_TIME_TRIGGER, 'data'),
        disable_all_action_buttons=Output(ids.ALL_ANNOTATION_BTNS, 'loading', allow_duplicate=True),
        focus_trigger=Output("focus-el-trigger", "data"),
        added_class_name=Output(ids.ADDED_CLASS_NAME, 'data'),
    ),
    prevent_initial_call=True,
)
def on_ui_update(
    # Triggers
    ui_trigger,
    # Data
    store_data,
    data_display_setting_json,
    browser_dpr,
    # Adding classes
    added_class_name: str | None,
    # Label settings
    show_probas: bool,  # TODO this is confusing
    sort_by: str,
    annot_button_ids: list,
):
    if ui_trigger is None and browser_dpr is None:
        raise PreventUpdate

    activeml_cfg = common.compose_from_state(store_data)
    data_type = activeml_cfg.dataset.data_type.instantiate()

    batch = Batch.from_json(store_data[StoreKey.BATCH_STATE.value])

    annotations_list = ANNOTATIONS_ADAPTER.validate_python(
        store_data[StoreKey.ANNOTATIONS_STATE.value]
    )
    
    idx = batch.progress
    embedding_idx = batch.emb_indices[idx]
    annotation = annotations_list[idx]

    human_data_path = Path(
        api.get_one_file_path(
            activeml_cfg.dataset.id,
            activeml_cfg.embedding.id,
            embedding_idx
        )
    )

    if data_display_setting_json is None:
        logging.debug15("Data Display Setting is not yet initialized. Initializing now.")
        data_display_setting = DataDisplaySetting()
    else:
        try:
            data_display_setting = DataDisplaySetting.model_validate(data_display_setting_json)
        except pydantic.ValidationError as e:
            logging.error(f"Data Presentation settings are expected to be valid here but are invalid: {e}")
            raise PreventUpdate

    rendered_data, w, h = components.create_data_display(data_display_setting, data_type, human_data_path, browser_dpr)

    sort_by = SortBySetting[sort_by] 

    # TODO how to organize this better?
    return dict(
        label_container=components.create_label_chips(
            activeml_cfg.dataset.classes, annotation, batch, show_probas, sort_by, added_class_name
        ),
        show_container=rendered_data,
        batch_progress=(idx / len(batch.emb_indices)) * 100,
        data_display_data=data_display_setting.model_dump(),
        is_computing_overlay=False,
        data_width=w,
        data_height=h,
        annot_start_time_trigger=True,
        was_class_added=False,
        disable_all_action_buttons=[False] * len(annot_button_ids),
        focus_trigger=ids.LABEL_SEARCH_INPUT,
        added_class_name=None,
    )


# On Query start. Show loading overlay.
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='triggerTrue'),
    Output(ids.COMPUTING_OVERLAY, 'visible'),
    Input(ids.QUERY_TRIGGER, 'data')
)


@callback(
    Input(ids.QUERY_TRIGGER, 'data'),
    State('session-store', 'data'),
    State('batch-size-input', 'value'),
    State('subsampling-input', 'value'),
    output=dict(
        store_data=Output('session-store', 'data', allow_duplicate=True),
        ui_trigger=Output(ids.UI_TRIGGER, 'data', allow_duplicate=True),
    ),
    prevent_initial_call=True,
    # background=True, # INFO LRU Cache won't work with this
)
def on_next_batch(
    trigger,
    store_data,
    batch_size,
    subsampling,
):
    # Assume that global index as at last position of batch
    if trigger is None:
        raise PreventUpdate

    logging.debug15("\n On next batch")

    # INFO: Assumes global idx is on the last of the completed batch
    # to determine correct number of restorable samples
    session_cfg = SessionConfig(batch_size, subsampling)
    activeml_cfg = common.compose_from_state(store_data)

    dataset_id = store_data[StoreKey.DATASET_SELECTION.value]

    global_history_idx = api.get_global_history_idx(dataset_id)

    history_size = api.get_num_annotated(dataset_id)

    if global_history_idx is None:
        if history_size == 0:
            global_history_idx = 0
        else:
            # Assume there have been annotations made but the index is missing
            global_history_idx = history_size - 1

        logging.debug15("Initializing global history idx to", global_history_idx)
        api.set_global_history_idx(dataset_id, global_history_idx)

    # TODO:
    num_restorable = max(0, history_size - (global_history_idx + 1))

    if num_restorable >= batch_size:
        logging.debug15("No Active ML needed")
        # No Active ML needed just restore Batch size many samples
        batch, annotations_list = api.restore_batch(activeml_cfg, global_history_idx, True, batch_size)

        # This assumes the idx is on the last of the previous batch
        api.increment_global_history_idx(dataset_id, 1)

    else:
        logging.debug15("Must use active ml")
        # Active learning needed. But first restore what is left to restore
        if num_restorable > 0:
            logging.debug15(f"Can still restore {num_restorable} samples before Active ML")
            batch_one, annotations_list_one = api.restore_batch(activeml_cfg, global_history_idx, True, num_restorable)

            emb_indices_one = batch_one.emb_indices
            class_probas_one = batch_one.class_probas
            annotations_one = annotations_list_one
            api.increment_global_history_idx(dataset_id, 1)
        else:
            emb_indices_one = []
            class_probas_one = []
            annotations_one = []

            new_history_idx = api.get_num_annotated(dataset_id)
            api.set_global_history_idx(dataset_id, new_history_idx)
        
        # Only the difference has to be quried
        session_cfg.batch_size = batch_size - num_restorable
        logging.debug15(f"Do active learning to get {session_cfg.batch_size} samples")

        X = api.load_embeddings(activeml_cfg.dataset.id, activeml_cfg.embedding.id)

        # Remove samples from pool that have been restored. To avoid possible duplication
        batch_two, annotations_list_two = api.request_query(activeml_cfg, session_cfg, X, emb_indices_one)

        logging.debug15("queried batch emb indices:")
        logging.debug15(batch_two.emb_indices)

        # TODO: Determine how many samples have been previously skipped
        # To align global idx correctly

        class_probas_combined = (
            class_probas_one + batch_two.class_probas
            if class_probas_one is not None and batch_two.class_probas is not None
            else None
        )

        # Combine Batches and annotations_list
        batch = Batch(
            emb_indices=emb_indices_one + batch_two.emb_indices,
            classes_sklearn=batch_two.classes_sklearn,
            class_probas=class_probas_combined,
            progress=0
        )

        annotations_list = annotations_one + annotations_list_two

    store_data[StoreKey.BATCH_STATE.value] = batch.to_json()

    jsonable = ANNOTATIONS_ADAPTER.dump_python(
        annotations_list,
        mode="json"
    )

    # store_data[StoreKey.ANNOTATIONS_STATE.value] = annotations_list.model_dump()
    store_data[StoreKey.ANNOTATIONS_STATE.value] = jsonable

    return dict(
        store_data=store_data,
        ui_trigger=True,
    )


@callback(
    Input('skip-batch-button', 'n_clicks'),
    State('session-store', 'data'),
    State(ids.ANNOT_PROGRESS, 'data'),
    output=dict(
        query_trigger=Output(ids.QUERY_TRIGGER, 'data'),
        session_data=Output('session-store', 'data', allow_duplicate=True),
        annot_progress=Output(ids.ANNOT_PROGRESS, 'data', allow_duplicate=True),
        search_text=Output(ids.LABEL_SEARCH_INPUT, 'value', allow_duplicate=True),
        focus_trigger=Output("focus-el-trigger", "data", allow_duplicate=True),
    ),
    prevent_initial_call=True
)
def on_skip_batch(
    n_clicks: int,
    session_data: dict,
    annot_progress,
):
    if n_clicks is None or n_clicks == 0:
        raise PreventUpdate

    # reset batch state
    batch_json = session_data.pop(StoreKey.BATCH_STATE.value, None)
    dataset_id = session_data[StoreKey.DATASET_SELECTION.value]
    embedding_id = session_data[StoreKey.EMBEDDING_SELECTION.value]
    batch = Batch.from_json(batch_json)

    logging.debug15(session_data[StoreKey.ANNOTATIONS_STATE.value])

    annotations_list = ANNOTATIONS_ADAPTER.validate_python(
        session_data[StoreKey.ANNOTATIONS_STATE.value]
    )

    api.save_partial_annotations(batch, dataset_id, embedding_id, annotations_list)
    annot_progress[AnnotProgress.PROGRESS.value] = api.get_num_annotated_not_skipped(dataset_id)

    return dict(
        query_trigger=True,
        session_data=session_data,
        annot_progress=annot_progress,
        search_text='',
        focus_trigger=ids.LABEL_SEARCH_INPUT,
    )


@callback(
    Input(actions.BACK.btn_id, 'n_clicks'),
    State('session-store', 'data'),
    State('batch-size-input', 'value'),
    State(ids.ANNOT_PROGRESS, 'data'),
    output=dict(
        session_data=Output('session-store', 'data'),
        ui_trigger=Output(ids.UI_TRIGGER, 'data', allow_duplicate=True),
        annot_progress=Output(ids.ANNOT_PROGRESS, 'data', allow_duplicate=True),
        search_text=Output(ids.LABEL_SEARCH_INPUT, 'value', allow_duplicate=True),
        focus_trigger=Output("focus-el-trigger", "data", allow_duplicate=True),
    ),
    prevent_initial_call=True
)
def on_back(
    clicks: None | int,
    store_data,
    batch_size, # TODO input these are UI inputs
    annot_progress,
):
    end_time = datetime.now(timezone.utc)

    if clicks is None:
        raise PreventUpdate

    logging.debug15("\non back click callback")
    # TODO only store last edit when there was a change?

    batch = Batch.from_json(store_data[StoreKey.BATCH_STATE.value])
    idx, start_time, annotation, annotations_list = _get_annotation_context(store_data, batch)
    annot_metadata = _init_or_update_annot_metadata(annotation, start_time, end_time)

    old_label = (
        MISSING_LABEL_MARKER if annotation is None else 
        annotation.label
    )

    annotation = Annotation(
        embedding_idx=batch.emb_indices[idx],
        label=old_label,
        meta_data=annot_metadata,
    )

    annotations_list[idx] = annotation

    jsonable = ANNOTATIONS_ADAPTER.dump_python(
        annotations_list,
        mode="json"
    )
    store_data[StoreKey.ANNOTATIONS_STATE.value] = jsonable


    # TODO: Make a helper for this?
    if batch.progress == 0:
        logging.debug15("Have to get last batch to be able to go back.")
        # TODO Serialize new Annotations made in current batch
        dataset_id = store_data.get(StoreKey.DATASET_SELECTION.value)
        embedding_id = store_data.get(StoreKey.EMBEDDING_SELECTION.value)
        file_paths = api.get_file_paths(dataset_id, embedding_id, batch.emb_indices)
        _ = api.update_annotations(dataset_id, file_paths, annotations_list)

        # TODO this step should be done in the serialize and deserialize methods
        activeml_cfg = common.compose_from_state(store_data)
        history_idx = api.get_global_history_idx(activeml_cfg.dataset.id)
        assert history_idx is not None

        try:
            batch, annotations_list = api.restore_batch(activeml_cfg, history_idx, False, batch_size)
        except RuntimeError:
            logging.warning("Raise PreventUpdate. Cannot go back further. No Annotations left")
            # Have to do ui_trigger so the buttons are enabled
            return dict(
                ui_trigger=True,
                session_data=dash.no_update,
                annot_progress=dash.no_update,
                search_text=dash.no_update,
                focus_trigger=dash.no_update,
            )

        # Update the global history idx
        api.increment_global_history_idx(dataset_id, -len(batch))
        logging.debug15(f"info decrementing global idx to: {api.get_global_history_idx(dataset_id)}")
        # Annotations can decrease if the annotation of a sample was change to SKIP
        annot_progress[AnnotProgress.PROGRESS.value] = api.get_num_annotated_not_skipped(dataset_id)
    else:
         batch.advance(step= -1)

    store_data[StoreKey.BATCH_STATE.value] = batch.to_json()
    return dict(
        ui_trigger=True,
        session_data=store_data,
        annot_progress=annot_progress,
        search_text='',
        focus_trigger=ids.LABEL_SEARCH_INPUT,
    )


@callback(
    Input(ids.UI_TRIGGER, 'data'),
    State(ids.ANNOT_PROGRESS, 'data'),
    output=dict(
        annot_progress=Output(ids.ANNOT_PROGRESS_TEXT, 'value'),
        num_samples=Output(ids.NUM_SAMPLES_TEXT, 'value'),
    ),
    prevent_initial_call=True
)
def on_annot_progress(
    trigger,
    annot_data,
):
    if trigger is None:
        raise PreventUpdate

    return dict(
        annot_progress=annot_data.get(AnnotProgress.PROGRESS.value),
        num_samples=annot_data.get(AnnotProgress.TOTAL_NUM.value)
    )


# Disable buttons to prevent spamming before processing is done.
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='disableAllButtons'),
    Output(ids.ALL_ANNOTATION_BTNS, 'loading'),
    Input(ids.ALL_ANNOTATION_BTNS, 'n_clicks'),
    prevent_initial_call=True
)

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='scrollToChip'),
    Output("label-radio", 'value'),
    Input(ids.LABEL_SEARCH_INPUT, "value"),
    prevent_initial_call=True,
)


@callback(
    Input(ids.START_TIME_TRIGGER, 'data'),
    State('session-store', 'data'),
    output=dict(
        session_data=Output("session-store", 'data', allow_duplicate=True)
    ),
    prevent_initial_call=True
)
def on_annot_start_timestamp(
    trigger,
    session_data
):
    if trigger is None:
        raise PreventUpdate

    # TODO: this will be utc aware time of the server and not user
    now_str = datetime.now(timezone.utc).isoformat()

    session_data[StoreKey.DATA_PRESENT_TIMESTAMP.value] = now_str

    return dict(
        session_data=session_data
    )


@callback(
    Input(ids.ADD_CLASS_BTN, 'n_clicks'),
    State('session-store', 'data'),
    State(ids.LABEL_SEARCH_INPUT, 'value'),
    output=dict(
        ui_trigger=Output(ids.UI_TRIGGER, 'data', allow_duplicate=True),
        search_value=Output(ids.LABEL_SEARCH_INPUT, 'value', allow_duplicate=True),
        added_class_name=Output(ids.ADDED_CLASS_NAME, 'data', allow_duplicate=True),
        label_value=Output('label-radio', 'value', allow_duplicate=True),
        store_data=Output('session-store', 'data', allow_duplicate=True),
    ),
    prevent_initial_call=True
)
def on_add_new_class(
    click: int | None,
    store_data: dict,
    new_class_name: str | None,
):
    if click is None:
        raise PreventUpdate

    if new_class_name is None:
        logging.warning("Failed to add class because no class name is provided")
        raise PreventUpdate

    activeml_cfg = common.compose_from_state(store_data)
    batch = Batch.from_json(store_data[StoreKey.BATCH_STATE.value])

    try:
        api.add_class(
            dataset_cfg=activeml_cfg.dataset,
            new_class_name=new_class_name,
            batch=batch,
        )
    except ValueError as e:
        logging.warning(f"Failed to add class: {e}")
        raise PreventUpdate

    store_data[StoreKey.BATCH_STATE.value] = batch.to_json()

    return dict(
        ui_trigger=True,
        search_value='',
        added_class_name=new_class_name,
        label_value=new_class_name,
        store_data=store_data,
    )

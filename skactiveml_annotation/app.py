import dash
from dash import (
    Dash,
    Input,
    Output,
    State,
    html,
    dcc,
    callback,
    DiskcacheManager
)
import diskcache
from dash.exceptions import PreventUpdate

import dash_mantine_components as dmc
import dash_loading_spinners


from skactiveml_annotation.shared_ids import STORE_DATA
from skactiveml_annotation.ui import clientside_callbacks
from skactiveml_annotation.ui.components import navbar
import skactiveml_annotation.paths as sap
from skactiveml_annotation.ui import hotkeys
from skactiveml_annotation.ui.pages import (
    annotation,
    home,
    embedding,
    hotkeys_cfg,
)

cache = diskcache.Cache(sap.BACKGROUND_CALLBACK_CACHE_PATH)
background_callback_manager = DiskcacheManager(cache)


def create_app() -> Dash:
    app = Dash(
        __package__,
        use_pages=True,  # Use dash page feature
        pages_folder=str(sap.PAGES_PATH),
        external_stylesheets=[dmc.theme.DEFAULT_THEME] + dmc.styles.ALL,
        # Allows to register callbacks on components that will be created by other callbacks,
        # and are therefore not in the initial layout.
        suppress_callback_exceptions=True,
        prevent_initial_callbacks=True,
        assets_folder=str(sap.ASSETS_PATH),
        title="scikit-activeml-annotation",
        background_callback_manager=background_callback_manager,
        update_title=''
    )

    app.layout = layout
    
    clientside_callbacks.register()
    register_pages(app)

    return app


def register_pages(app):
    home.layout.register(app)
    annotation.layout.register(app)
    embedding.layout.register(app)
    hotkeys_cfg.layout.register(app)

    hotkeys.register_callbacks(app)


def layout(**kwargs):
    _ = kwargs
    return (
        dmc.MantineProvider(
            dmc.AppShell(
                [
                    # Data stored across all pages
                    dcc.Store('browser-data'),
                    dcc.Store(STORE_DATA, storage_type='session'),
                    dcc.Store('selected-ids', storage_type='session'),

                    # Triggers
                    dcc.Store("click-btn-trigger"),
                    dcc.Store("focus-el-trigger"),
                    dcc.Store("go-last-page-trigger"),

                    # Hotkeys per Page
                    dcc.Store("keymapping-cfg", storage_type="local"),

                    navbar.create_navbar(),
                    dmc.AppShellMain(
                        [
                            html.Div(
                                dash_loading_spinners.Pacman(
                                    fullscreen=True,
                                ),
                                id='app_spinner_container'
                            ),

                            dmc.Container(
                                dash.page_container,
                                id='page_content_container',
                                fluid=True,
                                style={'padding': 0}
                            )
                        ],
                        style={
                            # 'border': '5px dashed red',
                            # 'height': '80%'
                        },
                    )
                ],
                header={'height': 50},
            )
        )
    )


@callback(
    Output("app_spinner_container", 'children'),
    Input("page_content_container", 'loading_state'),
    State("app_spinner_container", 'children'),
)
def hide_page_loading_spinner(
    _,
    children,
):
    if children:
        return None
    raise PreventUpdate

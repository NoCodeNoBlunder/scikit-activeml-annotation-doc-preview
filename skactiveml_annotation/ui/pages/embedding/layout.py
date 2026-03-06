
from dash import (
    Dash,
    register_page,
    dcc,
)

import dash_mantine_components as dmc

from . import (
    callbacks,
)

def register(app: Dash):
    register_page(
        __name__,
        path_template='/embedding',
        layout=_layout,
        description='Embedding Page',
    )
    callbacks.register(app)


def _layout(**kwargs):
    _ = kwargs
    return (
        dmc.AppShellMain(
            [
                dcc.Location('url-embedding', refresh=True),
                dcc.Location('url-embedding-init', refresh=False),
                dmc.Stack(
                    [
                        dmc.Title("Embedding", id='embedding-title'),

                        dmc.Container(
                            id="embedding-selection-container"
                        ),

                        dmc.Group(
                            [
                                dmc.Button("Cancel", id='cancel-embedding-button', disabled=True),
                                dmc.Button("Start Embedding", id='embedding-button')
                            ],
                            id='embedding-button-container'
                        ),

                        dmc.Progress(
                            id="embedding-progress",
                            value=0,
                            size="xl",
                            animated=True,
                            style={
                                'width': '75%',
                                'height': '30px'
                            },
                            transitionDuration=500
                        ),
                    ],
                    align='center'
                ),
            ]
        )
    )

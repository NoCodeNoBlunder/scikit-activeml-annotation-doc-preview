
from dash import (
    Dash,
    dcc,
    register_page,
)

from dash_extensions import Keyboard

import dash_mantine_components as dmc

from . import (
    actions,
    callbacks,
)


def register(app: Dash):
    register_page(
        __name__, path='/hotkeys', layout=_layout,
    )

    actions.register(app)
    callbacks.register(app)



def _layout(**kwargs: object):
    _ = kwargs

    return (
        dmc.Center(
            [
                dcc.Location(id='url-hotkeys', refresh=True),
                dcc.Location(id='url-hotkeys-init', refresh=False),

                dcc.Store(id="hotkey-ui-trigger"),

                Keyboard(
                    id="hotkeys-keyboard",
                ),

                dmc.Stack(
                    [
                        dmc.ScrollArea(
                            dmc.Container(
                                id="hotkey-configuration-container",
                                py="xs",
                            ),
                            type='auto',
                            offsetScrollbars='y',
                            styles=dict(
                                viewport={
                                    'maxHeight': '85vh',
                                    # 'border': '5px dashed red',
                                },
                            ),
                            py='xs',
                        ),
                        dmc.Flex(
                            [
                                dmc.Button("Reset", id="reset-hotkeys-btn", color="dark"),
                                dmc.Button("Confirm", id="confirm-hotkeys-btn", color="dark"),
                                dmc.Button("Back", id="back-hotkeys-btn", color="dark"),
                            ],
                            gap="md",
                        )
                    ],
                    gap="xl",
                )
            ],
            style={
                # "height": "100vh",
                # "border": "2px dashed green",
            }
        )
    )

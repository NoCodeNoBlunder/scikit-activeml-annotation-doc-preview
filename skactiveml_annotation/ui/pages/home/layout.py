import html
from dash import (
    Dash,
    dcc,
    html,
    register_page,
)
from dash_extensions import Keyboard

import dash_mantine_components as dmc

from . import (
    ids,
    actions,
    callbacks,
)


def register(app: Dash):
    register_page(__name__, path='/', layout=_layout)
    actions.register(app)
    callbacks.register(app)



def _layout(**kwargs: object):
    _ = kwargs
    return (
        dmc.Center(
            [
                dcc.Location(id='url_home', refresh=True),
                dcc.Location(id='url_home_init', refresh=False),

                dcc.Store(id=ids.NEXT_PAGE_TRIGGER),

                Keyboard(
                    id="home-keyboard",
                ),

                dmc.Stack(
                    [
                        dmc.Stack(
                            [
                                dmc.Title(
                                    "Welcome to scikit-activeml-annotation",
                                    order=1,
                                    style={
                                        "textAlign": 'center',
                                    }
                                ),
                                dmc.Title(
                                    "Configure your annotation pipeline",
                                    order=2,
                                    style={
                                        "textAlign": 'center',
                                    }
                                )
                            ],
                            align='center',
                            p='xl'
                        ),

                        dmc.Flex(
                            [
                                dmc.Box(
                                    # Spacer
                                    w="calc(50% - 275px)",
                                ),
                                dmc.Box(
                                    create_stepper(),
                                    style={
                                        # 'border': '2px dotted blue',
                                        'whiteSpace': 'normal',
                                        'wordBreak': 'normal',
                                        'overflowWrap': 'normal',
                                    },
                                    w="275px",
                                    mr="md",
                                ),

                                dcc.Loading(
                                    dmc.Box(
                                        # Current selection injected here
                                        html.Div(id=ids.RADIO_SELECTION),  # workaround so id exists at the start
                                        id=ids.UI_CONTAINER,
                                        tabIndex=0, # Make Container focusable
                                        style={
                                            # 'border': '2px dotted blue',
                                            'whiteSpace': 'normal',
                                            'wordBreak': 'normal',
                                            'overflowWrap': 'normal',
                                            'outline': 'none',
                                        }
                                    ),
                                    type='circle',
                                    delay_hide=150,
                                    delay_show=250,
                                ),

                            ],
                            w="100%",
                            h="60vh",
                            # gap="xl",
                        ),

                        dmc.Group(
                            [
                                dmc.Button(
                                    actions.BACK_ACTION.btn_text,
                                    id=actions.BACK_ACTION.btn_id,
                                    color='dark',
                                ),
                                dmc.Button(
                                    actions.CONFIRM_ACTION.btn_text,
                                    id=actions.CONFIRM_ACTION.btn_id,
                                    color='dark',
                                    disabled=True,
                                )
                            ]
                        )
                    ],
                    align='center',
                    w="100%",
                    style={
                        # 'border': '2px solid gold',
                    }
                )
            ],
            mt=1,
            style={'height': '100%'}
        )
    )


def create_stepper():
    return (
        dmc.Stepper(
            [
                dmc.StepperStep(id={'type': 'stepper-step', 'index': 0}, label="Dataset", description="Select a Dataset"),
                dmc.StepperStep(id={'type': 'stepper-step', 'index': 1}, label="Embedding", description="Select embedding method"),
                dmc.StepperStep(id={'type': 'stepper-step', 'index': 2}, label="Query Strategy", description="Select a Query Strategy"),
                dmc.StepperStep(id={'type': 'stepper-step', 'index': 3}, label="Model", description="Select a model"),
                dmc.StepperStep(id={'type': 'stepper-step', 'index': 4}, label="Sampling", description="Set Sampling parameters"),
            ],
            id=ids.STEPPER,
            active=0,
            orientation='vertical',
            iconSize=40,
            size='xl',
            # style={'border': '2px solid red'},
            mt='xs',
            # w="50%",
            allowNextStepsSelect=False
        )
    )

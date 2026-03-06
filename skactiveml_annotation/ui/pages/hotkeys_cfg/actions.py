
from dash import (
    Dash,
    Input,
    State,
)

from skactiveml_annotation.ui import common
from skactiveml_annotation.ui.hotkeys import (
    ButtonAction,
    on_key_pressed_handler,
    register_action,
    register_default_keybinds,
)


RESET_ACTION = ButtonAction(
    "Hotkeys.Main.Reset",
    "reset-hotkeys-btn",
    "Reset",
)

CONFIRM_ACTION = ButtonAction(
    "Hotkeys.Main.Confirm",
    "confirm-hotkeys-btn",
    "Confirm",
)

BACK_ACTION = ButtonAction(
    "Hotkeys.Main.Back",
    "back-hotkeys-btn",
    "Back",
)

ALL_ACTIONS = [
    RESET_ACTION,
    CONFIRM_ACTION,
    BACK_ACTION,
]


def register(app: Dash):
    for action in ALL_ACTIONS:
        register_action(action)

    register_default_keybinds(
        "Hotkeys",
        {
            "Main": {
                "Enter": CONFIRM_ACTION.action_id,
                "Backspace+Alt+Control": BACK_ACTION.action_id,
                "R+Alt+Control": RESET_ACTION.action_id,
            },
        }
    )

    @app.callback(
        Input("hotkeys-keyboard", "n_keydowns"),
        State("hotkeys-keyboard", "keydown"),
        State("keymapping-cfg", "data"),
        prevent_initial_call=True
    )
    def on_key_pressed(
        trigger,
        key_event,
        hotkey_cfg_json,
    ):
        hotkey_cfg = common.try_deserialize_hotkey_cfg(hotkey_cfg_json)
        on_key_pressed_handler(trigger, key_event, hotkey_cfg, 'Hotkeys')
    _ = on_key_pressed


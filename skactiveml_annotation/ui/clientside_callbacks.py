from dash import (
    ClientsideFunction,
    Input,
    clientside_callback,
)


def register():
    # Trigger to simulate a button click
    clientside_callback(
        ClientsideFunction(namespace='clientside', function_name='clickButtonWithId'),
        Input("click-btn-trigger", "data"),
    )

    # Trigger to focus an element with an id
    clientside_callback(
        ClientsideFunction(namespace='clientside', function_name='focusElementWithId'),
        Input("focus-el-trigger", "data"),
    )

    # Trigger to go back to the last page
    clientside_callback(
        ClientsideFunction(namespace='clientside', function_name='goToLastPage'),
        Input("go-last-page-trigger", "data"),
    )

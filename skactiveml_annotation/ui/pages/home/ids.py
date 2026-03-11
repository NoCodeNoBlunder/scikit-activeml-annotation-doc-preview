CONFIRM_BUTTON = 'confirm_button'
BACK_BUTTON = 'back_button'
RADIO_SELECTION = 'radio-selection'
NEXT_PAGE_TRIGGER = 'next-page-trigger'
STEPPER = 'stepper'
UI_CONTAINER = 'ui-container'

# TODO:
def make_ids(module_name: str, sep: str = "-"):
    """
    Returns an ID factory prefixed by the module's package path.

    module_name: pass __name__ from the calling ids.py
    sep: separator character (default "-")
    """
    page_name = module_name.split(".")[-2]


    def make(component_id: str) -> str:
        return f"{page_name}{sep}{component_id}"

    return make


ids = make_ids(__name__)

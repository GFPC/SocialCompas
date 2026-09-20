class State:
    """Represents a discrete FSM state."""

    def __init__(self, name: str = ""):
        self.name = name

    def __set_name__(self, owner, name):
        if not self.name:
            self.name = f"{owner.__name__}:{name}"

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<State '{self.name}'>"


class StatesGroup:
    """Group of FSM states."""
    pass


class SocialCompasSG(StatesGroup):
    """FSM States matching Miro Flowchart."""
    SELECT_CITY = State("SocialCompasSG:SELECT_CITY")
    SELECT_CATEGORY = State("SocialCompasSG:SELECT_CATEGORY")
    MAIN_MENU = State("SocialCompasSG:MAIN_MENU")
    PLACES_LIST = State("SocialCompasSG:PLACES_LIST")
    PLACE_DETAIL = State("SocialCompasSG:PLACE_DETAIL")
    FAVORITES = State("SocialCompasSG:FAVORITES")
    SETTINGS = State("SocialCompasSG:SETTINGS")

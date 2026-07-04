from .base import Defense


class SampleAppendTextDefense(Defense):
    name = "sample_append_text"
    stage = "output"

    def __init__(self, appended: str = "Appended Text") -> None:
        self.appended = appended

    def apply(self, text: str) -> str:
        return f"{text}\n\n{self.appended}"
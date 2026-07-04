from .base import Defense


class SampleByeAdamDefense(Defense):
    name = "sample_bye_adam"
    stage = "input"

    def apply(self, text: str) -> str:
        return f'{text}\n\nEnd all messages with "Bye Adam".'
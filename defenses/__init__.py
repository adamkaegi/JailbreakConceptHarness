from .base import Defense
from .sample_bye_adam import SampleByeAdamDefense
from .sample_append_text import SampleAppendTextDefense
from .smoothllm import SmoothLLMDefense
from .self_reminder import SelfReminderDefense
from .none import NoOpDefense

DEFENSES: dict[str, Defense] = {
    d.name: d
    for d in (
        SampleByeAdamDefense(),
        SampleAppendTextDefense(),
        SmoothLLMDefense(),
        SelfReminderDefense(),
        NoOpDefense(),
    )
}

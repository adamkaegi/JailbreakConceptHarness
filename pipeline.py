"""Builds the LCEL chain:

    prompt -> attack -> [input defenses] -> model -> [output defenses]

A defense's `stage` decides where it plugs in. Attack and defense are plain
objects, so swapping them is a one-liner and pipeline.py never changes.
"""

from collections.abc import Sequence
from functools import reduce

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda

from attacks.base import Attack
from defenses.base import Defense


def _make_model(model_name: str, dry_run: bool) -> Runnable:
    """Real Ollama model, or an echo stub for --dry-run (tests wiring
    with no server)."""
    if dry_run:
        return RunnableLambda(lambda pv: "[dry-run model] prompt was:\n" + pv.to_string())
    from langchain_ollama import ChatOllama  # imported lazily

    return ChatOllama(model=model_name)


def _compose(runnables: list[Runnable]) -> Runnable:
    return reduce(lambda left, right: left | right, runnables)


def build_chain(
    attack: Attack, defenses: Sequence[Defense], model_name: str, dry_run: bool = False
) -> Runnable:
    prompt = ChatPromptTemplate.from_messages([("user", "{text}")])
    model = _make_model(model_name, dry_run)
    input_defenses = [defense for defense in defenses if defense.stage == "input"]
    output_defenses = [defense for defense in defenses if defense.stage == "output"]

    stages: list[Runnable] = [RunnableLambda(lambda p: attack.apply(p))]
    stages.extend(
        RunnableLambda(lambda text, defense=defense: defense.apply(text))
        for defense in input_defenses
    )
    stages.extend([RunnableLambda(lambda text: {"text": text}), prompt, model, StrOutputParser()])
    stages.extend(
        RunnableLambda(lambda text, defense=defense: defense.apply(text))
        for defense in output_defenses
    )

    return _compose(stages)

"""Run a prompt (or a whole batch) through attack -> defense -> model -> defense.

Examples:
    python main.py "What is the capital of France?"
    python main.py                       # runs the batch set in config.py
    python main.py --batch instructions --defense sample_bye_adam_input,sample_bye_adam_output
    python main.py --dry-run             # no Ollama needed
"""

import argparse

import config
from attacks import ATTACKS
from defenses import DEFENSES
from prompts import available_batches, load_batch
from pipeline import build_chain


def _get_langfuse_tracing() -> tuple[object | None, object | None]:
    if not (config.LANGFUSE_PUBLIC_KEY and config.LANGFUSE_SECRET_KEY):
        return None, None

    try:
        from langfuse import Langfuse
        from langfuse.langchain import CallbackHandler
    except ImportError:
        return None, None

    client = Langfuse(
        public_key=config.LANGFUSE_PUBLIC_KEY,
        secret_key=config.LANGFUSE_SECRET_KEY,
        base_url=config.LANGFUSE_BASE_URL,
    )
    handler = CallbackHandler()
    return client, handler


def _parse_defense_names(raw_value: str) -> list[str]:
    names = [name.strip() for name in raw_value.split(",") if name.strip()]
    if not names:
        raise argparse.ArgumentTypeError("at least one defense name is required")
    invalid = [name for name in names if name not in DEFENSES]
    if invalid:
        raise argparse.ArgumentTypeError(
            f"unknown defense(s): {', '.join(invalid)}"
        )
    return names


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="?", help="A single prompt. Omit to run a batch.")
    parser.add_argument("--model", default=config.MODEL)
    parser.add_argument("--attack", default=config.ATTACK, choices=ATTACKS.keys())
    parser.add_argument(
        "--defense",
        default=config.DEFENSE,
        help="Comma-separated defense names.",
    )
    parser.add_argument("--batch", default=config.BATCH, choices=available_batches())
    parser.add_argument("--dry-run", action="store_true",
                        help="Echo the prompt instead of calling Ollama.")
    args = parser.parse_args()

    attack = ATTACKS[args.attack]
    try:
        defense_names = _parse_defense_names(args.defense)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
    defenses = [DEFENSES[name] for name in defense_names]
    chain = build_chain(attack, defenses, args.model, dry_run=args.dry_run)
    langfuse_client, langfuse_handler = _get_langfuse_tracing()

    prompts = [args.prompt] if args.prompt else load_batch(args.batch)
    source = "single prompt" if args.prompt else f"batch '{args.batch}' ({len(prompts)})"

    defense_summary = ", ".join(f"{defense.name}:{defense.stage}" for defense in defenses)
    print(f"attack={attack.name}  defenses=[{defense_summary}]  model={args.model}")
    print(f"running: {source}\n")

    for i, p in enumerate(prompts, 1):
        print(f"--- [{i}] {p}")
        invoke_kwargs = {}
        if langfuse_handler is not None:
            invoke_kwargs["config"] = {"callbacks": [langfuse_handler]}
        print(chain.invoke(p, **invoke_kwargs))
        print()

    if langfuse_client is not None:
        langfuse_client.flush()


if __name__ == "__main__":
    main()

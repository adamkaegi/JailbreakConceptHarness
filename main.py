"""Run a prompt (or a whole batch) through attack -> defense -> model -> defense.

Examples:
    python main.py "What is the capital of France?"
    python main.py                       # runs the batch set in config.py
    python main.py --batch instructions --defense sample_bye_adam_input,sample_bye_adam_output
    python main.py --dry-run             # no Ollama needed
"""

import argparse
import csv
from datetime import datetime
from pathlib import Path

import config
from attacks import ATTACKS
from defenses import DEFENSES
from judges import JUDGES
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


def _parse_judge_name(raw_value: str) -> str:
    name = raw_value.strip()
    if not name:
        raise argparse.ArgumentTypeError("a judge name is required")
    if name not in JUDGES:
        raise argparse.ArgumentTypeError(f"unknown judge: {name}")
    return name


def _write_run_csv(
    run_rows: list[dict[str, str]],
    attack_name: str,
    defense_names: list[str],
    judge_name: str,
    model_name: str,
    batch_name: str | None,
) -> Path:
    outputs_dir = Path(__file__).resolve().parent / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    batch_suffix = batch_name or "single"
    csv_path = outputs_dir / f"run-{batch_suffix}-{timestamp}.csv"

    fieldnames = ["attack", "defenses", "judge", "model", "input", "output", "judge_label"]
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in run_rows:
            writer.writerow(
                {
                    "attack": attack_name,
                    "defenses": ",".join(defense_names),
                    "judge": judge_name,
                    "model": model_name,
                    "input": row["input"],
                    "output": row["output"],
                    "judge_label": row["judge_label"],
                }
            )

    return csv_path


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
    parser.add_argument("--judge", default=config.JUDGE)
    parser.add_argument("--batch", default=config.BATCH, choices=available_batches())
    parser.add_argument("--dry-run", action="store_true",
                        help="Echo the prompt instead of calling Ollama.")
    args = parser.parse_args()

    attack = ATTACKS[args.attack]
    try:
        defense_names = _parse_defense_names(args.defense)
        judge_name = _parse_judge_name(args.judge)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
    defenses = [DEFENSES[name] for name in defense_names]
    judge = JUDGES[judge_name]
    chain = build_chain(attack, defenses, args.model, dry_run=args.dry_run)
    langfuse_client, langfuse_handler = _get_langfuse_tracing()

    prompts = [args.prompt] if args.prompt else load_batch(args.batch)
    source = "single prompt" if args.prompt else f"batch '{args.batch}' ({len(prompts)})"

    defense_summary = ", ".join(f"{defense.name}:{defense.stage}" for defense in defenses)
    print(
        f"attack={attack.name}  defenses=[{defense_summary}]  judge={judge.name}  model={args.model}"
    )
    print(f"running: {source}\n")

    run_rows: list[dict[str, str]] = []

    for i, p in enumerate(prompts, 1):
        print(f"--- [{i}] {p}")
        invoke_kwargs = {}
        if langfuse_handler is not None:
            invoke_kwargs["config"] = {"callbacks": [langfuse_handler]}
        output_text = chain.invoke(p, **invoke_kwargs)
        judge_label = judge.apply(output_text)
        run_rows.append(
            {
                "input": p,
                "output": output_text,
                "judge_label": judge_label,
            }
        )
        print(output_text)
        print(f"judge={judge_label}")
        print()

    csv_path = _write_run_csv(
        run_rows,
        attack.name,
        defense_names,
        judge.name,
        args.model,
        args.batch if not args.prompt else None,
    )
    print(f"saved csv: {csv_path}")

    if langfuse_client is not None:
        langfuse_client.flush()


if __name__ == "__main__":
    main()

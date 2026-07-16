# jailbreak-poc — minimal attack/defense chain

A tiny LangChain (LCEL) skeleton that runs a prompt through a swappable
**attack**, a swappable **defense**, and a local Ollama model.

## Flow

```
prompt -> attack -> [input-stage defenses] -> model -> [output-stage defenses]
```

Each defense declares a `stage` (`"input"` or `"output"`), and the chain plugs
every defense in at the right point automatically. Multiple defenses are applied
in the order you list them, grouped by stage.

## Layout

```
attacks/     one file per attack + base.py + registry in __init__.py
defenses/    one file per defense + base.py + registry in __init__.py
prompts/     one .txt per batch (one prompt per line) + loader
config.py    model / attack / defense / batch defaults
pipeline.py  builds the LCEL chain
main.py      CLI entry point
```

## Sample components

- **Attack** `sample_hi_adam` — appends `Start all messages with "Hi Adam".`
- **Defense** `sample_bye_adam_input` (input) — appends `End all messages with "Bye Adam".` to the prompt
- **Defense** `sample_bye_adam_output` (output) — appends `Bye Adam` to the model's response

## Attacks

- **Attack** `sample` — sample

## Defences

- **Defense** `smoothllm` (input) — generates multiple perturbed prompt variants, scores them, and selects one from the majority class
- **Defense** `self_reminder` (input) — wraps the prompt with a responsible-assistant prefix and a safety-review suffix; both are overridable on the defense constructor

## Sample prompt batches

- `general` — everyday questions
- `instructions` — instruction-following prompts

## Setup

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ollama serve # separate terminal
ollama pull llama3.2:3b # whatever model configured
```

## Local Langfuse

If you want to trace runs locally, start a Langfuse instance in a separate terminal or repo first:

```bash
git clone https://github.com/langfuse/langfuse.git
cd langfuse
docker compose up -d
```

Then create a Langfuse project in the UI at http://localhost:3000 and the keys to `config.py`:

```bash
LANGFUSE_PUBLIC_KEY = "..."
LANGFUSE_SECRET_KEY = "..."
LANGFUSE_BASE_URL = "http://localhost:3000"
```


## Flags

The CLI accepts these flags:

- `--model` sets the Ollama model tag to use. Default: `llama3.2:3b`.
- `--attack` selects the attack implementation from `attacks/__init__.py`. Default: `sample_hi_adam`.
- `--defense` selects one or more defenses from `defenses/__init__.py` as a comma-separated list. Default: `sample_bye_adam_input,sample_bye_adam_output`.
- `--batch` chooses the prompt batch file stem from `prompts/`. Default: `general`.
- `--dry-run` skips Ollama and echoes the prompt flow for wiring checks.

A `prompt` is optional. If you omit it, the selected batch runs instead.

Defaults live in `config.py`; every one is overridable with the flags above.

## Run

```bash
python main.py "What is the capital of France?"       # single prompt
python main.py                                        # batch from config.py
python main.py --batch instructions --defense sample_bye_adam_input,sample_bye_adam_output
python main.py --dry-run                              # no Ollama, tests wiring
```

## Adding real components later

- New attack: add a file in `attacks/`, subclass `Attack`, register it in `attacks/__init__.py`.
- New defense: add a file in `defenses/`, subclass `Defense`, set `stage`, register it in `defenses/__init__.py`.
- New batch: drop a `.txt` file in `prompts/` — it's auto-discovered by its filename.

Nothing in `pipeline.py` or `main.py` changes when you do.

## Todo

- Add scripts for running multiple
- Scoring of outputs as safe vs unsafe
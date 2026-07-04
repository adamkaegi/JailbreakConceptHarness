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
- **Defense** `sample_bye_adam` (input) — appends `End all messages with "Bye Adam".` to the prompt
- **Defense** `sample_append_text` (output) — appends `Appended Text` to the model's response

## Sample prompt batches

- `general` — everyday questions
- `instructions` — instruction-following prompts

## Setup

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ollama serve            # separate terminal
ollama pull llama3.2:3b
```

## Run

```bash
python main.py "What is the capital of France?"       # single prompt
python main.py                                        # batch from config.py
python main.py --batch instructions --defense sample_bye_adam,sample_append_text
python main.py --dry-run                              # no Ollama, tests wiring
```

Defaults live in `config.py`; every one is overridable with the flags above.

For multiple defenses, pass a comma-separated list. Input defenses run before
the model; output defenses run after it.

## Adding real components later

- New attack: add a file in `attacks/`, subclass `Attack`, register it in `attacks/__init__.py`.
- New defense: add a file in `defenses/`, subclass `Defense`, set `stage`, register it in `defenses/__init__.py`.
- New batch: drop a `.txt` file in `prompts/` — it's auto-discovered by its filename.

Nothing in `pipeline.py` or `main.py` changes when you do.
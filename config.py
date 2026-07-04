"""Central config. Override any of these with CLI flags in main.py."""

MODEL = "llama3.2:3b"   # any pulled Ollama model tag

ATTACK = "sample_hi_adam"      # attacks:  sample_hi_adam | none
DEFENSE = "sample_bye_adam,sample_append_text"  # comma-separated defenses
BATCH = "general"       # prompt batch = a .txt file stem in prompts/

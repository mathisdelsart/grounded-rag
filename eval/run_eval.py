"""System evaluation: faithfulness and relevance.

Runs offline / in CI, not on every user request. Reads eval/dataset.jsonl
(reference questions with expected chunks and answers) and measures retrieval
precision and whether the answer is supported by the retrieved chunks.
"""

# TODO: implement run_eval() and wire it into CI

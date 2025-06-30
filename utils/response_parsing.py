import json
from core.exceptions import InvalidJsonFormatError

def post_process_weights(raw_weights: dict[str, float]) -> dict[str, int]:
    """
    Normalize weights so they sum to exactly 100, using rounding with remainder distribution.
    Ensures non-negative values and handles small rounding errors.
    """
    if not isinstance(raw_weights, dict):
        print(raw_weights) # handle this error
        raise ValueError("Expected a dictionary of weights.")

    # Step 0: Safely cast all values to float
    casted = {k: float(v) for k, v in raw_weights.items()}

    # Step 1: Early return if already normalized
    if round(sum(casted.values())) == 100:
        return {k: int(v) for k, v in casted.items()}

    # Step 2: Clip negatives to 0
    clipped = {k: max(0.0, v) for k, v in casted.items()}
    total = sum(clipped.values()) or 1.0

    # Step 3: Scale to 100
    scaled = {k: v / total * 100 for k, v in clipped.items()}

    # Step 4: Floor values
    floored = {k: int(v) for k, v in scaled.items()}

    # Step 5: Distribute remaining points
    remainders = {k: scaled[k] - floored[k] for k in scaled}
    shortfall = 100 - sum(floored.values())
    for k in sorted(remainders, key=remainders.get, reverse=True)[:shortfall]:
        floored[k] += 1

    return floored


def parse_llm_output(json_str: str) -> dict:
    """
    Cleans and parses a raw JSON string from the LLM output.
    Handles backtick blocks and <think> tags if present.
    Returns parsed Python dict.
    """
    if not isinstance(json_str, str):
        raise InvalidJsonFormatError("Expected a string as LLM response.")

    clean = json_str.strip()
    # Remove <think> sections
    if clean.startswith('<think>'):
        try:
            clean = clean.split('</think>')[1].strip()
        except Exception:
            raise InvalidJsonFormatError()

    # Remove Markdown-style code blocks
    if clean.startswith('```'):
        clean = clean.replace('```json', '').replace('```', '').strip()

    try:
        parsed = json.loads(clean)
        return parsed
    except json.JSONDecodeError:
        raise InvalidJsonFormatError()


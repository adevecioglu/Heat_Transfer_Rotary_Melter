"""JSON scenario input, preserving the existing V11 input envelope and fields."""
import json
import math
from pathlib import Path
from .Paths import DEFAULT_CONFIG


def load_inputs(path=DEFAULT_CONFIG):
    data = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(data, dict):
        raise ValueError('Scenario must be a JSON object.')
    inputs = data.get('inputs', data)
    if not isinstance(inputs, dict):
        raise ValueError('Scenario inputs must be an object.')
    for name, value in inputs.items():
        if isinstance(value, (int, float)) and not math.isfinite(value):
            raise ValueError(f'{name}: a finite number is required.')
    # The production engine performs its original schema and physical validation.
    return data


def save_inputs(data, path):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')

# Auto-generated safe helpers to avoid 'str' object has no attribute 'get' errors
from typing import Any, Mapping
import json
try:
    import yaml
    _has_yaml = True
except Exception:
    _has_yaml = False

def to_mapping(obj: Any) -> Mapping:
    if isinstance(obj, Mapping):
        return obj
    if isinstance(obj, str):
        # try JSON first
        try:
            parsed = json.loads(obj)
            if isinstance(parsed, Mapping):
                return parsed
        except Exception:
            pass
        # then YAML if available
        if _has_yaml:
            try:
                parsed = yaml.safe_load(obj)
                if isinstance(parsed, Mapping):
                    return parsed
            except Exception:
                pass
    # fallback empty mapping-like
    return {}

def get(obj: Any, key: Any, default: Any=None) -> Any:
    return to_mapping(obj).get(key, default)

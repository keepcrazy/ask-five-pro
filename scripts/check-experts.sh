#!/bin/bash
# Report whether the experts in the single bundled registry are readable.

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ASK_FIVE_DIR="${1:-$(cd "$SCRIPT_DIR/.." && pwd)}"
REGISTRY="$ASK_FIVE_DIR/brain-crew/expert-registry.json"

python3 - "$REGISTRY" <<'PY'
import json
import sys
from pathlib import Path

registry_path = Path(sys.argv[1]).resolve()
installed = []
simulated = []
warnings = []
try:
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    experts = data.get("experts")
    if not isinstance(experts, list) or not experts:
        raise ValueError("registry contains no experts")
    for expert in experts:
        expert_id = expert.get("id", "")
        path = Path(expert.get("path", ""))
        resolved = path if path.is_absolute() else registry_path.parent / path
        if resolved.is_file():
            installed.append(expert_id)
        else:
            simulated.append(expert_id)
except Exception as exc:
    warnings.append(str(exc))

print(json.dumps({
    "installed": installed,
    "simulated": simulated,
    "warnings": warnings,
}, ensure_ascii=False))
sys.exit(0 if not simulated and not warnings else 1)
PY

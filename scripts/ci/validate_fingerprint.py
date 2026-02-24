#!/usr/bin/env python3
"""
Valida estrutura e fingerprint SHA-256 do ruleset JSON.

Uso:
    python scripts/ci/validate_fingerprint.py services/atlas-engine/config/atlas_ruleset_v0.2.json

Verifica:
  1. Arquivo é JSON válido
  2. Contém chaves obrigatórias (version, metadata, caps_fator_custo, gating_rules)
  3. Cada regra tem rule_id único
  4. Imprime SHA-256 do conteúdo
"""
import hashlib
import json
import sys
from pathlib import Path


REQUIRED_KEYS = {"version", "metadata", "caps_fator_custo", "gating_rules"}
RULE_GROUPS = ["gating_rules", "regras_compostas", "regras_simples"]


def main(ruleset_path: str) -> int:
    p = Path(ruleset_path)
    if not p.exists():
        print(f"ERRO: arquivo não encontrado: {p}", file=sys.stderr)
        return 1

    raw = p.read_text(encoding="utf-8")

    # 1. JSON válido
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERRO: JSON inválido — {e}", file=sys.stderr)
        return 1

    # 2. Chaves obrigatórias
    missing = REQUIRED_KEYS - set(data.keys())
    if missing:
        print(f"ERRO: chaves obrigatórias ausentes: {missing}", file=sys.stderr)
        return 1

    # 3. rule_id únicos
    seen_ids: set[str] = set()
    duplicates: list[str] = []
    total_rules = 0
    for group in RULE_GROUPS:
        for rule in data.get(group, []) or []:
            rid = rule.get("rule_id", "")
            total_rules += 1
            if rid in seen_ids:
                duplicates.append(rid)
            seen_ids.add(rid)

    if duplicates:
        print(f"ERRO: rule_id duplicados: {duplicates}", file=sys.stderr)
        return 1

    # 4. SHA-256
    sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    print(f"Fingerprint validation: OK")
    print(f"  arquivo      : {p}")
    print(f"  version      : {data.get('version')}")
    print(f"  total regras : {total_rules}")
    print(f"  SHA-256      : {sha}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python validate_fingerprint.py <caminho_ruleset.json>", file=sys.stderr)
        sys.exit(1)
    sys.exit(main(sys.argv[1]))

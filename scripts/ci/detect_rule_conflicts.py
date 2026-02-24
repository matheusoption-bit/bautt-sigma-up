#!/usr/bin/env python3
"""
Detecta conflitos potenciais entre regras do ruleset ATLAS.

Uso:
    python scripts/ci/detect_rule_conflicts.py services/atlas-engine/config/atlas_ruleset_v0.2.json

Verificações:
  1. Duas regras com mesma macroetapa e estratégias conflitantes (multiply vs max_factor)
  2. Cap warning > cap maximo (inconsistência)
  3. Regras com prioridade duplicada no mesmo grupo
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

RULE_GROUPS = ["gating_rules", "regras_compostas", "regras_simples"]


def main(ruleset_path: str) -> int:
    p = Path(ruleset_path)
    if not p.exists():
        print(f"ERRO: arquivo não encontrado: {p}", file=sys.stderr)
        return 1

    data = json.loads(p.read_text(encoding="utf-8"))
    conflicts: list[str] = []

    # 1. Conflitos de estratégia por macroetapa
    macro_strategies: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for group in RULE_GROUPS:
        for rule in data.get(group, []) or []:
            strategy = (rule.get("conflict_resolution") or {}).get("strategy", "max_factor")
            for macro in (rule.get("effect") or {}).get("macro_factors", {}).keys():
                macro_strategies[macro].append((rule.get("rule_id", "?"), strategy))

    for macro, entries in macro_strategies.items():
        strategies = {s for _, s in entries}
        if len(strategies) > 1:
            details = "; ".join(f"{rid}={s}" for rid, s in entries)
            conflicts.append(
                f"Macroetapa '{macro}': estratégias conflitantes ({', '.join(strategies)}): {details}"
            )

    # 2. Inconsistência cap_warning > cap_maximo
    caps = data.get("caps_fator_custo", {}).get("default", {})
    for macro, cfg in caps.items():
        cw = cfg.get("cap_warning")
        cm = cfg.get("cap_maximo")
        if cw is not None and cm is not None and float(cw) > float(cm):
            conflicts.append(
                f"Cap inconsistente para '{macro}': cap_warning={cw} > cap_maximo={cm}"
            )

    # 3. Prioridades duplicadas dentro do mesmo grupo
    for group in RULE_GROUPS:
        prio_map: dict[int, list[str]] = defaultdict(list)
        for rule in data.get(group, []) or []:
            prio_map[int(rule.get("priority", 0))].append(rule.get("rule_id", "?"))
        for prio, rids in prio_map.items():
            if len(rids) > 1:
                conflicts.append(
                    f"Prioridade {prio} duplicada em '{group}': {rids}"
                )

    if conflicts:
        print(f"AVISO: {len(conflicts)} conflito(s) detectado(s):", file=sys.stderr)
        for c in conflicts:
            print(f"  - {c}", file=sys.stderr)
        # Retorna 0 (warning, não blocking) — estratégias mistas podem ser intencionais
        # Se quiser tornar blocking, troque para return 1
        print(f"Rule conflict detection: {len(conflicts)} warning(s)")
        return 0

    print("Rule conflict detection: OK — nenhum conflito encontrado")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python detect_rule_conflicts.py <caminho_ruleset.json>", file=sys.stderr)
        sys.exit(1)
    sys.exit(main(sys.argv[1]))

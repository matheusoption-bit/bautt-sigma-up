#!/usr/bin/env python3
"""
Auditoria automatica do ruleset do ATLAS.
Detecta conflitos, caps invalidos, e vulnerabilidades de logica.
"""

import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import argparse


class RulesetAuditor:
    """Auditor de ruleset com deteccao de conflitos e vulnerabilidades."""
    
    def __init__(self, ruleset_path: str, strict: bool = False):
        self.ruleset_path = Path(ruleset_path)
        self.strict = strict
        self.ruleset = self._load_ruleset()
        self.issues = []
        self.warnings = []
        self.stats = defaultdict(int)
    
    def _load_ruleset(self) -> Dict:
        try:
            with open(self.ruleset_path) as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar ruleset: {e}")
            sys.exit(1)
    
    def audit_fingerprint(self) -> bool:
        ruleset_str = json.dumps(self.ruleset, sort_keys=True)
        calculated = hashlib.sha256(ruleset_str.encode()).hexdigest()[:16]
        declared = self.ruleset.get("fingerprint", "")
        
        if calculated != declared:
            self.issues.append({
                "type": "FINGERPRINT_MISMATCH",
                "severity": "CRITICAL",
                "message": f"Fingerprint invalido. Calc: {calculated}, Decl: {declared}"
            })
            return False
        return True
    
    def detect_multiply_max_conflicts(self) -> List[Dict]:
        conflicts = []
        rules = self.ruleset.get("regras_compostas", [])
        groups = defaultdict(list)
        
        for rule in rules:
            key = (
                rule.get("target", {}).get("macroetapa"),
                rule.get("target", {}).get("output_field")
            )
            groups[key].append(rule)
        
        for (macro, field), rule_list in groups.items():
            if len(rule_list) > 1:
                strategies = {r.get("aggregation_strategy") for r in rule_list}
                if len(strategies) > 1:
                    conflicts.append({
                        "macroetapa": macro,
                        "field": field,
                        "strategies": list(strategies)
                    })
        
        for conflict in conflicts:
            self.issues.append({
                "type": "STRATEGY_CONFLICT",
                "severity": "CRITICAL",
                "message": f"Conflito em {conflict['macroetapa']}.{conflict['field']}"
            })
        
        return conflicts
    
    def audit_caps(self) -> List[Dict]:
        invalid_caps = []
        global_caps = self.ruleset.get("caps", {})
        
        for field, value in global_caps.items():
            if not isinstance(value, (int, float)) or value < 1.0 or value > 10.0:
                invalid_caps.append({
                    "location": "global",
                    "field": field,
                    "value": value
                })
        
        if invalid_caps:
            for cap in invalid_caps:
                self.issues.append({
                    "type": "INVALID_CAP",
                    "severity": "HIGH",
                    "message": f"Cap invalido em {cap['location']}.{cap['field']}: {cap['value']}"
                })
        
        return invalid_caps
    
    def audit_gating_rules(self) -> List[Dict]:
        gating_issues = []
        gatings = self.ruleset.get("gating", [])
        
        for gating in gatings:
            rule_id = gating.get("rule_id")
            logic = gating.get("logic", "all")
            conditions = gating.get("conditions", [])
            
            if logic == "all" and len(conditions) > 1:
                gating_issues.append({
                    "rule_id": rule_id,
                    "reason": "Gating com logic='all' pode ter falsos negativos"
                })
        
        return gating_issues
    
    def run_full_audit(self):
        print(f"Auditando ruleset: {self.ruleset_path}")
        self.audit_fingerprint()
        self.detect_multiply_max_conflicts()
        self.audit_caps()
        self.audit_gating_rules()
        
        critical = len([i for i in self.issues if i["severity"] == "CRITICAL"])
        success = (not self.strict and critical == 0) or (self.strict and len(self.issues) == 0)
        
        return success, {
            "issues": self.issues,
            "warnings": self.warnings,
            "stats": dict(self.stats)
        }
    
    def generate_markdown_report(self) -> str:
        lines = ["# Ruleset Audit Report\n"]
        lines.append(f"**File:** `{self.ruleset_path}`\n")
        
        if self.issues:
            lines.append("## Issues\n")
            for issue in self.issues:
                lines.append(f"- **{issue['type']}** ({issue['severity']}): {issue['message']}\n")
        else:
            lines.append("## Nenhum issue encontrado\n")
        
        return "".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ruleset", required=True)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--output-format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--output")
    args = parser.parse_args()
    
    auditor = RulesetAuditor(args.ruleset, strict=args.strict)
    success, _ = auditor.run_full_audit()
    
    report = auditor.generate_markdown_report()
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
    else:
        print(report)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

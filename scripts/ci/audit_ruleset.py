# scripts/ci/audit_ruleset.py
"""
Auditoria automática do ruleset do ATLAS.
Detecta conflitos, caps inválidos, e vulnerabilidades de lógica.
"""

import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import argparse


class RulesetAuditor:
    """Auditor de ruleset com detecção de conflitos e vulnerabilidades."""
    
    def __init__(self, ruleset_path: str, strict: bool = False):
        self.ruleset_path = Path(ruleset_path)
        self.strict = strict
        self.ruleset = self._load_ruleset()
        self.issues = []
        self.warnings = []
        self.stats = defaultdict(int)
    
    def _load_ruleset(self) -> Dict:
        """Carrega e valida JSON do ruleset."""
        try:
            with open(self.ruleset_path) as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erro ao carregar ruleset: {e}")
            sys.exit(1)
    
    def audit_fingerprint(self) -> bool:
        """Valida que o fingerprint está correto."""
        ruleset_str = json.dumps(self.ruleset, sort_keys=True)
        calculated_hash = hashlib.sha256(ruleset_str.encode()).hexdigest()[:16]
        declared_hash = self.ruleset.get("fingerprint", "")
        
        if calculated_hash != declared_hash:
            self.issues.append({
                "type": "FINGERPRINT_MISMATCH",
                "severity": "CRITICAL",
                "message": f"Fingerprint não corresponde. Calculado: {calculated_hash}, Declarado: {declared_hash}"
            })
            return False
        
        self.stats["fingerprint_valid"] = 1
        return True
    
    def audit_version(self) -> bool:
        """Valida versionamento semântico."""
        version = self.ruleset.get("version", "")
        if not version or not version.count('.') == 2:
            self.issues.append({
                "type": "INVALID_VERSION",
                "severity": "HIGH",
                "message": f"Versão inválida: {version}. Use formato semver (ex: 0.2.0)"
            })
            return False
        
        self.stats["version_valid"] = 1
        return True
    
    def detect_multiply_max_conflicts(self) -> List[Dict]:
        """Detecta conflitos entre regras multiply e max_factor."""
        conflicts = []
        rules = self.ruleset.get("regras_compostas", [])
        
        # Agrupa regras por macroetapa + output_field
        groups = defaultdict(list)
        for rule in rules:
            key = (
                rule.get("target", {}).get("macroetapa"),
                rule.get("target", {}).get("output_field")
            )
            groups[key].append(rule)
        
        # Detecta conflitos
        for (macro, field), rule_list in groups.items():
            if len(rule_list) > 1:
                strategies = {r.get("aggregation_strategy") for r in rule_list}
                if len(strategies) > 1:
                    conflicts.append({
                        "macroetapa": macro,
                        "output_field": field,
                        "strategies": list(strategies),
                        "rule_ids": [r.get("rule_id") for r in rule_list]
                    })
        
        if conflicts:
            for conflict in conflicts:
                self.issues.append({
                    "type": "STRATEGY_CONFLICT",
                    "severity": "CRITICAL",
                    "message": f"Conflito em {conflict['macroetapa']}.{conflict['output_field']}: múltiplas estratégias {conflict['strategies']}",
                    "rule_ids": conflict['rule_ids']
                })
        
        self.stats["strategy_conflicts"] = len(conflicts)
        return conflicts
    
    def audit_caps(self) -> List[Dict]:
        """Valida que todos os caps estão dentro de limites razoáveis."""
        invalid_caps = []
        
        # Caps globais
        global_caps = self.ruleset.get("caps", {})
        for field, value in global_caps.items():
            if not isinstance(value, (int, float)) or value < 1.0 or value > 10.0:
                invalid_caps.append({
                    "location": "global",
                    "field": field,
                    "value": value,
                    "reason": "Cap fora do range [1.0, 10.0]"
                })
        
        # Caps regionais
        for region, config in self.ruleset.get("regional_overrides", {}).items():
            for field, value in config.get("caps", {}).items():
                if not isinstance(value, (int, float)) or value < 1.0 or value > 10.0:
                    invalid_caps.append({
                        "location": f"regional.{region}",
                        "field": field,
                        "value": value,
                        "reason": "Cap fora do range [1.0, 10.0]"
                    })
        
        if invalid_caps:
            for cap_issue in invalid_caps:
                self.issues.append({
                    "type": "INVALID_CAP",
                    "severity": "HIGH",
                    "message": f"Cap inválido em {cap_issue['location']}.{cap_issue['field']}: {cap_issue['value']}",
                    "details": cap_issue
                })
        
        self.stats["invalid_caps"] = len(invalid_caps)
        return invalid_caps
    
    def audit_gating_rules(self) -> List[Dict]:
        """Valida regras de gating para evitar falsos positivos/negativos."""
        gating_issues = []
        gatings = self.ruleset.get("gating", [])
        
        for gating in gatings:
            rule_id = gating.get("rule_id")
            logic = gating.get("logic", "all")
            conditions = gating.get("conditions", [])
            
            # Detecta gating com "all" que pode ser burglado
            if logic == "all" and len(conditions) > 1:
                # Verifica se todas as condições são obrigatórias
                optional_fields = self._get_optional_fields()
                gating_fields = {c.get("metric") for c in conditions}
                
                if gating_fields & optional_fields:
                    gating_issues.append({
                        "rule_id": rule_id,
                        "reason": "Gating com logic='all' inclui campos opcionais",
                        "optional_fields": list(gating_fields & optional_fields)
                    })
            
            # Detecta gating sem validação de flags_risco
            if rule_id in ["ATLAS_COMBO_004", "ATLAS_COMBO_005"]:
                has_flags_check = any("flags_risco" in str(c) for c in conditions)
                if not has_flags_check:
                    gating_issues.append({
                        "rule_id": rule_id,
                        "reason": "Gating jurídico sem validação de flags_risco"
                    })
        
        if gating_issues:
            for issue in gating_issues:
                self.issues.append({
                    "type": "GATING_VULNERABILITY",
                    "severity": "CRITICAL",
                    "message": f"Vulnerabilidade em gating {issue['rule_id']}: {issue['reason']}",
                    "details": issue
                })
        
        self.stats["gating_issues"] = len(gating_issues)
        return gating_issues
    
    def _get_optional_fields(self) -> set:
        """Retorna campos que são opcionais no schema."""
        # Campos que podem ser None/null no TerrainMetricsInput
        return {
            "pct_app_area",
            "overlaps_area_uniao",
            "historico_deslizamento_r4",
            "proximidade_erosao_m",
            "distancia_saneamento_km"
        }
    
    def audit_score_penalties(self) -> List[Dict]:
        """Valida penalidades de score por alertas."""
        penalty_issues = []
        
        # Verifica se há mapeamento de severidade -> penalidade
        penalties = self.ruleset.get("alert_penalty_map", {})
        
        if not penalties:
            penalty_issues.append({
                "reason": "Nenhum alert_penalty_map definido",
                "impact": "Alertas não afetam score"
            })
        else:
            # Valida valores
            if penalties.get("info", 0) > 0:
                penalty_issues.append({
                    "severity": "info",
                    "penalty": penalties["info"],
                    "reason": "Info não deveria penalizar score"
                })
            
            if penalties.get("critical", 0) < 10:
                penalty_issues.append({
                    "severity": "critical",
                    "penalty": penalties.get("critical", 0),
                    "reason": "Penalidade de critical muito baixa"
                })
        
        if penalty_issues:
            for issue in penalty_issues:
                self.warnings.append({
                    "type": "SCORE_PENALTY",
                    "severity": "MEDIUM",
                    "message": f"Problema em penalidades: {issue.get('reason')}",
                    "details": issue
                })
        
        self.stats["penalty_issues"] = len(penalty_issues)
        return penalty_issues
    
    def run_full_audit(self) -> Tuple[bool, Dict]:
        """Executa auditoria completa."""
        print("🔍 Iniciando auditoria do ruleset...")
        print(f"📁 Arquivo: {self.ruleset_path}")
        print(f"⚙️  Modo: {'STRICT' if self.strict else 'NORMAL'}\n")
        
        # Executa todas as auditorias
        self.audit_fingerprint()
        self.audit_version()
        self.detect_multiply_max_conflicts()
        self.audit_caps()
        self.audit_gating_rules()
        self.audit_score_penalties()
        
        # Compilar resultados
        critical_count = len([i for i in self.issues if i["severity"] == "CRITICAL"])
        high_count = len([i for i in self.issues if i["severity"] == "HIGH"])
        
        success = (
            (not self.strict and critical_count == 0) or
            (self.strict and len(self.issues) == 0 and len(self.warnings) == 0)
        )
        
        return success, {
            "success": success,
            "issues": self.issues,
            "warnings": self.warnings,
            "stats": dict(self.stats),
            "summary": {
                "total_issues": len(self.issues),
                "critical": critical_count,
                "high": high_count,
                "medium": len([i for i in self.issues if i["severity"] == "MEDIUM"]),
                "warnings": len(self.warnings)
            }
        }
    
    def generate_report(self, format: str = "markdown") -> str:
        """Gera relatório em formato especificado."""
        if format == "markdown":
            return self._generate_markdown_report()
        elif format == "json":
            return json.dumps({
                "issues": self.issues,
                "warnings": self.warnings,
                "stats": dict(self.stats)
            }, indent=2)
        else:
            raise ValueError(f"Formato não suportado: {format}")
    
    def _generate_markdown_report(self) -> str:
        """Gera relatório em Markdown."""
        lines = []
        lines.append("# 🔍 Ruleset Audit Report\n")
        lines.append(f"**File:** `{self.ruleset_path}`  ")
        lines.append(f"**Version:** {self.ruleset.get('version', 'N/A')}  ")
        lines.append(f"**Fingerprint:** `{self.ruleset.get('fingerprint', 'N/A')}`\n")
        
        # Summary
        summary = {
            "total_issues": len(self.issues),
            "critical": len([i for i in self.issues if i["severity"] == "CRITICAL"]),
            "high": len([i for i in self.issues if i["severity"] == "HIGH"]),
            "warnings": len(self.warnings)
        }
        
        lines.append("## 📊 Summary\n")
        lines.append(f"- **Total Issues:** {summary['total_issues']}")
        lines.append(f"- **Critical:** {summary['critical']}")
        lines.append(f"- **High:** {summary['high']}")
        lines.append(f"- **Warnings:** {summary['warnings']}\n")
        
        # Issues
        if self.issues:
            lines.append("## ❌ Issues\n")
            for issue in sorted(self.issues, key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}.get(x["severity"], 3)):
                severity_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡"}.get(issue["severity"], "⚪")
                lines.append(f"### {severity_emoji} {issue['type']} ({issue['severity']})\n")
                lines.append(f"{issue['message']}\n")
                if "details" in issue:
                    lines.append(f"```json\n{json.dumps(issue['details'], indent=2)}\n```\n")
        
        # Warnings
        if self.warnings:
            lines.append("## ⚠️ Warnings\n")
            for warning in self.warnings:
                lines.append(f"- **{warning['type']}:** {warning['message']}\n")
        
        # Stats
        if self.stats:
            lines.append("## 📈 Statistics\n")
            for key, value in self.stats.items():
                lines.append(f"- `{key}`: {value}")
        
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Auditoria de ruleset do ATLAS")
    parser.add_argument("--ruleset", required=True, help="Caminho para o arquivo ruleset JSON")
    parser.add_argument("--strict", action="store_true", help="Modo strict (falha em warnings)")
    parser.add_argument("--output-format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--output", help="Arquivo de saída (default: stdout)")
    
    args = parser.parse_args()
    
    auditor = RulesetAuditor(args.ruleset, strict=args.strict)
    success, results = auditor.run_full_audit()
    
    report = auditor.generate_report(format=args.output_format)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"✅ Relatório salvo em: {args.output}")
    else:
        print(report)
    
    # Exit code
    if not success:
        print("\n❌ Auditoria FALHOU!")
        sys.exit(1)
    else:
        print("\n✅ Auditoria PASSOU!")
        sys.exit(0)


if __name__ == "__main__":
    main()

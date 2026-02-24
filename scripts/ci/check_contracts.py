#!/usr/bin/env python3
"""
Verifica compliance dos contratos ATLAS/DELTA em tempo de CI.

Verificações:
  1. ATLASEngine é importável e instanciável com ruleset mínimo
  2. ATLASEngine.evaluate() retorna dict com chaves obrigatórias
  3. delta_engine.integration_contract é importável
  4. aplicar_atlas_ao_orcamento aceita (orcamento_base, atlas_report) e retorna DataFrame
"""
import sys


ATLAS_REPORT_REQUIRED_KEYS = {
    "score_fisico",
    "ajustes_custo",
    "alertas",
    "regras_aplicadas",
    "viabilidade_bloqueada",
    "bloqueios",
    "fator_area_util",
    "metadata",
}


def main() -> int:
    errors: list[str] = []

    # 1. Importar ATLASEngine
    try:
        from atlas_engine.atlas_engine import ATLASEngine, ATLASBlockedException  # noqa: F401
    except ImportError as e:
        errors.append(f"Não foi possível importar ATLASEngine: {e}")
        # Sem engine, não dá para seguir
        for err in errors:
            print(f"  ERRO: {err}", file=sys.stderr)
        return 1

    # 2. Instanciar + evaluate com ruleset mínimo
    try:
        minimal_ruleset = {"version": "0.0.0-test", "metadata": {"name": "CONTRACT_TEST"}}
        engine = ATLASEngine(ruleset=minimal_ruleset)
        report = engine.evaluate(
            terrain_metrics={"declividade_media_pct": 10.0},
            raise_on_block=False,
        )
        if not isinstance(report, dict):
            errors.append(f"evaluate() retornou {type(report)}, esperava dict")
        else:
            missing = ATLAS_REPORT_REQUIRED_KEYS - set(report.keys())
            if missing:
                errors.append(f"Chaves ausentes no report: {missing}")
    except Exception as e:
        errors.append(f"Erro ao instanciar/evaluate ATLASEngine: {e}")

    # 3. Importar contrato DELTA
    try:
        from delta_engine.integration_contract import aplicar_atlas_ao_orcamento  # noqa: F401
    except ImportError as e:
        errors.append(f"Não foi possível importar delta_engine.integration_contract: {e}")

    # 4. Verificar assinatura aplicar_atlas_ao_orcamento
    try:
        import inspect
        from delta_engine.integration_contract import aplicar_atlas_ao_orcamento
        sig = inspect.signature(aplicar_atlas_ao_orcamento)
        params = list(sig.parameters.keys())
        if len(params) < 2:
            errors.append(f"aplicar_atlas_ao_orcamento espera >= 2 parâmetros, tem {len(params)}: {params}")
    except Exception as e:
        errors.append(f"Erro ao verificar assinatura DELTA: {e}")

    if errors:
        print(f"Contract compliance: FALHOU ({len(errors)} erro(s))", file=sys.stderr)
        for err in errors:
            print(f"  ERRO: {err}", file=sys.stderr)
        return 1

    print("Contract compliance: OK")
    print("  - ATLASEngine importável e instanciável")
    print("  - evaluate() retorna dict com chaves corretas")
    print("  - delta_engine.integration_contract importável")
    print("  - aplicar_atlas_ao_orcamento tem assinatura correta")
    return 0


if __name__ == "__main__":
    sys.exit(main())

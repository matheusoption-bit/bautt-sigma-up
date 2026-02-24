from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator

ClusterRegional = Literal["SC_LITORAL", "SP_RMSP", "BR_DEFAULT"]

class InfraSaneamento(BaseModel):
    esgoto_proximo: Optional[bool] = None
    drenagem_superficial: Optional[Literal["boa", "regular", "precaria", "inexistente"]] = None

class TerrainMetricsInput(BaseModel):
    model_config = {"extra": "allow"}

    cluster_regional: ClusterRegional = "BR_DEFAULT"

    # common fields used by ATLAS ruleset
    estado: Optional[str] = None
    municipio: Optional[str] = None

    declividade_media_pct: Optional[float] = None
    declividade_max_pct: Optional[float] = None
    pct_app_area: Optional[float] = None

    solo_classe: Optional[str] = None
    tipo_solo: Optional[str] = None

    acesso_pavimentado: Optional[bool] = None
    distancia_pavimentacao_m: Optional[float] = None

    overlaps_area_uniao: Optional[bool] = None
    historico_deslizamento_r4: Optional[bool] = None
    flags_risco: Optional[List[str]] = None

    infra_saneamento: Optional[InfraSaneamento] = None

    # non-blocking warnings
    validation_warnings: List[str] = Field(default_factory=list)

    # critical field paths (dot-path) for FM-008 coverage scoring
    critical_fields: List[str] = Field(default_factory=lambda: [
        "declividade_media_pct",
        "solo_classe",
        "pct_app_area",
        "infra_saneamento.esgoto_proximo",
        "infra_saneamento.drenagem_superficial",
    ])

    @model_validator(mode="after")
    def _warn_missing_critical(self):
        crit = []
        if self.declividade_media_pct is None and self.declividade_max_pct is None:
            crit.append("declividade_media_pct/declividade_max_pct ausentes")
        if (self.solo_classe is None) and (self.tipo_solo is None):
            crit.append("solo_classe/tipo_solo ausentes")
        if self.pct_app_area is None:
            crit.append("pct_app_area ausente")
        if crit:
            self.validation_warnings.append("Dados insuficientes: " + "; ".join(crit))
        return self

    def terrain_metrics_dict(self) -> Dict[str, Any]:
        d = self.model_dump(exclude={"validation_warnings", "cluster_regional", "critical_fields"}, exclude_none=True)
        return d

    @staticmethod
    def get_by_path(obj: Dict[str, Any], path: str) -> Any:
        cur: Any = obj
        for part in path.split("."):
            if not isinstance(cur, dict):
                return None
            cur = cur.get(part)
            if cur is None:
                return None
        return cur

class AlertItem(BaseModel):
    severity: Literal["info", "warning", "critical"]
    code: str
    message: Optional[str] = Field(default=None, alias="message")
    mensagem: Optional[str] = Field(default=None)
    regra_id: Optional[str] = None
    macroetapa: Optional[str] = None

    model_config = {"populate_by_name": True, "extra": "allow"}

class ATLASReportResponse(BaseModel):
    score_fisico: int
    ajustes_custo: Dict[str, float] = Field(default_factory=dict)
    itens_custo_adicional: List[Dict[str, Any]] = Field(default_factory=list)
    fator_area_util: float = 1.0
    alertas: List[AlertItem] = Field(default_factory=list)
    regras_aplicadas: List[str] = Field(default_factory=list)
    viabilidade_bloqueada: bool = False
    bloqueios: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    breakdown_ajustes: List[Dict[str, Any]] = Field(default_factory=list)

class ApplyAtlasRequest(BaseModel):
    terrain_metrics: TerrainMetricsInput
    orcamento_base: Dict[str, Any]
    cluster_regional: ClusterRegional = "BR_DEFAULT"

class DeltaApplyResponse(BaseModel):
    atlas_report: ATLASReportResponse
    orcamento_ajustado: Optional[Dict[str, Any]] = None

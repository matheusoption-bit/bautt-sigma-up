# services/atlas-api/src/middleware/rate_limiter.py
"""
Rate limiter lógico baseado em fingerprint de payload.
Detecta tentativas de exploração por padrões repetitivos.
"""

import hashlib
import time
from typing import Dict, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from pydantic import BaseModel


class RateLimitConfig(BaseModel):
    """Configuração de rate limiting."""
    max_requests_per_minute: int = 60
    max_identical_payloads_per_hour: int = 5
    max_low_coverage_per_hour: int = 10
    suspicious_pattern_threshold: int = 3


class PayloadFingerprint(BaseModel):
    """Fingerprint de um payload."""
    hash: str
    timestamp: datetime
    coverage_score: Optional[float] = None
    critical_fields: Dict[str, any] = {}


class SmartRateLimiter:
    """
    Rate limiter inteligente que detecta padrões de exploração.
    Não apenas limita por IP, mas por comportamento suspeito.
    """
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self.payload_history: Dict[str, list[PayloadFingerprint]] = defaultdict(list)
        self.ip_requests: Dict[str, list[datetime]] = defaultdict(list)
        self.suspicious_ips: set = set()
    
    def _get_payload_fingerprint(self, payload: Dict) -> str:
        """Gera fingerprint do payload baseado em campos críticos."""
        critical_fields = {
            "declividade_media_pct": payload.get("declividade_media_pct"),
            "solo_classe": payload.get("solo_classe"),
            "pct_app_area": payload.get("pct_app_area"),
            "overlaps_area_uniao": payload.get("overlaps_area_uniao"),
            "flags_risco": tuple(sorted(payload.get("flags_risco", [])))
        }
        
        # Hash dos campos críticos
        fp_str = json.dumps(critical_fields, sort_keys=True)
        return hashlib.md5(fp_str.encode()).hexdigest()
    
    def _cleanup_old_entries(self, client_id: str):
        """Remove entradas antigas para evitar memory leak."""
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        one_minute_ago = now - timedelta(minutes=1)
        
        # Limpa payload history (1 hora)
        if client_id in self.payload_history:
            self.payload_history[client_id] = [
                fp for fp in self.payload_history[client_id]
                if fp.timestamp > one_hour_ago
            ]
        
        # Limpa IP requests (1 minuto)
        if client_id in self.ip_requests:
            self.ip_requests[client_id] = [
                ts for ts in self.ip_requests[client_id]
                if ts > one_minute_ago
            ]
    
    def check_rate_limit(self, request: Request, payload: Dict) -> Optional[Dict]:
        """
        Verifica se a requisição deve ser bloqueada.
        Retorna None se OK, ou dict com detalhes do bloqueio.
        """
        client_ip = request.client.host
        now = datetime.now()
        
        # Cleanup
        self._cleanup_old_entries(client_ip)
        
        # 1. Rate limit básico por IP (requests/minuto)
        self.ip_requests[client_ip].append(now)
        if len(self.ip_requests[client_ip]) > self.config.max_requests_per_minute:
            return {
                "blocked": True,
                "reason": "RATE_LIMIT_EXCEEDED",
                "message": f"Máximo de {self.config.max_requests_per_minute} requisições por minuto excedido",
                "retry_after": 60
            }
        
        # 2. Detectar payloads idênticos repetidos
        payload_fp = self._get_payload_fingerprint(payload)
        fingerprint = PayloadFingerprint(
            hash=payload_fp,
            timestamp=now,
            coverage_score=payload.get("metadata", {}).get("coverage_score"),
            critical_fields={
                "declividade_media_pct": payload.get("declividade_media_pct"),
                "pct_app_area": payload.get("pct_app_area"),
                "overlaps_area_uniao": payload.get("overlaps_area_uniao")
            }
        )
        
        self.payload_history[client_ip].append(fingerprint)
        
        # Contar payloads idênticos na última hora
        identical_count = sum(
            1 for fp in self.payload_history[client_ip]
            if fp.hash == payload_fp
        )
        
        if identical_count > self.config.max_identical_payloads_per_hour:
            self.suspicious_ips.add(client_ip)
            return {
                "blocked": True,
                "reason": "SUSPICIOUS_PATTERN_DETECTED",
                "message": f"Payload idêntico enviado {identical_count} vezes na última hora",
                "retry_after": 3600,
                "fingerprint": payload_fp
            }
        
        # 3. Detectar tentativas de exploração por coverage baixo
        low_coverage_count = sum(
            1 for fp in self.payload_history[client_ip]
            if fp.coverage_score is not None and fp.coverage_score < 0.4
        )
        
        if low_coverage_count > self.config.max_low_coverage_per_hour:
            self.suspicious_ips.add(client_ip)
            return {
                "blocked": True,
                "reason": "LOW_COVERAGE_ABUSE",
                "message": f"{low_coverage_count} requisições com coverage < 0.4 na última hora",
                "retry_after": 3600
            }
        
        # 4. Detectar tentativas de bypass de gating
        gating_bypass_patterns = self._detect_gating_bypass_attempts(client_ip)
        if gating_bypass_patterns:
            self.suspicious_ips.add(client_ip)
            return {
                "blocked": True,
                "reason": "GATING_BYPASS_ATTEMPT",
                "message": "Padrão de tentativa de bypass de gating detectado",
                "patterns": gating_bypass_patterns,
                "retry_after": 3600
            }
        
        return None  # OK
    
    def _detect_gating_bypass_attempts(self, client_ip: str) -> list:
        """Detecta padrões de tentativa de bypass de gating."""
        patterns = []
        recent_payloads = self.payload_history[client_ip][-10:]  # Últimos 10
        
        if len(recent_payloads) < 3:
            return patterns
        
        # Padrão 1: Variação mínima em pct_app_area próximo ao limiar (10%)
        app_areas = [
            fp.critical_fields.get("pct_app_area")
            for fp in recent_payloads
            if fp.critical_fields.get("pct_app_area") is not None
        ]
        
        if len(app_areas) >= 3:
            # Verifica se há múltiplas tentativas entre 9.5% e 10.5%
            threshold_attempts = [a for a in app_areas if 9.5 <= a <= 10.5]
            if len(threshold_attempts) >= 3:
                patterns.append({
                    "type": "THRESHOLD_PROBING",
                    "field": "pct_app_area",
                    "values": threshold_attempts
                })
        
        # Padrão 2: Alternância entre overlaps_area_uniao true/false
        overlaps = [
            fp.critical_fields.get("overlaps_area_uniao")
            for fp in recent_payloads[-5:]
            if fp.critical_fields.get("overlaps_area_uniao") is not None
        ]
        
        if len(overlaps) >= 4:
            # Verifica alternância
            alternations = sum(1 for i in range(len(overlaps)-1) if overlaps[i] != overlaps[i+1])
            if alternations >= 2:
                patterns.append({
                    "type": "VALUE_ALTERNATION",
                    "field": "overlaps_area_uniao",
                    "pattern": overlaps
                })
        
        return patterns
    
    async def middleware(self, request: Request, call_next):
        """Middleware para FastAPI."""
        # Apenas aplica rate limit em endpoints de avaliação
        if not request.url.path.startswith("/atlas/evaluate"):
            return await call_next(request)
        
        # Extrai payload
        try:
            body = await request.body()
            payload = json.loads(body) if body else {}
        except:
            payload = {}
        
        # Verifica rate limit
        block_result = self.check_rate_limit(request, payload)
        
        if block_result:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": block_result["message"],
                    "retry_after": block_result["retry_after"],
                    "details": block_result
                }
            )
        
        response = await call_next(request)
        return response


# Instância global
rate_limiter = SmartRateLimiter()

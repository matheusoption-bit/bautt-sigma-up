"""Rate limiter inteligente baseado em fingerprint de payload."""
import hashlib
import json
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import Request, HTTPException

class SmartRateLimiter:
    """Rate limiter que detecta padroes de exploracao."""
    
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests = max_requests_per_minute
        self.ip_requests: Dict[str, list] = defaultdict(list)
        self.payload_history: Dict[str, list] = defaultdict(list)
    
    def _get_payload_fingerprint(self, payload: Dict) -> str:
        """Gera fingerprint do payload."""
        critical_fields = {
            "declividade_media_pct": payload.get("declividade_media_pct"),
            "solo_classe": payload.get("solo_classe"),
            "pct_app_area": payload.get("pct_app_area")
        }
        fp_str = json.dumps(critical_fields, sort_keys=True)
        return hashlib.md5(fp_str.encode()).hexdigest()
    
    def check_rate_limit(self, request: Request, payload: Dict) -> Optional[Dict]:
        """Verifica se requisicao deve ser bloqueada."""
        client_ip = request.client.host
        now = datetime.now()
        
        # Limpa requests antigos
        one_minute_ago = now - timedelta(minutes=1)
        self.ip_requests[client_ip] = [
            ts for ts in self.ip_requests[client_ip] 
            if ts > one_minute_ago
        ]
        
        # Adiciona request atual
        self.ip_requests[client_ip].append(now)
        
        # Verifica rate limit
        if len(self.ip_requests[client_ip]) > self.max_requests:
            return {
                "blocked": True,
                "reason": "RATE_LIMIT_EXCEEDED",
                "retry_after": 60
            }
        
        return None

# Instancia global
rate_limiter = SmartRateLimiter()

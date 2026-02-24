# legacy/

Arquivos **preservados para referência histórica**. Não usar em produção.

| Arquivo | Substituto canônico |
|---|---|
| `delta_integration_contract.py` | `services/delta-engine/src/delta_engine/integration_contract.py` |
| `atlas_engine_v02.py` | `services/atlas-engine/src/atlas_engine/atlas_engine.py` |

## Por que existem aqui?

Esses arquivos eram a implementação original antes da migração para a estrutura
`services/<nome>/src/<package>/`. Foram mantidos aqui para referência de diff,
sem nenhum import apontando para eles no código atual.

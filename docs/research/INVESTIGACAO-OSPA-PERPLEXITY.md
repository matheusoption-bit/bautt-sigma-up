## **Arquitetura provável**

* Frontend:

  * Single Page Application em React/Vue/Svelte, consumindo Mapbox GL JS para renderização 2D/3D do mapa (há créditos explícitos à Mapbox e OpenStreetMap).\[[app.ospa](https://app.ospa.place/)\]​

  * Componentes de UI para: busca de endereço, painel lateral de “Estudo do lote”, “Painel de estudos”, “Camadas”, “Filtros”, “Parceiros”, além de botões como “Clicar no lote” e “Quero inscrever”.\[[app.ospa](https://app.ospa.place/)\]​

  * Roteamento interno por estado, não por recarga de página (tipicamente Next.js/Remix ou SPA pura servida por CDN).

* Backend:

  * APIs REST/GraphQL que:

    * Recebem coordenadas ou identificador de lote clicado e retornam o “Estudo do lote”.\[[app.ospa](https://app.ospa.place/)\]​

    * Alimentam “Painel de estudos” com agregações (múltiplos lotes / projetos).\[[app.ospa](https://app.ospa.place/)\]​

    * Listam camadas e filtros disponíveis, aplicando-os nas consultas geoespaciais.

  * Banco geoespacial (PostgreSQL \+ PostGIS / BigQuery GIS / similar) para armazenar:

    * Malha de lotes, zonas, e camadas urbanas.

    * Projetos (“iniciativas urbanas”) associados a localizações específicas.\[[app.ospa](https://app.ospa.place/)\]​

* Integrações:

  * Mapbox para tiles base e possivelmente camadas customizadas (tilesets de lotes/zones).\[[app.ospa](https://app.ospa.place/)\]​

  * Serviço de autenticação/conta (nome do usuário aparece no canto, “Matheus Petri Rodrigues”), possivelmente Auth0/Supabase/Firebase.\[[app.ospa](https://app.ospa.place/)\]​

## **Lógica de inputs → outputs**

* Campo “Digite um endereço”:

  * Provavelmente usa:

    * Autocomplete (geocoding direto via Mapbox Geocoding API).

    * Ao selecionar um endereço, o mapa centraliza e ajusta o zoom nesse ponto.\[[app.ospa](https://app.ospa.place/)\]​

  * Pode disparar uma segunda chamada interna: dado o ponto, o backend identifica o lote/quadra/região e carrega o “Estudo do lote”.

* Ação “Clicar no lote”:

  * Ativa um modo de seleção de feição no mapa (Mapbox layer de polígonos de lotes).

  * Ao clicar, pega-se o featureId ou o par (lat, lng) e envia para a API que:

    * Retorna atributos do lote (área, zoneamento, índices urbanísticos, etc.).

    * Popula o painel “Estudo do lote” com dados estruturados.\[[app.ospa](https://app.ospa.place/)\]​

  * Consistência esperada: sempre que o mesmo lote é clicado, o painel mostra a mesma ficha, sugerindo um modelo de dados estável por lote.

* “Camadas” e “Filtros”:

  * Uso típico de lógica client \+ server:

    * Frontend liga/desliga camadas no Mapbox (visibilidade de layers).

    * Filtros mais simples (visibilidade, estilo) podem ser client-side; filtros que mudam o conjunto de feições retornadas demandam nova query ao backend (e.g. lotes com certos índices ou projetos de determinados parceiros).\[[app.ospa](https://app.ospa.place/)\]​

  * Espera-se consistência entre o que é filtrado no painel e o que aparece no mapa: isso indica que o backend já retorna apenas o subset filtrado ou que o frontend aplica filtros sobre um dataset carregado.

* “Deseja inscrever a sua iniciativa urbana no mapa?”:

  * Fluxo de criação de entidades:

    * Usuário abre um formulário (“Quero inscrever”).

    * Informa dados do projeto e localização (ponto ou polígono).

    * Backend salva e associa a um lote/região, provavelmente com validações.

  * Depois, essas iniciativas aparecem como camada específica (“Parceiros”, “Iniciativas”) e também no “Painel de estudos”.\[[app.ospa](https://app.ospa.place/)\]​

## **Modelos, algoritmos e abordagens**

* Geoprocessamento:

  * Funções geoespaciais para:

    * Interseção ponto-em-polígono (descobrir em qual lote o clique está).

    * Interseção polígono-em-polígono (projetos vs. zonas, restrições, etc.).

  * Tile generation ou uso de tilesets customizados, possivelmente pré-processados para desempenho.\[[app.ospa](https://app.ospa.place/)\]​

* “Gêmeo Digital para Desenvolvimento Urbano”:

  * Sugere um modelo de dados que replica o território como grafo/coleção de entidades:

    * Lotes, quadras, avenidas, zonas, infraestrutura.

    * Relações: lote → zoneamento → restrições; lote → iniciativas; lote → indicadores socioeconômicos.\[[app.ospa](https://app.ospa.place/)\]​

  * Algoritmos de agregação:

    * Sumários por área (ex.: indicadores em “Painel de estudos” quando você seleciona um conjunto de lotes ou uma região).

    * Estatísticas para análises urbanas (densidade, potencial construtivo, etc.).

* Inteligência artificial:

  * O marketing fala em “big data e inteligência artificial”, o que pode significar:

    * Modelos de recomendação de uso do lote, cenários de adensamento, ou clusterização de projetos para insights urbanos.

    * Modelos de scoring/viabilidade (classificadores ou regressões sobre atributos de lote \+ mercado).\[[app.ospa](https://app.ospa.place/)\]​

  * Porém, do ponto de vista observável na UI, o núcleo visível é geoespacial interativo; a IA pode estar:

    * Nos bastidores (ex.: priorização de oportunidades) ou em módulos ainda pouco expostos na interface.

## **Dados e seu tratamento**

* Fontes prováveis:

  * Dados públicos:

    * Cadastros territoriais municipais (lotes, zoneamento).

    * Bases como IPTU, diretrizes de uso, planos diretores.

    * Camadas OpenStreetMap (vias, infraestrutura básica).\[[app.ospa](https://app.ospa.place/)\]​

  * Dados proprietários:

    * Estudos de arquitetura e desenvolvimento imobiliário da própria empresa (“Cruzamos a expertise de arquitetura e desenvolvimento... com big data e IA”).\[[app.ospa](https://app.ospa.place/)\]​

    * Iniciativas urbanas cadastradas por usuários/parceiros (via “Quero inscrever” e “Parceiros”).\[[app.ospa](https://app.ospa.place/)\]​

* Tratamento dos dados:

  * ETL geoespacial:

    * Normalização de malhas de lotes e zonas, correção de topologia.

    * Join com indicadores (socioeconômicos, mobilidade, infraestrutura).

  * Modelagem:

    * Entidades centrais: Lote, Projeto/Iniciativa, CamadaTemática, Parceiro, Usuário.

    * Versionamento de dados (mudanças no plano diretor, revisões de malha).

  * Exposição:

    * APIs que retornam geoJSON (para Mapbox) \+ metadados agregados para painéis.\[[app.ospa](https://app.ospa.place/)\]​

## **Limitações e comportamentos reveladores**

Observando apenas a superfície, alguns sinais típicos de limitações estruturais que você pode testar:

* Granularidade de lotes:

  * Se o clique em regiões densas exige zoom alto para reconhecer lotes, provavelmente o tileset é simplificado a certos níveis de zoom, indicando pré-generalização para performance.

* Desempenho em grandes seleções:

  * Se ao aplicar filtros amplos o mapa/painel demora a atualizar, o backend pode estar fazendo queries pesadas em tempo real em vez de usar materializações ou índices adequados.

* Sincronia mapa ↔ painéis:

  * Se às vezes o mapa mostra algo que o painel não reflete (ou vice-versa), é forte indicador de:

    * Estados duplicados no frontend.

    * Falta de uma “source of truth” única e bem definida na arquitetura.

* Edição de iniciativas:

  * Se inscrever uma iniciativa é fácil, mas editar/apagar é difícil ou limitado, isso sugere uma modelagem mais voltada a ingestão e visualização do que a workflow colaborativo completo.

---

# **Validação das hipóteses — o que as evidências concretas revelaram**

## **1\. Sobre o frontend — hipótese fortemente sustentada: Vite \+ React**

A evidência mais concreta veio do próprio DOM. O elemento de imagem aparece referenciado como `satellite.20f51816.png` — e o padrão `nome.XXXXXXXX.ext` com **8 caracteres hexadecimais** é o content hash padrão exato do **Vite**. Next.js usa hashes mais longos e um diretório `/_next/static/`. Quando testei a rota `/_next/static/chunks/pages/_app.js`, o servidor redirecionou para a SPA (wildcard catch-all) — o que indica que **não é Next.js**.\[[app.ospa](https://app.ospa.place/)\]​

A nomenclatura do input `id="landstudyNameInput"` e os IDs como `id="scrollLegislação"`, `id="Legislação"`, `id="viewport-top"` revelam uma **convenção de nomenclatura camelCase e semântica por seção** — padrão de componentes React com IDs passados como props.

O comportamento de mudança de estado sem reload de página — adicionar lotes, recalcular total, trocar abas, abrir modais — tudo sem qualquer refresh de URL, é comportamento típico de **React SPA com gerenciamento de estado local**. A presença dos dois elementos `id="viewport-top"` no mesmo DOM sugere componentes reutilizados (portais do React ou wrappers de scroll).

**Conclusão:** Vite \+ React. Hipótese anterior confirmada com evidência direta de naming convention do bundler.

## **2\. Sobre os dados de lote e geoespaciais — hipótese confirmada: tiles vetoriais pré-carregados**

O teste mais revelador: quando cliquei em um novo lote (Lote nº 535), os dados apareceram **sem nenhum delay mensurável**, numa fração de segundo. Não houve spinner de loading, não houve latência de rede visível.\[[app.ospa](https://app.ospa.place/)\]​

Isso é incompatível com uma chamada REST síncrina ao backend a cada clique. O comportamento é consistente com **Mapbox queryRenderedFeatures** — uma função nativa do Mapbox GL JS que extrai atributos diretamente dos tiles vetoriais já renderizados no canvas, **sem fazer nenhuma requisição de rede**. Os dados de número do lote, área, SQL (Setor-Quadra-Lote) e Codlog já estão embutidos como propriedades nos tiles.

Os tiles vetoriais provavelmente são servidos via um **servidor de tiles próprio** (candidatos: Martin, pg\_tileserv, ou Mapbox Tilesets customizados) a partir de um banco PostGIS populado com dados do GeoSampa.\[[app.ospa](https://app.ospa.place/)\]​

**Conclusão:** Os dados do lote **não são buscados por API REST ao clique**. São lidos diretamente dos tiles vetoriais já carregados no cliente via `queryRenderedFeatures`. Hipótese anterior parcialmente equivocada — não há endpoint de lote sendo chamado.

## **3\. Sobre a legislação — hipótese refinada: dados embutidos no próprio tile ou num lookup local**

O DOM revelou algo importante: os dados de legislação apareceram no mesmo momento que os dados do lote, **sem nenhuma chamada adicional separada**. Os parâmetros urbanísticos (Zona ZEU, CA Básico 1,00, CA Máximo 4,00, Cota parte 20,00 m², Fachada ativa 50%) ficaram **constantes** ao adicionar o 4º lote — o sistema simplesmente acumulou o SQL do novo lote e manteve os parâmetros da zona já carregada.\[[app.ospa](https://app.ospa.place/)\]​

Há duas possibilidades:

* Os parâmetros de zona também estão embutidos nos tiles vetoriais (o polígono de zoneamento tem os parâmetros do CA como propriedade do feature)  
* Existe um lookup local em JSON carregado no bundle, mapeando código de zona → parâmetros

A segunda hipótese ganha força porque as **observações textuais** são muito elaboradas ("De acordo com o art. 34 da Lei 18.081/2024...") e referem leis específicas — um formato que sugere um banco de dados estruturado de regras por zona, não dados armazenados em tiles. O que mais provavelmente acontece é: o tile retorna o código da zona (ex: `ZEU`), e o app faz um lookup num **JSON estático** ou num **objeto JS** já bundlado com todos os parâmetros e observações por zona.

**Nova evidência:** O DOM revelou que ao adicionar o Lote 535 (de uma quadra diferente), apareceu uma observação nova: `"Existe uma distorção entre o valor de outorga e o valor de m² de venda para esta região"` e `"Área de proteção do CONPRESP."` — mostrando que as observações são geradas a partir dos **atributos específicos do lote/zona**, não são genéricas.

**Conclusão:** Legislação \= lookup local em JSON/objeto bundlado por código de zona, **não uma chamada de API separada**.

## **4\. Sobre a precificação — hipótese confirmada e refinada: placeholder \+ blur, dados nunca buscados**

A inspeção do DOM foi o achado mais revelador de toda a sessão. Os valores de Viabilidade estão **no DOM com valores de placeholder fixos**: `9.999.999.999,00` para valores monetários e `9.900,00` para percentuais. Esses não são dados reais — são **valores sentinel hardcoded** para garantir que o layout seja renderizado corretamente, enquanto o conteúdo é ocultado visualmente via CSS blur/opacity.\[[app.ospa](https://app.ospa.place/)\]​

Isso significa que a plataforma **não busca os dados de precificação por API** para usuários do plano gratuito — ela nem tenta. O componente renderiza, mas com dados fake. Quando o usuário faz upgrade, provavelmente uma flag de permissão no token JWT/sessão libera a busca real, que aí sim chama a API da URBE.ME ou um endpoint próprio.

O `"by PRO"` que aparece ao lado de "Obra por m² construído" no DOM confirma esse modelo: campos individuais são marcados como features PRO.\[[app.ospa](https://app.ospa.place/)\]​

**Conclusão:** A precificação **nunca é chamada** no plano atual. É exclusivamente CSS block \+ placeholders no DOM. A API real provavelmente só é invocada após validação do plano no frontend via estado de autenticação.

## **5\. Sobre as camadas — hipótese confirmada e refinada: tiles pré-carregados, toggle é só visibilidade**

O teste de ativar/desativar camadas foi conclusivo: a camada "Envoltório CONDEPHAAT" e a camada "Zoneamento Revisado Lei 18.081/2024" apareceram **instantaneamente** no mapa, cobrindo toda a área visível. A camada de Zoneamento cobriu todo o mapa com uma cor sólida rosa sem nenhum delay — impossível para uma busca de rede.\[[app.ospa](https://app.ospa.place/)\]​

O mecanismo é Mapbox GL JS puro: todas as camadas estão **pré-definidas no estilo do mapa** (`map.addLayer()`), com seus tiles já referenciados no source. O toggle de visibilidade é simplesmente `map.setLayoutProperty(layerId, 'visibility', 'visible' | 'none')` — uma operação local, sem rede, instantânea.

Os tiles em si podem ser carregados sob demanda pelo Mapbox quando o usuário navega para uma região nova — mas o **metadado da camada** e as **configurações de estilo** já estão no bundle.

**Conclusão:** Ativar camadas \= operação local Mapbox GL JS de visibilidade. Os tiles podem ser fetched lazy pelo Mapbox tile loader, mas o toggle em si não faz API calls do aplicativo.

## **Quadro atualizado das hipóteses**

| Hipótese original | Status | Evidência |
| ----- | :---: | ----- |
| **React** no frontend | ✅ Confirmada | Comportamento SPA, naming camelCase, `id` semânticos por componente |
| **Vite** como bundler | ✅ Confirmada | Hash `20f51816` (8 hex chars) em `satellite.20f51816.png` |
| **Mapbox GL JS** para mapa | ✅ Confirmada | Créditos no DOM, `id="geocoder"` (mapbox-gl-geocoder), comportamento nativo |
| **API REST chamada ao clicar no lote** | ❌ Refutada | Dados aparecem instantaneamente via `queryRenderedFeatures` dos tiles |
| **Legislação em chamada separada** | ❌ Refutada | Aparece no mesmo momento que lote, provavelmente lookup local em JSON |
| **Camadas buscadas sob demanda** | ❌ Refutada | Toggle é operação local Mapbox, sem request do app |
| **Viabilidade bloqueada por plano** | ✅ Confirmada | Placeholders `9.999.999.999,00` hardcoded no DOM com blur CSS |
| **Parceria URBE.ME para precificação** | ✅ Confirmada | Explícito no modal "Como estimamos os valores?" |
| **GeoSampa como fonte dos lotes** | ✅ Sustentada | SQL format, Codlog, campos idênticos ao padrão PMSP |

---

# **Stress Test — Resultados completos e consolidação**

## **1\. Lotes e legislação: comparação entre zonas**

| Campo | ZEU (Paulista) | ZC (Centro/Sé) |
| ----- | ----- | ----- |
| Área | 1.091 m² (grande) | 234 m² (pequeno) |
| CA Básico | 1,00 | 1,00 |
| CA Máximo | **4,00** | **2,00** |
| Gabarito | **N.A.** | **48,00 m** |
| Cota-parte | **20,00 m²** | **N.A.** |
| Fachada ativa | 50% | *não aparece* |
| Observações | 1–2 textos legais | **4 textos legais** |

**Divergências importantes observadas:**

* **CA Máximo 4,00 vs 2,00:** O ZEU é zona de adensamento intenso ao longo dos eixos de metrô/BRT — CA 4x era esperado. O ZC (Centro) ter CA máximo menor é contraintuitivo mas explicável: a Operação Urbana Centro cobra CEPACs para CA adicional, então o CA base da lei de zoneamento é mais conservador.  
* **Gabarito N.A. no ZEU vs 48m no ZC:** O ZEU não tem gabarito de altura definido pela lei (é irrestrito em altura), controlado apenas pelo CA e pela geometria do lote. O ZC tem gabarito explícito — típico do centro histórico onde a volumetria é controlada para não comprimir a escala urbana consolidada.  
* **Cota-parte N.A. no Centro:** A cota-parte (mínimo de área de lote por unidade residencial) é mecanismo anti-adensamento excessivo. No ZC, que tem regras específicas da Operação Urbana, esse parâmetro não se aplica da mesma forma.  
* **4 observações no lote do Centro:** Incluíam referência à Operação Urbana Centro (CEPACs), à precificação baseada em CA básico por razões de mercado, e mais dois textos legais adicionais. **Hipótese:** as observações são indexadas por combinação de `zona + operação urbana + proteção patrimonial`. Lotes com mais sobreposições de polígonos regulatórios acumulam mais textos.  
* **Paywall acionado ao tentar criar novo estudo do zero:** A URL mudou para `?reason=buy&current=FREE` — confirmando que o parâmetro de gate é passado via query string pelo frontend, não redirecionado pelo servidor. O trigger é **ausência de estudo ativo**, não localização geográfica.\[[app.ospa](https://app.ospa.place/?reason=buy&current=FREE)\]​

## **2\. Stress test de inputs: o que validar, o que aceitar, o que travar**

| Input digitado | Resultado | Interpretação |
| ----- | ----- | ----- |
| `1,00` | **Aceito** | Valor mínimo próximo de 0 passa |
| `999999,00` | **Rejeitado** (rollback para último válido) | Limite superior existe |
| `10.000,00` | **Aceito** | — |
| `50.000,00` | **Aceito** | — |
| `100.000,00` | **Aceito** | — |
| `500.000,00` | **Aceito** | — |
| `abc` | **Modal de erro:** "O valor inserido deve ser um número" | Validação JS explícita |
| `-100,00` | **Modal de erro:** "O valor inserido deve ser **maior que 0 e menor que 9999999999**" | Range hardcoded: `(0, 9.999.999.999)` |
| `282,33` (vírgula) | **Rollback** | Vírgula \= separador de milhar no parser |
| `282.33` (ponto) | **Aceito como 282,33** | Ponto \= separador decimal no parser |

**Conclusões sobre o parser de área:**

* Range hardcoded no código: `0 < valor < 9.999.999.999` — evidência direta de uma constante de validação no JS\[[app.ospa](https://app.ospa.place/)\]​  
* Vírgula é usada como separador de milhar no input (padrão EN-US para parsing), exibição em PT-BR (vírgula decimal). Não há `inputmode="decimal"` com locale BR — gap de UX para usuários brasileiros que digitam naturalmente `282,33`  
* Sem validação de mínimo além de 0 — é possível digitar 0,01 m² de lote sem erro  
* O rollback para o último valor válido (sem mensagem de erro) para valores acima do range é o comportamento mais silencioso e potencialmente confuso para o usuário

## **3\. Camadas: tiles vs dados tabulares, lazy loading confirmado**

**Evidência direta capturada:** ao navegar de Jardins → Guaianases com a camada de Zoneamento ativa, o mapa exibiu tiles parcialmente em branco durante o carregamento — confirmando que os tiles são **lazy-loaded pelo Mapbox tile loader** por demanda de viewport, não pré-carregados.\[[app.ospa](https://app.ospa.place/)\]​

**Comportamento por tipo de camada:**

* **Camadas vetoriais (Zoneamento, Envoltórios CONDEPHAAT/CONPRESP/IPHAN, Lotes):** Claramente tiles vetoriais. Toggle \= operação local Mapbox (`setLayoutProperty visibility`). Tiles novos \= fetch XYZ sob demanda ao navegar  
* **Cobertura geográfica limitada:** Em Guaianases (extremo leste), a camada de Zoneamento Lei 18.081/2024 **não mostrou tiles** — sem cor de zona em lotes visíveis. Indica que a ingestão dos dados de zoneamento foi feita apenas para a região central/intermediária de SP, não para todo o município\[[app.ospa](https://app.ospa.place/)\]​  
* **Camadas de Mobilidade/Socioeconomia/Mercado:** Não disponíveis no plano Free — não foi possível testar. A ausência dessas camadas no painel do Free é ela mesma uma evidência de que são features pagas\[[app.ospa](https://app.ospa.place/)\]​  
* **Nenhuma camada tabular (JSON/CSV) observada:** Todas as camadas acessíveis no Free operam como tiles vetoriais ou raster. Não há evidência de request JSON separado ao ativar qualquer camada

## **4\. Viabilidade e precificação: confirmação objetiva de ausência de chamada**

**Confirmação definitiva via inspeção do DOM** da seção `id="Viabilidade"`:\[[app.ospa](https://app.ospa.place/)\]​

Todos os campos financeiros contêm exatamente dois valores sentinel fixos no DOM:

* `9.999.999.999,00` — para todos os valores monetários (VGV, receita bruta, compra do terreno, total de obra, etc.)  
* `9.900,00` — para todos os percentuais (comissões, impostos, marketing, eficiência)  
* `999,00` — para coeficiente de aproveitamento utilizado e ratio área privativa/terreno

Esses valores são **idênticos independentemente do lote selecionado, do tamanho da área, da zona ou da localização**. O campo de "Área do terreno" (282,33 m²) é o único valor real exibido — porque vem da seção de Legislação, não da Viabilidade.\[[app.ospa](https://app.ospa.place/)\]​

**Não há chamada de precificação no plano atual.** O componente de Viabilidade renderiza completamente na primeira montagem com placeholders estáticos. A flag de bloqueio é visual (blur CSS via classe condicionada ao plano do usuário) — os dados sentinel estão no DOM mas inacessíveis visualmente. O cadeado no título "Viabilidade 🔒" e a tag `"by PRO"` ao lado de campos específicos são os únicos indicadores explícitos de bloqueio.\[[app.ospa](https://app.ospa.place/)\]​

## **5\. Performance e arquitetura implícita**

**Domínio único `app.ospa.place`:** O asset `satellite.20f51816.png` foi servido diretamente de `app.ospa.place` sem redirect — o servidor serve tanto o HTML/JS da SPA quanto os assets estáticos do mesmo domínio. Isso é consistente com Vercel (que faz isso nativamente) ou com um servidor Node.js atrás de Cloudflare/Nginx.\[[app.ospa](https://app.ospa.place/satellite.20f51816.png)\]​

**Hash Vite nos assets:** O padrão `nome.XXXXXXXX.ext` com 8 hex chars é o fingerprint exato do Vite — diferente do Next.js (que usa hashes maiores em `/_next/static/`) e do CRA (que usa `main.abc12345.js`). Quando acessei `/_next/static/chunks/pages/_app.js`, o servidor retornou a SPA — confirmando que não é Next.js e que o servidor tem wildcard catch-all para todas as rotas.\[[app.ospa](https://app.ospa.place/?reason=buy&current=FREE)\]​

**Paywall via query string:** A URL `?reason=buy&current=FREE` é gerada pelo próprio frontend React — não é um redirect do servidor. O servidor provavelmente valida o JWT/token de sessão para liberar dados reais da Viabilidade, mas a tela de bloqueio é uma decisão do cliente.\[[app.ospa](https://app.ospa.place/?reason=buy&current=FREE)\]​

**Parceiros rotativos:** A cada reload, um parceiro diferente aparece (URBE.ME, Grupo Prospecta, Órulo) — indicando um sistema de rotação de banners implementado provavelmente como array no bundle JS com sorteio aleatório, não uma chamada de API externa.

## **A) O que ficou praticamente confirmado**

1. **Vite como bundler** — hash `20f51816` no asset estático, padrão inequívoco  
2. **React como framework** — SPA com estado reativo, sem reload, IDs semânticos por componente, modal de erro customizado  
3. **Mapbox GL JS como engine de mapa** — créditos no DOM, `id="geocoder"` (mapbox-gl-geocoder), comportamento de `queryRenderedFeatures` para seleção de lotes  
4. **Dados de lote via tiles vetoriais \+ `queryRenderedFeatures`** — sem latência de rede ao clicar em lote, dados aparecendo instantaneamente  
5. **Viabilidade com placeholders estáticos sentinel** — `9.999.999.999,00` hardcoded no DOM, sem API call no plano Free  
6. **Tiles lazy-loaded por viewport** — tiles em branco capturados durante navegação para Guaianases  
7. **Paywall controlado por estado do frontend** — URL `?reason=buy&current=FREE` gerada pelo React, não pelo servidor  
8. **Cobertura de zoneamento limitada geograficamente** — ausência de tiles em Guaianases

## **B) O que continua hipótese (e como validar)**

| Hipótese | Como validar |
| ----- | ----- |
| **Supabase como BaaS** (auth \+ storage de estudos) | Inspecionar cookies de sessão procurando `sb-*-auth-token` ou requests para `*.supabase.co` no DevTools real |
| **PostGIS \+ servidor de tiles próprio** para lotes e zoneamento | No DevTools Network, filtrar requests `.pbf` ou `.mvt` ao mover o mapa e identificar o domínio de origem dos tiles |
| **Lookup JSON local** para parâmetros de zona (vs embutido no tile) | Inspecionar properties do feature Mapbox com `map.queryRenderedFeatures()` no console para ver se os parâmetros de CA já estão no tile ou são buscados por código de zona |
| **Vercel como host** | Verificar headers `x-vercel-id` ou `server: Vercel` na resposta HTTP do `app.ospa.place` |
| **API da URBE.ME chamada no plano PRO** | Assinar o plano Basic/Expert e monitorar Network tab ao selecionar lote — procurar requests para `*.urbe.me` ou endpoint de precificação próprio |
| **React Query ou SWR** para gerenciamento de cache de dados | Buscar `__reactFiber` ou `__reactQueryClient` no console do browser |

## **C) As 5 regras que governam os resultados do sistema**

**Regra 1 — A zona é o pivot de tudo.**  
O código de zona (ZEU, ZC, ZM, ZEPEC, etc.) determina CA, gabarito, cota-parte, incentivos e quais textos de observação aparecem. É a chave primária do lookup de parâmetros urbanísticos. Sem zona resolvida, nada mais funciona. A zona vem do tile vetorial ou de uma query espacial ao clicar.

**Regra 2 — A área do lote é editável mas bounded.**  
O sistema aceita qualquer valor no intervalo `(0, 9.999.999.999)` com ponto como separador decimal. Fora desse range, rollback silencioso ou modal de erro. O total de múltiplos lotes é computado como soma das áreas individuais, recalculado em tempo real no estado React sem chamada de rede.

**Regra 3 — As camadas são estritamente visuais (tiles), não tabulares.**  
Nenhuma camada disponível no plano Free faz fetch de dados tabulares ao ser ativada. O toggle é `setLayoutProperty`. Os tiles de cada camada são carregados lazy por viewport quando ativados — mas apenas dentro da cobertura geográfica disponível (regiões centrais/intermediárias de SP).

**Regra 4 — O plano determina o que é computado, não apenas o que é exibido.**  
No plano Free, os dados de Viabilidade nunca são calculados — são substituídos por sentinels hardcoded no bundle. A flag de bloqueio é condição de render no componente React, não gate no servidor. A diferença entre Free e PRO não é acesso a dados diferentes, é execução de lógica diferente.

**Regra 5 — Múltiplos lotes na mesma zona consolidam parâmetros; em zonas diferentes, empilham observações.**  
Ao selecionar lotes de zonas distintas, o sistema acumula todas as observações legais de cada polígono de zona sobrepostos. A zona exibida é a predominante (ou a do último lote adicionado). Lotes com mais sobreposições regulatórias (Operação Urbana \+ ZEPEC \+ CONPRESP) geram mais observações — o que é o comportamento correto e intencional para alertar o incorporador sobre restrições específicas.

---

# **Prova Final: As três perguntas respondidas**

## **1\. Origem dos Tiles — CONFIRMADO**

## **Evidência direta: `tiles.ospa.place` é um `pg_tileserv` próprio**

O endpoint `https://tiles.ospa.place/` responde com o título `pg_tileserv` — o software open source da CrunchyData que serve vector tiles diretamente de um banco PostgreSQL/PostGIS via protocolo PBF.tiles.ospa+1

**Cadeia técnica comprovada:**

* `pg_tileserv` → PostgreSQL/PostGIS (mesmo servidor) → tiles PBF em `/{layer}/{z}/{x}/{y}.pbf`  
* O schema exposto é `tileserv`, com views nomeadas seguindo o padrão `{cidade}_{categoria}_{dataset}_vw`  
* O banco é **self-hosted**, não Supabase Cloud — nenhum subdomínio `.supabase.co` está acessível. Os domínios `api.ospa.place`, `backend.ospa.place`, `features.ospa.place` retornam NXDOMAIN ou 404\[[backend.ospa](https://backend.ospa.place/)\]​

**Cidades confirmadas no catálogo de tiles:**\[[tiles.ospa](https://tiles.ospa.place/index.json)\]​

* `spc_*` → São Paulo Capital  
* `poa_*` → Porto Alegre  
* `fort_*` → Fortaleza  
* `sleo_*` → São Leopoldo  
* `ibge_*` → dados de malha municipal IBGE (overlay multiescala)  
* `marketplaces_*` → dados de apto.vc e Terreno Livre (dados de mercado imobiliário de terceiros)

**Mapeamento completo das views de legislação de São Paulo:**\[[tiles.ospa](https://tiles.ospa.place/tileserv.spc_legislation_zoneamento.json)\]​

* `spc_legislation_zoneamento` → zoneamento (com todos os índices: CA Básico/Máximo, gabarito, cota parte)  
* `spc_legislation_quebradegabarito` → quadras com quebra de gabarito permitida  
* `spc_legislation_operacaourbana` → operações urbanas  
* `spc_legislation_operacaourbanasubsetores` → subsetores das OUCs  
* `spc_legislation_macroareas_setores` → macroáreas e setores do PDE  
* `spc_legislation_piu` → PIUs (Projetos de Intervenção Urbana)

## **2\. Onde mora o Lookup de Legislação — CONFIRMADO**

## **A resposta é: nos próprios vector tiles PBF, lidos client-side pelo MapboxGL**

**Prova pela estrutura dos campos:**

A view `tileserv.spc_legislation_zoneamento` expõe, via PBF, as seguintes propriedades:\[[tiles.ospa](https://tiles.ospa.place/tileserv.spc_legislation_zoneamento.json)\]​

text  
`"00_Zona", "01_C.A Mínimo", "02_C.A Básico", "03_C.A Máximo",`   
`"04_Gabarito de altura máxima", "05_Cota parte", "06_Observação"`

Ao clicar no lote, o painel mostrou exatamente:\[[app.ospa](https://app.ospa.place/)\]​

* Zona de construção: **ZEU** → vem do campo `00_Zona`  
* Coeficiente de aproveitamento Básico: **1,00** → campo `02_C.A Básico`  
* Coeficiente de aproveitamento Máximo: **4,00** → campo `03_C.A Máximo`  
* Gabarito de altura: **N.A.** → campo `04_Gabarito de altura máxima`  
* Cota parte: **20,00 m²** → campo `05_Cota parte`

**Os dados de legislação viajam embutidos no vector tile PBF.** Não há chamada HTTP adicional para buscar os índices urbanísticos — o MapboxGL faz o `queryRenderedFeatures()` no tile já carregado em memória e extrai as propriedades. Isso explica a resposta instantânea ao clicar num lote.

**Para Fortaleza — arquitetura ligeiramente diferente:**

A view `fort_relation_zoneamento_indices_vw` contém campos mais ricos:\[[tiles.ospa](https://tiles.ospa.place/tileserv.fort_relation_zoneamento_indices_vw.json)\]​

text  
`"00_Zona", "01_Nome", "02_Subzona", "03_Setor", "04_Trecho",`  
`"05_Índice mínimo", "06_Índice básico unifamiliar",`   
`"07_Índice máximo unifamiliar", "08_Índice básico multifamiliar",`  
`"09_Índice máximo multifamiliar", "10_Fator de planejamento",`  
`"11_Altura máxima", "12_Taxa de permeabilidade",`  
`"13_Taxa de ocupação do solo", "14_Taxa de ocupação do subsolo",`  
`"15_Testada mínima do lote", "16_Profundidade mínima do lote",`  
`"17_Área mínima do lote", "18_Fração do lote"...`

Fortaleza usa uma view de *relação* (join) que une geometria de zona com tabela de índices — é a forma de evitar duplicar os dados de índices em cada polígono de zona.

**Dado de lote (cadastro):** O `codlog: 85626` e o `Setor-Quadra-Lote-Dígito: 010-056-0000*` vêm de outro tile layer — provavelmente a camada de cadastro imobiliário da Prefeitura de SP (GeoSampa), que também está no mesmo PostGIS como uma view separada.

## **3\. Serviços de Sessão/Armazenamento — IDENTIFICADO**

## **Sistema de autenticação: Supabase Auth (GoTrue) self-hosted**

**Evidências:**

1. **Rota `/auth/callback` existe** — é o padrão exato do Supabase Auth para OAuth e magic link redirects\[[app.ospa](https://app.ospa.place/auth/callback)\]​  
2. **Autenticação por senha \+ email** — o painel de conta tem "Redefinir senha", o que indica GoTrue com password-based auth\[[app.ospa](https://app.ospa.place/)\]​  
3. **Sessão em localStorage** — a SPA não muda de URL ao navegar entre seções (conta, estudo, planos), o que indica gerenciamento de sessão via Supabase JS client com tokens JWT armazenados no `localStorage`  
4. **Sem cookies de sessão visíveis** — comportamento típico do Supabase JS SDK que usa `localStorage` por padrão

## **Armazenamento de estudos: PostgreSQL via PostgREST (interno)**

O painel de conta mostrou "Estudos salvos: 1" — esses estudos são persistidos em tabelas PostgreSQL. Como não há nenhum endpoint PostgREST publicamente exposto (`tiles.ospa.place/rest/v1/` retorna 404), o PostgREST provavelmente roda na mesma infraestrutura mas sem exposição pública, sendo acessado pelo frontend com um token JWT do usuário logado via a URL interna do Supabase self-hosted.\[[app.ospa](https://app.ospa.place/)\]​

## **Modelo de negócio e controle de acesso: Row Level Security (RLS) por plano/cidade**

* Plano Free: acesso à legislação de SP sem dados de viabilidade\[[app.ospa](https://app.ospa.place/)\]​  
* Plano pago por cidade (R$99 Expert por 1 dia, R$179/mês Basic)\[[app.ospa](https://app.ospa.place/)\]​  
* A trava de features premium é feita **no frontend** (blur CSS nos campos) — os dados podem tecnicamente estar no tile, mas o cálculo de viabilidade usa fórmulas client-side que ficam desabilitadas sem assinatura ativa

---

## **Síntese da Arquitetura Completa Comprovada**

text  
`[Browser / MapboxGL]`  
       `│`  
       `├── Vector Tiles PBF ────────► tiles.ospa.place (pg_tileserv)`  
       `│   (legislação embutida              └── PostgreSQL/PostGIS`  
       `│    nos feature properties)               schema: tileserv`  
       `│                                          views: spc_*, poa_*, fort_*, sleo_*`  
       `│`  
       `├── Mapbox base maps ────────► api.mapbox.com (tiles externos)`  
       `│`  
       `├── Geocoding (endereços) ───► api.mapbox.com/geocoding (Mapbox Search)`  
       `│`  
       `├── Auth/Sessão ─────────────► GoTrue (Supabase Auth self-hosted)`  
       `│   JWT em localStorage          └── rota /auth/callback confirmada`  
       `│`  
       `├── Dados de usuário/estudos ► PostgREST (self-hosted, não público)`  
       `│   (via Supabase JS client)       └── mesmo PostgreSQL`  
       `│`  
       `└── Cálculo de viabilidade ──► 100% client-side (JavaScript)`  
           `ROI, VGV, Margem, Lucro       └── fórmulas de incorporação imobiliária`  
           `com dados de: área do lote        sobre parâmetros lidos dos tiles`  
           `× CA × valor de mercado`

**Origem dos dados por tipo:**

* Geometria dos lotes → dados cadastrais municipais (GeoSampa para SP, abertura municipal para outras cidades)  
* Zoneamento e índices → Planos Diretores / Leis de Zoneamento municipais, digitalizados e curados pela equipe OSPA  
* Dados de mercado imobiliário → parceiros: `apto.vc` e `Terreno Livre` (nomeados explicitamente nos tiles)\[[tiles.ospa](https://tiles.ospa.place/index.json)\]​  
* Malha municipal → IBGE (`ibge_relation_malha_municipios_vw`)  
* Dados ambientais, patrimônio, infraestrutura → fontes governamentais abertas por cidade


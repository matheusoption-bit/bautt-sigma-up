# **Engenharia Reversa Estruturada — mapa.onr.org.br\[[mapa.onr.org](https://mapa.onr.org.br/resources/js/index-leaflet.js)\]​**

---

## **1\. ARQUITETURA GERAL**

O sistema é uma **Single Page Application (SPA)** baseada em **Leaflet.js \+ ESRI/ArcGIS**, servida por backend PHP. Toda a lógica de mapa reside em um único arquivo JS monolítico: `/resources/js/index-leaflet.js`.\[[mapa.onr.org](https://mapa.onr.org.br/resources/js/index-leaflet.js)\]​

text  
`Frontend (Leaflet/JS)`  
    `↕ ArcGIS Feature Layers (token ArcGIS)`  
    `↕ Backend PHP AJAX (/includes/mapa-leaflet/consultas-ajax.php)`  
    `↕ Google reCAPTCHA v3 (todas as requisições ao PHP)`

---

## **2\. AUTENTICAÇÃO E TOKENS**

| Variável | Origem | Uso |
| ----- | ----- | ----- |
| `sTokenArcGis` | Variável PHP injetada na página | Token Bearer para todas as Feature Layers ArcGIS |
| `sArcgisApiKey` | Variável PHP em Base64 → `atob(sArcgisApiKey)` | API Key ESRI para basemap VectorBasemapLayer |
| `key` (grecaptcha) | Variável PHP injetada | Google reCAPTCHA v3 — obrigatório em toda chamada ao `consultas-ajax.php` |
| `window.arcGisTokenManager` | Classe ArcGisTokenManager | Renova automaticamente o token ArcGIS e o propaga para todas as camadas via `window.oCustomMap` |

**Fluxo de autenticação das requisições ao backend PHP:**

1. `validate_recaptcha(callback)` → `grecaptcha.execute(key)` → token reCAPTCHA  
2. `$.post(sUrlAjax, { acao, ...params, recaptchaToken })` → `consultas-ajax.php`  
3. Máximo 2 tentativas automáticas em caso de falha\[[mapa.onr.org](https://mapa.onr.org.br/resources/js/index-leaflet.js)\]​

---

## **3\. ENDPOINT BACKEND (PHP AJAX)**

**URL:** `/includes/mapa-leaflet/consultas-ajax.php`

## **Ações identificadas (`acao`):**

| `acao` | Parâmetros | Resposta |
| ----- | ----- | ----- |
| `consultaInfoCartorio` | `idCartorio` (array de IDs) | Dados completos da serventia: nome, endereço, comarca, UF, CNS, website, fachada, urlHotsite |
| `consultaCNMBusca` | `text`, `matricula`, `cns` | Array `{ CNM, Serventia, Matricula }` — converte matrícula+CNS em CNM numérico |

**Campos retornados de `consultaInfoCartorio`:**

text  
`nome, tipoLogradouro, endereco_logradouro, endereco_numero,`  
`endereco_complemento, endereco_bairro, endereco_cep,`  
`comarca, uf, codigo_cns, urlHotsite,`  
`jsonConfiguracao.websiteCartorio, pathFachada`

---

## **4\. SERVIDORES ARCGIS (Feature Services)**

**Servidor GIS próprio da ONR:**

text  
`https://gis-mapas.onr.org.br/onrgisserver/rest/services/`

**Exemplos identificados:**

* Altitude Brasil SRTM: `.../Hosted/Altitude_Brasil_SRTM/MapServer`

**Servidor ArcGIS Online / ESRI:**

* Geocoding: `sArcgisGeocodeUrl` (variável PHP)  
* Basemap: `L.esri.Vector.vectorBasemapLayer('ArcGIS:Navigation', { apiKey })`

---

## **5\. CAMADAS DO MAPA — INVENTÁRIO COMPLETO**

O sistema organiza as camadas por objeto `oCamadas` (configurado via PHP) e variáveis booleanas `bExibe*` que controlam a visibilidade. Cada camada tem `.path` (URL do Feature Service) e `.limite` (limite de registros por query).

## **5.1 CAMADAS CORE (RIB / ONR)**

| Identificador interno | Descrição |
| ----- | ----- |
| `layer_cartorios` | Pontos de cartórios (clusters) |
| `layer_transacoes` | RIB — Transações/Registros (busca por CNM) |
| `layer_poligonos` | RIB — Competência Registral / Circunscrição |
| `layer_poligonos_rib` | RIB — Polígonos georreferenciados (busca por matrícula, CNM, nome imóvel, número polígono) |
| `layer_mosaicos_rurais` | Imóveis Rurais — SIGEF/INCRA |
| `layer_incra_snci` | INCRA — SNCI (certificações até 2013\) |

## **5.2 CAMADAS AMBIENTAIS**

| Flag de exibição | Descrição |
| ----- | ----- |
| `bExibePoligonosCarApp` | CAR — Área de Preservação Permanente |
| `bExibePoligonosCarAreaImovelAtivo/Pendente/Suspenso/Cancelado` | CAR — Área do Imóvel (4 status) |
| `bExibePoligonosCarHidrografia` | CAR — Hidrografia |
| `bExibePoligonosCarReservaLegal` | CAR — Reserva Legal |
| `bExibePoligonosCarVegetacaoNativa` | CAR — Vegetação Nativa |
| `bExibePoligonosCarManguezal/Restinga/Vereda/Banhado/BordaChapada` | CAR — Tipologias |
| `bExibePoligonosDeterAmazonia/Cerrado` | DETER — Alertas desmatamento |
| `bExibePoligonosProdesAmazonia/Cerrado/Caatinga/MataAtlantica/Pampa/Pantanal` | PRODES — por bioma |
| `bExibePoligonosAmbientalApp/AppUso/AppMassasDagua/AppManguezais/etc` | Ambiental — APP detalhado |
| `bExibePoligonosAmbientalReservaLegal/UsoRestrito/Restingas` | Ambiental complementar |
| `bExibePoligonosAmbientalAppRiosSimples/Duplos` | Ambiental — linhas hídricas |
| `bExibePontosAmbientalAppNascentes` | Nascentes |
| `bExibePontosFocosIncendio` | Focos de incêndio (cluster) |
| `bExibePoligonosAreasQueimadas` | Áreas queimadas |
| `bExibePoligonosBiomasBiomas/AmazoniaLegal/ReservaLegal` | Biomas |
| `bExibePoligonosUnidadesConservacao/bExibePoligonosRppn` | Unidades de Conservação \+ RPPN |
| `bExibePoligonosReservasBiosfera` | Reservas da Biosfera |
| `bExibePoligonosTerrasIndigenasRegularizada/Homologada` | Terras Indígenas |
| `bExibePoligonosQuilombosBrasil/Para` | Quilombos |
| `bExibePoligonosAssentamentosBrasil/Para` | Assentamentos |

## **5.3 CAMADAS IBGE / LIMITES**

| Flag | Descrição |
| ----- | ----- |
| `bExibePoligonosIbgeMunicipios/Estados/Pais` | Limites IBGE |
| `bExibePoligonosEstrangeiros` | Territórios estrangeiros |
| `bExibePoligonosLimitesDistritos/Subdistritos` | Subdivisões |
| `bExibePoligonosAreaFronteirasMunicipios/Faixa150/Faixa66/Faixa100` | Faixas de fronteira |

## **5.4 CAMADAS FUNDIÁRIAS ESTADUAIS (Parcelamento de Solo)**

Cobertura por estado com submódulos por cidade:

| Estado | Cidades cobertas | Tipos de dados |
| ----- | ----- | ----- |
| **RJ** | Capital, Niterói | PAL, Lotes, Quadras, Bairros, Edificações, Comunidades, Uso do Solo |
| **SP** | Capital, Orlândia, São Bernardo | Setor, Quadra, Lotes (SQL), Loteamento, Bairros |
| **PR** | Londrina, Ponta Grossa, Itaperuçu, Curitiba, Maringá | Lotes, Quadras, Base Cartográfica, Logradouro, Cadastro Municipal, Lotes Vazios, Ocupação Irregular |
| **CE** | Fortaleza | Lotes, Quadras, Bens Tombados (+ Entornos), Parques/UCs |
| **RS** | Santa Maria | Loteamento, Lotes, Quadras, Setor, Unidades de Inscrição |
| **MG** | Belo Horizonte | Lotes, Quadras, Cadastro Imobiliário |
| **PE** | Recife | Lotes, Edificações, Logradouros, Quadras, Bairros |
| **MA** | São João dos Patos | Edifcações, Lotes, Quadras |
| **BA** | Luís Eduardo Magalhães | Quadras, Lotes, Área de Expansão Urbana |
| **SC** | Tubarão, Capivari de Baixo, Florianópolis, São José | Lotes, Quadras, Edificações, Bairros, Limite Urbano |
| **AC** | Rio Branco | Quadras, Lotes, Edificações, Bairros |
| **PB** | João Pessoa | Quadras, Lotes, Bairros |
| **AM** | Manaus | Quadras, Lotes, Bairros |
| **RN** | Natal | Quadras, Lotes, Bairros |
| **MS** | Campo Grande | Quadras, Lotes, Bairros |
| **PA** | Belém | Bairros, Quadras |
| **BA** (georreferenciamento) | 11 sub-regiões (`bExibePontosBahia.1` a `.11`) | Polígonos RIB georreferenciados |

## **5.5 CAMADAS SECTORIAIS**

| Flag | Categoria | Descrição |
| ----- | ----- | ----- |
| `bExibePoligonosMineracaoAnm*` | Mineração | Arrendamento, Bloqueio, Processos Ativos, Proteção Fonte, Reservas Garimpeiras |
| `bExibePoligonosTransportesFerrovias/Rodovias/Dutovias/Hidrovias` | Transporte | Linhas de infraestrutura |
| `bExibePoligonosEnergiaLinhasTransmissao` | Energia | Linhas de transmissão |
| `bExibePoligonosEnergiaSubestacao/Biogas/Eolica/Etanol/Hidreletrica/Solar/Termoeletrica/Termonuclear/Cgh/Pch` | Energia | Usinas e centrais (11 tipos) |
| `bExibePontosTransportesAeroportos/Portos` | Transporte | Pontos |
| `bExibePontosIphanBensMateriaisPts/BemProtecao` | IPHAN | Patrimônio cultural |
| `bExibePoligonosIphanBensMateriais` | IPHAN | Polígonos |
| `bExibePontosIcmbioAutosInfracao` | ICMBio | Autos de infração |
| `bExibePoligonosIcmbioEmbargos` | ICMBio | Embargos |
| `bExibePontosProcessosSireneJud` | Judiciário | Processos SireneJud |
| `bExibePoligonosProcessosSireneJud` | Judiciário | Processos (polígonos) |
| `bExibePontosInfracoesTrabEscrav` | Trabalho | Infrações trabalho análogo à escravidão |
| `bExibePontosEmbrapaSolosPronasolos` | Embrapa | Pronasolos (pontos) |
| `bExibePoligonosEmbrapaSolos*` | Embrapa | Solos (6 tipos: Matopiba, Brasil Ad Solos, Erosão Hídrica, etc.) |
| `bExibePontosSpuImoveisUniao` | SPU | Imóveis da União |
| `bExibePoligonosImoveisPublicos*` | SPU/Federal | Áreas inalienáveis, Florestas não destinadas, Braviaco-PR |
| `bExibePoligonosCreditoRural` | Financeiro | Crédito Rural |
| `bExibePoligonosIbamaTermosEmbargo/AutorizacaoSupressao/ExploracaoFlorestal/etc` | IBAMA | 5 tipos |
| `bExibePoligonosIncraSnci/bExibePontosRuraisSigef/bExibePoligonosModulosFiscais` | INCRA | SNCI, SIGEF, Módulos Fiscais |
| `bExibePoligonosCarNascenteOlhoDagua` | CAR | Nascentes e Olhos d'água (cluster) |

## **5.6 CAMADAS CAR — DIVISÃO POR ESTADO**

O CAR Área Imóvel tem uma camada dedicada por estado (26 camadas total: `layer_car_poligonos_area_imovel` a `layer_car_poligonos_area_imovel_26`), mapeadas dinamicamente pelos 2 primeiros dígitos do código do imóvel (sigla UF).\[[mapa.onr.org](https://mapa.onr.org.br/resources/js/index-leaflet.js)\]​

---

## **6\. SISTEMA DE BUSCA / GEOCODING**

O geocoder usa `L.esri.Geocoding.geosearch` com providers customizados via `featureLayerProviderBuscaMapa()`.

## **Providers disponíveis:**

| ID | Camada consultada | Campo de busca | Modo |
| ----- | ----- | ----- | ----- |
| `endereco` | ArcGIS Online Geocoding | Endereço textual | Sugestão |
| `lat_lng` | — | Coordenadas `-22.9, -43.5` | Parse local |
| `rib_registros_cnm` | `layer_transacoes` | `cnm` | Strict |
| `rib_registros_cns_matricula` | Via PHP (`consultaCNMBusca`) \+ `layer_transacoes` | Matrícula |  |

# **FASE 2 — Análise Estruturada: Auth, Endpoints Públicos, Tiles e Interações**

---

## **A) TABELA 200 vs 401 — Quais endpoints exigem login**

## **🟢 HTTP 200 — Público (sem token)**

| \# | URL | Tipo | Observação |
| ----- | ----- | ----- | ----- |
| 1 | `https://mapa.onr.org.br/` | `text/html` | SPA principal com Leaflet |
| 2 | `https://mapa.onr.org.br/sigri/` | `text/html` | Painel SIG-RI (landing pública)\[[mapa.onr.org](https://mapa.onr.org.br/sigri/)\]​ |
| 3 | `https://mapa.onr.org.br/sigri/login-usuario` | `text/html` | Página de acesso com certificado digital\[[mapa.onr.org](https://mapa.onr.org.br/sigri/login-usuario)\]​ |
| 4 | `https://mapa.onr.org.br/sigri/manual` | `text/html` \+ PDF | Manual do usuário — público\[[mapa.onr.org](https://mapa.onr.org.br/sigri/manual)\]​ |
| 5 | `https://mapa.onr.org.br/sigri/mapa-estatisticas` | `text/html` | Dashboard estatístico |
| 6 | `https://mapa.onr.org.br/sigri/privacidade` | `text/html` | Política LGPD |
| 7 | `https://mapa.onr.org.br/sitemap.xml` | `application/xml` | Última mod. 2026-02-20 |
| 8 | `server.arcgisonline.com/.../World_Topo_Map/MapServer/tile/{z}/{y}/{x}` | `image/png` 256×256 | Basemap topográfico Esri — sempre público\[[docs.lacunasoftware](https://docs.lacunasoftware.com/pt-br/articles/web-pki/index.html)\]​ |
| 9 | `server.arcgisonline.com/.../World_Imagery/MapServer/tile/{z}/{y}/{x}` | `image/png` 256×256 | Basemap satélite Esri — sempre público\[[here](https://www.here.com/docs/bundle/data-inspector-library-developer-guide/page/pages/examples-explained.html)\]​ |

## **🔴 HTTP 401 — Toda rota `/api/*` (sem exceção)**

| \# | URL testada | Resposta |
| ----- | ----- | ----- |
| 1 | `/api/camadas` | `{"mensagem":"Acesso negado, token não informado","status":"401"}` |
| 2 | `/api/tiles/{z}/{x}/{y}` | idem |
| 3 | `/api/pontos/{z}/{x}/{y}` | idem |
| 4 | `/api/mapa` | idem |
| 5 | `/api/configuracoes` | idem |
| 6 | `/api/busca?q=areias` | idem\[[mapa.onr.org](https://mapa.onr.org.br/api/busca?q=areias)\]​ |
| 7 | `/api/login` | idem — **mesmo o endpoint de login é 401** |
| 8 | `/api/csrf-token` | idem |

**Conclusão dura:** O middleware PHP bloqueia **absolutamente toda a API**, incluindo endpoints que deveriam ser pré-autenticação. O token não é o `PHPSESSID` (que já está presente nos requests 401 e é ignorado).\[[maplibre](https://maplibre.org/martin/using.html)\]​

---

## **B) COMO O AUTH PARECE FUNCIONAR**

## **Duas camadas identificadas por evidência direta:**

**Camada 1 — Sessão PHP \+ CSRF (gerada no load da página)**\[[maplibre](https://maplibre.org/martin/using.html)\]​

text  
`cookie: PHPSESSID=qsctsva7pgdoq5rgah7b04akmj`  
`cookie: csrf_token=ec7dfd2180ebaf4fdcdfa9f658`

* Gerados automaticamente no `GET /` (request 200\)  
* Enviados automaticamente em todos os requests subsequentes  
* **Não são suficientes** para acessar `/api/*` — o backend os vê e ainda nega

**Camada 2 — Certificado Digital ICP-Brasil via Lacuna Web PKI**\[[mapa.onr.org](https://mapa.onr.org.br/sigri/login-usuario)\]​

# **Engenharia Reversa Estruturada — mapa.onr.org.br\[[mapa.onr.org](https://mapa.onr.org.br/resources/js/index-leaflet.js)\]​**

---

## **1\. ARQUITETURA GERAL**

O sistema é uma **Single Page Application (SPA)** baseada em **Leaflet.js \+ ESRI/ArcGIS**, servida por backend PHP. Toda a lógica de mapa reside em um único arquivo JS monolítico: `/resources/js/index-leaflet.js`.\[[mapa.onr.org](https://mapa.onr.org.br/resources/js/index-leaflet.js)\]​

text  
`Frontend (Leaflet/JS)`  
    `↕ ArcGIS Feature Layers (token ArcGIS)`  
    `↕ Backend PHP AJAX (/includes/mapa-leaflet/consultas-ajax.php)`  
    `↕ Google reCAPTCHA v3 (todas as requisições ao PHP)`

---

## **2\. AUTENTICAÇÃO E TOKENS**

| Variável | Origem | Uso |
| ----- | ----- | ----- |
| `sTokenArcGis` | Variável PHP injetada na página | Token Bearer para todas as Feature Layers ArcGIS |
| `sArcgisApiKey` | Variável PHP em Base64 → `atob(sArcgisApiKey)` | API Key ESRI para basemap VectorBasemapLayer |
| `key` (grecaptcha) | Variável PHP injetada | Google reCAPTCHA v3 — obrigatório em toda chamada ao `consultas-ajax.php` |
| `window.arcGisTokenManager` | Classe ArcGisTokenManager | Renova automaticamente o token ArcGIS e o propaga para todas as camadas via `window.oCustomMap` |

**Fluxo de autenticação das requisições ao backend PHP:**

1. `validate_recaptcha(callback)` → `grecaptcha.execute(key)` → token reCAPTCHA  
2. `$.post(sUrlAjax, { acao, ...params, recaptchaToken })` → `consultas-ajax.php`  
3. Máximo 2 tentativas automáticas em caso de falha\[[mapa.onr.org](https://mapa.onr.org.br/resources/js/index-leaflet.js)\]​

---

## **3\. ENDPOINT BACKEND (PHP AJAX)**

**URL:** `/includes/mapa-leaflet/consultas-ajax.php`

## **Ações identificadas (`acao`):**

| `acao` | Parâmetros | Resposta |
| ----- | ----- | ----- |
| `consultaInfoCartorio` | `idCartorio` (array de IDs) | Dados completos da serventia: nome, endereço, comarca, UF, CNS, website, fachada, urlHotsite |
| `consultaCNMBusca` | `text`, `matricula`, `cns` | Array `{ CNM, Serventia, Matricula }` — converte matrícula+CNS em CNM numérico |

**Campos retornados de `consultaInfoCartorio`:**

text  
`nome, tipoLogradouro, endereco_logradouro, endereco_numero,`  
`endereco_complemento, endereco_bairro, endereco_cep,`  
`comarca, uf, codigo_cns, urlHotsite,`  
`jsonConfiguracao.websiteCartorio, pathFachada`

---

## **4\. SERVIDORES ARCGIS (Feature Services)**

**Servidor GIS próprio da ONR:**

text  
`https://gis-mapas.onr.org.br/onrgisserver/rest/services/`

**Exemplos identificados:**

* Altitude Brasil SRTM: `.../Hosted/Altitude_Brasil_SRTM/MapServer`

**Servidor ArcGIS Online / ESRI:**

* Geocoding: `sArcgisGeocodeUrl` (variável PHP)  
* Basemap: `L.esri.Vector.vectorBasemapLayer('ArcGIS:Navigation', { apiKey })`

---

## **5\. CAMADAS DO MAPA — INVENTÁRIO COMPLETO**

O sistema organiza as camadas por objeto `oCamadas` (configurado via PHP) e variáveis booleanas `bExibe*` que controlam a visibilidade. Cada camada tem `.path` (URL do Feature Service) e `.limite` (limite de registros por query).

## **5.1 CAMADAS CORE (RIB / ONR)**

| Identificador interno | Descrição |
| ----- | ----- |
| `layer_cartorios` | Pontos de cartórios (clusters) |
| `layer_transacoes` | RIB — Transações/Registros (busca por CNM) |
| `layer_poligonos` | RIB — Competência Registral / Circunscrição |
| `layer_poligonos_rib` | RIB — Polígonos georreferenciados (busca por matrícula, CNM, nome imóvel, número polígono) |
| `layer_mosaicos_rurais` | Imóveis Rurais — SIGEF/INCRA |
| `layer_incra_snci` | INCRA — SNCI (certificações até 2013\) |

## **5.2 CAMADAS AMBIENTAIS**

| Flag de exibição | Descrição |
| ----- | ----- |
| `bExibePoligonosCarApp` | CAR — Área de Preservação Permanente |
| `bExibePoligonosCarAreaImovelAtivo/Pendente/Suspenso/Cancelado` | CAR — Área do Imóvel (4 status) |
| `bExibePoligonosCarHidrografia` | CAR — Hidrografia |
| `bExibePoligonosCarReservaLegal` | CAR — Reserva Legal |
| `bExibePoligonosCarVegetacaoNativa` | CAR — Vegetação Nativa |
| `bExibePoligonosCarManguezal/Restinga/Vereda/Banhado/BordaChapada` | CAR — Tipologias |
| `bExibePoligonosDeterAmazonia/Cerrado` | DETER — Alertas desmatamento |
| `bExibePoligonosProdesAmazonia/Cerrado/Caatinga/MataAtlantica/Pampa/Pantanal` | PRODES — por bioma |
| `bExibePoligonosAmbientalApp/AppUso/AppMassasDagua/AppManguezais/etc` | Ambiental — APP detalhado |
| `bExibePoligonosAmbientalReservaLegal/UsoRestrito/Restingas` | Ambiental complementar |
| `bExibePoligonosAmbientalAppRiosSimples/Duplos` | Ambiental — linhas hídricas |
| `bExibePontosAmbientalAppNascentes` | Nascentes |
| `bExibePontosFocosIncendio` | Focos de incêndio (cluster) |
| `bExibePoligonosAreasQueimadas` | Áreas queimadas |
| `bExibePoligonosBiomasBiomas/AmazoniaLegal/ReservaLegal` | Biomas |
| `bExibePoligonosUnidadesConservacao/bExibePoligonosRppn` | Unidades de Conservação \+ RPPN |
| `bExibePoligonosReservasBiosfera` | Reservas da Biosfera |
| `bExibePoligonosTerrasIndigenasRegularizada/Homologada` | Terras Indígenas |
| `bExibePoligonosQuilombosBrasil/Para` | Quilombos |
| `bExibePoligonosAssentamentosBrasil/Para` | Assentamentos |

## **5.3 CAMADAS IBGE / LIMITES**

| Flag | Descrição |
| ----- | ----- |
| `bExibePoligonosIbgeMunicipios/Estados/Pais` | Limites IBGE |
| `bExibePoligonosEstrangeiros` | Territórios estrangeiros |
| `bExibePoligonosLimitesDistritos/Subdistritos` | Subdivisões |
| `bExibePoligonosAreaFronteirasMunicipios/Faixa150/Faixa66/Faixa100` | Faixas de fronteira |

## **5.4 CAMADAS FUNDIÁRIAS ESTADUAIS (Parcelamento de Solo)**

Cobertura por estado com submódulos por cidade:

| Estado | Cidades cobertas | Tipos de dados |
| ----- | ----- | ----- |
| **RJ** | Capital, Niterói | PAL, Lotes, Quadras, Bairros, Edificações, Comunidades, Uso do Solo |
| **SP** | Capital, Orlândia, São Bernardo | Setor, Quadra, Lotes (SQL), Loteamento, Bairros |
| **PR** | Londrina, Ponta Grossa, Itaperuçu, Curitiba, Maringá | Lotes, Quadras, Base Cartográfica, Logradouro, Cadastro Municipal, Lotes Vazios, Ocupação Irregular |
| **CE** | Fortaleza | Lotes, Quadras, Bens Tombados (+ Entornos), Parques/UCs |
| **RS** | Santa Maria | Loteamento, Lotes, Quadras, Setor, Unidades de Inscrição |
| **MG** | Belo Horizonte | Lotes, Quadras, Cadastro Imobiliário |
| **PE** | Recife | Lotes, Edificações, Logradouros, Quadras, Bairros |
| **MA** | São João dos Patos | Edifcações, Lotes, Quadras |
| **BA** | Luís Eduardo Magalhães | Quadras, Lotes, Área de Expansão Urbana |
| **SC** | Tubarão, Capivari de Baixo, Florianópolis, São José | Lotes, Quadras, Edificações, Bairros, Limite Urbano |
| **AC** | Rio Branco | Quadras, Lotes, Edificações, Bairros |
| **PB** | João Pessoa | Quadras, Lotes, Bairros |
| **AM** | Manaus | Quadras, Lotes, Bairros |
| **RN** | Natal | Quadras, Lotes, Bairros |
| **MS** | Campo Grande | Quadras, Lotes, Bairros |
| **PA** | Belém | Bairros, Quadras |
| **BA** (georreferenciamento) | 11 sub-regiões (`bExibePontosBahia.1` a `.11`) | Polígonos RIB georreferenciados |

## **5.5 CAMADAS SECTORIAIS**

| Flag | Categoria | Descrição |
| ----- | ----- | ----- |
| `bExibePoligonosMineracaoAnm*` | Mineração | Arrendamento, Bloqueio, Processos Ativos, Proteção Fonte, Reservas Garimpeiras |
| `bExibePoligonosTransportesFerrovias/Rodovias/Dutovias/Hidrovias` | Transporte | Linhas de infraestrutura |
| `bExibePoligonosEnergiaLinhasTransmissao` | Energia | Linhas de transmissão |
| `bExibePoligonosEnergiaSubestacao/Biogas/Eolica/Etanol/Hidreletrica/Solar/Termoeletrica/Termonuclear/Cgh/Pch` | Energia | Usinas e centrais (11 tipos) |
| `bExibePontosTransportesAeroportos/Portos` | Transporte | Pontos |
| `bExibePontosIphanBensMateriaisPts/BemProtecao` | IPHAN | Patrimônio cultural |
| `bExibePoligonosIphanBensMateriais` | IPHAN | Polígonos |
| `bExibePontosIcmbioAutosInfracao` | ICMBio | Autos de infração |
| `bExibePoligonosIcmbioEmbargos` | ICMBio | Embargos |
| `bExibePontosProcessosSireneJud` | Judiciário | Processos SireneJud |
| `bExibePoligonosProcessosSireneJud` | Judiciário | Processos (polígonos) |
| `bExibePontosInfracoesTrabEscrav` | Trabalho | Infrações trabalho análogo à escravidão |
| `bExibePontosEmbrapaSolosPronasolos` | Embrapa | Pronasolos (pontos) |
| `bExibePoligonosEmbrapaSolos*` | Embrapa | Solos (6 tipos: Matopiba, Brasil Ad Solos, Erosão Hídrica, etc.) |
| `bExibePontosSpuImoveisUniao` | SPU | Imóveis da União |
| `bExibePoligonosImoveisPublicos*` | SPU/Federal | Áreas inalienáveis, Florestas não destinadas, Braviaco-PR |
| `bExibePoligonosCreditoRural` | Financeiro | Crédito Rural |
| `bExibePoligonosIbamaTermosEmbargo/AutorizacaoSupressao/ExploracaoFlorestal/etc` | IBAMA | 5 tipos |
| `bExibePoligonosIncraSnci/bExibePontosRuraisSigef/bExibePoligonosModulosFiscais` | INCRA | SNCI, SIGEF, Módulos Fiscais |
| `bExibePoligonosCarNascenteOlhoDagua` | CAR | Nascentes e Olhos d'água (cluster) |

## **5.6 CAMADAS CAR — DIVISÃO POR ESTADO**

O CAR Área Imóvel tem uma camada dedicada por estado (26 camadas total: `layer_car_poligonos_area_imovel` a `layer_car_poligonos_area_imovel_26`), mapeadas dinamicamente pelos 2 primeiros dígitos do código do imóvel (sigla UF).\[[mapa.onr.org](https://mapa.onr.org.br/resources/js/index-leaflet.js)\]​

---

## **6\. SISTEMA DE BUSCA / GEOCODING**

O geocoder usa `L.esri.Geocoding.geosearch` com providers customizados via `featureLayerProviderBuscaMapa()`.

## **Providers disponíveis:**

| ID | Camada consultada | Campo de busca | Modo |
| ----- | ----- | ----- | ----- |
| `endereco` | ArcGIS Online Geocoding | Endereço textual | Sugestão |
| `lat_lng` | — | Coordenadas `-22.9, -43.5` | Parse local |
| `rib_registros_cnm` | `layer_transacoes` | `cnm` | Strict |
| `rib_registros_cns_matricula` | Via PHP (`consultaCNMBusca`) \+ `layer_transacoes` | Matrícula |  |

## **Relatório de Engenharia Reversa — mapa.onr.org.br**

---

## **1\) URLs Reais Confirmadas (ArcGIS Services)**

## **Servidor privado: `gis-mapas.onr.org.br/onrgisserver` — ArcGIS Enterprise v11.4**

| \# | URL real (domínio \+ path) | Tipo | Classificação |
| ----- | ----- | ----- | ----- |
| 1 | `gis-mapas.onr.org.br/onrgisserver/rest/services/Hosted/Altitude_Brasil_SRTM/MapServer` | MapServer (tile) | **MapServer — tiledMapLayer / overlay altitude** |
| 2 | `gis-mapas.onr.org.br/onrgisserver/rest/services/Hosted/competencias_registrais_hml/FeatureServer/0/query` | FeatureServer (query) | **FeatureServer — polígonos RIB core (circunscrição registral)** |
| 3 | `gis-mapas.onr.org.br/onrgisserver/rest/services/Hosted/Unidades_Cartorios/FeatureServer/0/query` | FeatureServer (query) | **FeatureServer — pontos de cartórios (cluster)** |
| 4 | `gis-mapas.onr.org.br/onrgisserver/rest/services/Hosted/SIGEF_082025/FeatureServer/0/query` | FeatureServer (query) | **FeatureServer — imóveis rurais SIGEF (polígonos)** |
| 5 | `gis-mapas.onr.org.br/onrgisserver/rest/services/Hosted/layer_transacoes_6965160_1754671605/FeatureServer/0/query` | FeatureServer (query) | **FeatureServer — transações RIB (pontos/CNM)** |
| 6 | `gis-mapas.onr.org.br/onrgisserver/rest/services/Hosted/snci_competencias_matriculas_1466d/FeatureServer/0/query` | FeatureServer (query) | **FeatureServer — INCRA SNCI (certificações)** |
| 7 | `gis-mapas.onr.org.br/onrgisserver/rest/services/Hosted/mineracao_anm_ProcessosAtivos_HML/FeatureServer/0/query` | FeatureServer (query) | **FeatureServer — Mineração ANM (processos ativos)** |
| 8 | `gis-mapas.onr.org.br/onrgisserver/rest/services/Hosted/Deter_Amazonia/FeatureServer/0/query` | FeatureServer (query) | **FeatureServer — ambiental DETER Amazônia** |
| 9 | `gis-mapas.onr.org.br/onrgisserver/rest/services/Hosted/quilombos_HML/FeatureServer/0/query` | FeatureServer (query) | **FeatureServer — polígonos Quilombos** |
| 10 | `geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates` | Geocode | **ArcGIS Online Geocoding** (busca de endereços) |
| 11 | `basemaps-api.arcgis.com/arcgis/rest/services/styles/ArcGIS:Navigation` | VectorBasemapLayer | **Basemap vetorial ArcGIS Navigation** (fundo do mapa) |
| 12 | `mapa.onr.org.br/includes/mapa-leaflet/consultas-ajax.php` | PHP AJAX | **Backend PHP próprio** (reCAPTCHA \+ dados cartório/CNM) |

**Evidências diretas:**

* Root do servidor público: `{"currentVersion":11.4,"folders":["Hosted","Utilities"]}`\[[gis-mapas.onr.org](https://gis-mapas.onr.org.br/onrgisserver/rest/services?f=json)\]​  
* Lista completa de 32 FeatureServers exposta sem tokengis-mapas.onr.org+1  
* Query real em `Unidades_Cartorios/0/query` retornou 3 cartórios reais (Paranaíguara, Petrolina, Hidrolândia)\[[gis-mapas.onr.org](https://gis-mapas.onr.org.br/onrgisserver/rest/services/Hosted/Unidades_Cartorios/FeatureServer/0/query?where=1%3D1&outFields=*&resultRecordCount=3&f=json)\]​  
* Altitude MapServer retorna `{"error":{"code":499,"message":"Token Required"}}` — único serviço que exige token para tiles\[[gis-mapas.onr.org](https://gis-mapas.onr.org.br/onrgisserver/rest/services/Hosted/Altitude_Brasil_SRTM/MapServer?f=json)\]​  
* `competencias_registrais_hml` e `SIGEF_082025` retornam metadados completos sem tokengis-mapas.onr.org+1

---

## **2\) Token ArcGIS e API Key — Como Entram nos Requests**

## **a) `sTokenArcGis` — token de sessão do ArcGIS Enterprise privado**

**Como é obtido:** Gerado via `POST` para `gis-mapas.onr.org.br/onrgisserver/tokens/generateToken` com credenciais do usuário logado (PHP backend retorna o token após login com reCAPTCHA). O endpoint GET está explicitamente desabilitado: `"HTTP GET is disabled"`.\[[gis-mapas.onr.org](https://gis-mapas.onr.org.br/onrgisserver/tokens/generateToken?f=json)\]​

**Como entra nos requests:** **Sempre em querystring**, padrão `?token=<sTokenArcGis>`. No código-fonte:\[[mapa.onr.org](https://mapa.onr.org.br/)\]​

js  
`L.esri.query({ url: oCamadas.layer_poligonos.path }).token(sTokenArcGis)`  
`L.esri.tiledMapLayer({ url: "...Altitude_Brasil_SRTM/MapServer", token: sTokenArcGis })`  
`L.esri.featureLayer({ url: ..., token: sTokenArcGis })`

A biblioteca `esri-leaflet` injeta automaticamente `?token=` em cada request.

**Renovação do token:** O código referencia `window.arcGisTokenManager` (instância de `ArcGisTokenManager`) passado como `tokenManager: window.arcGisTokenManager` em todas as classes de camada. Isso indica renovação automática: quando a resposta retorna erro 498/499, o TokenManager faz novo POST para `/generateToken` e re-executa o request original com o novo token — tudo transparente ao usuário.

**Descoberta crítica:** A maioria dos FeatureServers tem `allowAnonymousToQuery: true` e `allowOthersToQuery: true` — ou seja, **queries de dados não exigem token**. O token só é obrigatório para o `Altitude MapServer` (tile/raster) e para camadas com edição ativa.gis-mapas.onr.org+2

## **b) `sApiKey` — API Key da ESRI (ArcGIS Online)**

**Como é obtida:** No código:\[[mapa.onr.org](https://mapa.onr.org.br/)\]​

js  
`const sApiKey = atob(sArcgisApiKey)`

A variável `sArcgisApiKey` é um Base64 injetado pelo servidor PHP no HTML (fora do escopo do JS público). Decodificada via `atob()` no client-side.

**Como entra nos requests:** Via parâmetro `apiKey` na inicialização da camada vetorial:

js  
`L.esri.Vector.vectorBasemapLayer('ArcGIS:Navigation', { apiKey: sApiKey })`

O SDK de basemap vetorial da ESRI injeta a key como `token=<sApiKey>` nas requisições para `basemaps-api.arcgis.com`. Não vai em header Authorization.

**Também usada no Geocoding:** O provider `featureLayerProviderBuscaMapa` recebe `apikey: sApiKey` para buscas de endereço sem sessão autenticada.

---

## **3\) Fluxo PHP AJAX \+ reCAPTCHA — Evidência Completa**

## **Endpoint**

text  
`POST /includes/mapa-leaflet/consultas-ajax.php`

## **Parâmetros enviados (extraídos do código )\[[mapa.onr.org](https://mapa.onr.org.br/)\]​**

| `acao` | Dados enviados | O que retorna |
| ----- | ----- | ----- |
| `consultaInfoCartorio` | `idCartorio: [array de ids]` \+ `recaptchaToken` | Array com dados completos da serventia: nome, endereço, CNS, comarca/UF, website, pathFachada |
| `consultaCNMBusca` | `matricula`, `cns`, `text`, `recaptchaToken` | Array `{CNM, Serventia, Matricula}` — traduz matrícula+CNS → CNM numérico |

## **Fluxo detalhado**

text  
`1. Usuário clica em marcador de cartório no mapa`  
`2. JS chama validate_recaptcha(callback)`  
   `↓`  
`3. grecaptcha.ready() → grecaptcha.execute(key) → Promise<sToken>`  
   `↓`  
`4. $.post('/includes/mapa-leaflet/consultas-ajax.php',`  
         `{ acao: 'consultaInfoCartorio',`  
           `idCartorio: [ids],`  
           `recaptchaToken: sToken })`  
   `↓`  
`5. PHP valida sToken via API do Google (curl para googleapis.com)`  
   `- Falha → retorna {"mensagem":"Erro na validação do reCAPTCHA"}  ← Screenshot 1 da sua conversa`  
   `- Sucesso → consulta banco de dados ONR`  
   `↓`  
`6. PHP retorna { dados: [{nome, endereco_logradouro, cartorio, ...}] }`  
   `↓`  
`7. JS monta popup HTML e abre no Leaflet`

## **Mecanismo de retry**

O código implementa retry automático com até **2 tentativas**:\[[mapa.onr.org](https://mapa.onr.org.br/)\]​

js  
`let tentativas = 0;`  
`const enviar = () => {`  
  `tentativas++;`  
  `validate_recaptcha((sToken) => {`  
    `$.post(sUrlAjax, {..., recaptchaToken: sToken}, ...)`  
    `.fail((oResultado) => {`  
      `if (tentativas < 2) { enviar(); return; }`  
      `// exibe erro`  
    `});`  
  `});`  
`};`  
`enviar();`

## **O erro na primeira screenshot da sua conversa**

json  
`{"mensagem":"Erro na validação do reCAPTCHA"}`

Isso é o retorno do `consultas-ajax.php` quando o token reCAPTCHA expirou ou foi rejeitado pelo Google — o request chegou ao PHP mas falhou na validação do captcha. É o comportamento esperado quando se acessa sem sessão válida.

---

## **Resumo da Arquitetura**

text  
`Browser (Leaflet + esri-leaflet)`  
  `│`  
  `├─→ ArcGIS Enterprise (gis-mapas.onr.org.br) — 32 FeatureServers`  
  `│     ├─ Query: ?token= em querystring (via esri-leaflet automático)`  
  `│     ├─ Maioria: allowAnonymousToQuery=true (sem token p/ query)`  
  `│     └─ Tile MapServer: exige token obrigatoriamente (erro 499)`  
  `│`  
  `├─→ ArcGIS Online (geocode.arcgis.com) — Geocoding mundial`  
  `│     └─ ?token= ou apiKey= (ambos suportados)`  
  `│`  
  `├─→ ArcGIS Basemap (basemaps-api.arcgis.com) — Vetorial Navigation`  
  `│     └─ apiKey= (decodificada de Base64 no client)`  
  `│`  
  `├─→ bdgex.eb.mil.br/mapcache — WMS topográfico (sem auth)`  
  `│`  
  `└─→ mapa.onr.org.br/includes/mapa-leaflet/consultas-ajax.php`  
        `└─ POST com recaptchaToken + ação → dados privados do ONR`

## **Engenharia Reversa Completa — mapa.onr.org.br**

---

## **1\. ARQUITETURA GERAL**

O sistema é composto por três camadas distintas:

| Camada | Tecnologia | Domínio |
| ----- | ----- | ----- |
| Frontend Leaflet | JS \+ jQuery \+ ESRI Leaflet | `mapa.onr.org.br` |
| GIS Backend | ArcGIS FeatureServer 11.4 | `gis-mapas.onr.org.br` |
| Basemap Topográfico | WMS (Exército Brasileiro) | `bdgex.eb.mil.br/mapcache` |

---

## **2\. CATÁLOGO COMPLETO — FeatureServer ONR**

**Base URL:** `https://gis-mapas.onr.org.br/onrgisserver/rest/services/Hosted/`\[[gis-mapas.onr.org](https://gis-mapas.onr.org.br/onrgisserver/rest/services/Hosted?f=json)\]​

Todos retornam `type: "FeatureServer"` e aceitam `?f=json`:

## **Camadas Proprietárias ONR**

| Nome do Serviço | Descrição |
| ----- | ----- |
| `competencias_registrais_hml` | **Principal** — Polígonos de competência registral (circunscrições) por cartório |
| `Unidades_Cartorios` | Pontos (multipoint) das unidades cartorárias do Brasil |
| `snci_competencias_matriculas_1466d` | Competências e matrículas INCRA/SNCI |
| `layer_transacoes_6965160_...` | Transações de imóveis (CNM) — múltiplas instâncias com timestamps |
| `layer_transacoes_6965161_...` | idem (shard 2\) |
| `layer_transacoes_6981793_...` | idem (shard 3\) |

## **Dados Ambientais / Fundiários**

| Nome do Serviço | Fonte |
| ----- | ----- |
| `CAR_AM_Imoveis` | CAR — Área do Imóvel (Amazonas) |
| `CAR_AM_RESERVA` | CAR — Reserva Legal |
| `CAR_AM_SERVIDAO_ADM` | CAR — Servidão Administrativa |
| `FBDS_NASCENTES_SUL` | FBDS — Nascentes (região Sul) |
| `FBDS_RIOS_SIMPLES_SUL` | FBDS — Rios simples (Sul) |
| `AREA_IMOVEL_ATU_UF_RS_HML` | Área de imóvel atualizada — RS |
| `AREA_IMOVEL_ATU_UF_SC_HML` | Área de imóvel atualizada — SC |
| `Areas_Queimadas_2025_03_01_aq1km_V6` | Áreas queimadas (INPE/MapBiomas) |
| `Focos_Mensais_22042025` | Focos de incêndio mensais |
| `CNUC_03_2025` | Unidades de Conservação (CNUC/MMA) |
| `RPPN_06_2025` | RPPNs |
| `UCs_06_2025` | Unidades de Conservação (atualizado) |
| `quilombos_HML` | Territórios Quilombolas |
| `Deter_Amazonia` | DETER — Amazônia |
| `Deter_Cerrado` | DETER — Cerrado |
| `Deter_Nao_Floresta` | DETER — Não floresta |
| `SIGEF_082025` | SIGEF (polígonos rurais certificados) |
| `sigef_20241220_175752_hml` | SIGEF (versão anterior) |
| `BR_Municipios_2022_33961` | Municípios brasileiros (IBGE 2022\) |
| `sp_capital_lotes_20221227_0849_v2_HML` | Lotes — São Paulo Capital |
| `mineracao_anm_Arrendamento2_HML` | ANM — Arrendamento |
| `mineracao_anm_Bloqueio2_hml` | ANM — Bloqueio |
| `mineracao_anm_ProcessosAtivos_HML` | ANM — Processos Ativos |
| `mineracao_anm_ProtecaoFonte_4e3f9` | ANM — Proteção de Fonte |
| `mineracao_anm_ProtecaoFonte_Novo_HML` | ANM — Proteção de Fonte (novo) |
| `mineracao_anm_ReservasGarimpeiras_HML` | ANM — Reservas Garimpeiras |

---

## **3\. SCHEMA DAS CAMADAS PRINCIPAIS**

## **`competencias_registrais_hml` (Layer 0 — Polígono)\[[gis-mapas.onr.org](https://gis-mapas.onr.org.br/onrgisserver/rest/services/Hosted/competencias_registrais_hml/FeatureServer/0?f=json)\]​**

| Campo | Tipo | Tamanho | Descrição |
| ----- | ----- | ----- | ----- |
| `fid` | OID | 4 | Chave primária |
| `cartorio` | String | 192 | Nome da serventia |
| `codigo_cns` | String | 10 | Código Nacional da Serventia |
| `cor` | String | 10 | Cor de preenchimento do polígono |
| `cor_borda` | String | 10 | Cor da borda |
| `uf` | String | 4 | UF |
| `comarca` | String | 100 | Comarca |
| `obs` | String | 254 | Observações |
| `abrangen` | String | 121 | Abrangência do cartório |
| `area_m2` | Double | — | Área em m² |
| `perimetro` | Double | — | Perímetro em metros |
| `temp` | String | 10 | Campo temporário |
| `SHAPE__Length` | Double (virtual) | — | Comprimento do shape |
| `SHAPE__Area` | Double (virtual) | — | Área do shape |

*   
  **Geometria:** `esriGeometryPolygon`  
* **SR:** EPSG:3857 (Web Mercator), WKID 102100  
* **maxScale:** 1128 (muito detalhado), **minScale:** 73.957.191  
* **serviceItemId:** `d91a06be439b4add9eac364ae05f22f4`

## **`Unidades_Cartorios` (Layer 0 — Ponto)\[[gis-mapas.onr.org](https://gis-mapas.onr.org.br/onrgisserver/rest/services/Hosted/Unidades_Cartorios/FeatureServer/0?f=json)\]​**

| Campo | Tipo | Tamanho | Descrição |
| ----- | ----- | ----- | ----- |
| `fid` | OID | 4 | Chave primária |
| `x` | Double | — | Longitude |
| `y` | Double | — | Latitude |
| `cns` | String | 254 | Código Nacional da Serventia |
| `idcartorio` | String | 10 | ID do cartório |
| `endereco` | String | 254 | Endereço completo |
| `cod_mun` | String | 7 | Código IBGE do município |
| `nm_mun` | String | 100 | Nome do município |
| `cartorio` | String | 254 | Nome do cartório |

*   
  **Geometria:** `esriGeometryMultipoint`  
* **maxRecordCount:** 2000, **standardMaxRecordCount:** 16000

---

## **4\. ENDPOINT AJAX — `/includes/mapa-leaflet/consultas-ajax.php`**

**URL:** `POST /includes/mapa-leaflet/consultas-ajax.php`

Todas as requisições exigem token Google reCAPTCHA v3 no campo `recaptchaToken`.

| Parâmetro `acao` | Campos | Resposta |
| ----- | ----- | ----- |
| `consultaInfoCartorio` | `idCartorio` (array de IDs) | `dados[]` com nome, endereço, comarca, UF, CNS, urlHotsite, pathFachada, jsonConfiguracao.websiteCartorio |
| `consultaCNMBusca` | `matricula`, `cns`, `text` | `dados[].CNM`, `dados[].Serventia`, `dados[].Matricula` |

**Estrutura do retorno `consultaInfoCartorio`:**

json  
`{`  
  `"dados": [{`  
    `"nome": "...",`  
    `"tipoLogradouro": "...",`  
    `"endereco_logradouro": "...",`  
    `"endereco_numero": "...",`  
    `"endereco_complemento": "...",`  
    `"endereco_bairro": "...",`  
    `"endereco_cep": "...",`  
    `"comarca": "...",`  
    `"uf": "...",`  
    `"codigo_cns": "...",`  
    `"urlHotsite": "...",`  
    `"pathFachada": "...",`  
    `"jsonConfiguracao": { "websiteCartorio": "..." }`  
  `}]`  
`}`

---

## **5\. SERVIÇOS WMS EXTERNOS — BDGEX (Exército Brasileiro)**

**Base URL:** `https://bdgex.eb.mil.br/mapcache`  
**Usado via:** `L.tileLayer.wms()` com layers combinadas: `ctm250,ctm100,ctm50,ctm25`\[[gis-mapas.onr.org](https://gis-mapas.onr.org.br/onrgisserver/rest/services/Hosted/competencias_registrais_hml/FeatureServer/0?f=json)\]​

| Layer | Descrição |
| ----- | ----- |
| `ctm25` | Cartas Topográficas 1:25.000 |
| `ctm50` | Cartas Topográficas 1:50.000 |
| `ctm100` | Cartas Topográficas 1:100.000 |
| `ctm250` | Cartas Topográficas 1:250.000 |
| `ctmmultiescalas` | CTM multi-escala (25k–250k) |
| `ctmmultiescalas_mercator` | CTM multi-escala em EPSG:3857 |
| `Multiescala_LocalidadesLimites` | Localidades e limites políticos |
| `Multiescala_Hidrografia` | Hidrografia vetorial |
| `Multiescala_Relevo` | Relevo (curvas de nível) |
| `Multiescala_RodoviasFerrovias` | Vias terrestres |
| `mds25` / `mds50` / `mds250` | Modelo digital de superfície (MDS) |
| `curva_nivel25/50/100/250` | Curvas de nível por escala |
| `cartaimagem25/50/100/250` | Cartas imagem |
| `ortoimagem_scn25` | Ortoimagens SCN |
| `ortoimagens_codeplan` | Ortoimagens CODEPLAN-DF |
| `landsat7` | Landsat 7 (ano 2000\) |
| `rapideye` | RapidEye (2013) |
| `municipios` | Municípios 1:250.000 |
| `estados` | Estados 1:250.000 |
| `capitais` | Capitais estaduais |
| `ram_mds` / `ram_colorimetria_25/50` | Sensores orbitais colorimétricos |
| `censo_heatmap_pop` | Mapa de calor — densidade pop. |
| `censo_idoso` | % idosos por setor censitário |

---

## **6\. BASEMAPS LEAFLET**

javascript  
*`// Topográfico (BDGEX WMS)`*  
`L.tileLayer.wms('https://bdgex.eb.mil.br/mapcache', {`  
  `layers: 'ctm250,ctm100,ctm50,ctm25',`  
  `format: 'image/png',`  
  `transparent: true,`  
  `crs: L.CRS.EPSG4326`  
`})`

*`// Satélite (Google Maps)`*  
`L.tileLayer('https://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}', {`  
  `subdomains: ['mt0','mt1','mt2','mt3']`  
`})`

*`// Mapa (ESRI Vector)`*  
`L.esri.Vector.vectorBasemapLayer('ArcGIS:Navigation', { apiKey: sApiKey })`

*`// Altitude (overlay — ESRI TiledMapLayer)`*  
*`// URL: https://gis-mapas.onr.org.br/onrgisserver/rest/services/Hosted/Altitude_Brasil_SRTM/MapServer`*

---

## **7\. PROVIDERS DE BUSCA/GEOCODING**

| ID do Provider | Camada ArcGIS | Campos de Busca |
| ----- | ----- | ----- |
| `endereco` | ArcGIS Online Geocoder | endereço livre |
| `lat_lng` | — | coordenadas `-22.9, -43.5` |
| `rib_registros_cnm` | `layer_transacoes` | `cnm` |
| `geo_rib_numero_matricula` | `layer_poligonos_rib` | `matricula` |
| `geo_rib_numero_poligono` | `layer_poligonos_rib` | `id` |
| `geo_rib_cnm` | `layer_poligonos_rib` | `cnm` |
| `geo_rib_nome_imovel` | `layer_poligonos_rib` | `nome_imovel` |
| `rib_registros_cns_matricula` | Ajax `consultaCNMBusca` | matrícula \+ CNS |
| `sigef_area` | `layer_mosaicos_rurais` | `nome_area`, `cidade` |
| `sigef_codigo` | `layer_mosaicos_rurais` | `codigo_imo` (CCIR/SNCR) |
| `sigef_parcela` | `layer_mosaicos_rurais` | `parcela_co` (hash UUID) |
| `snci_certificado` | `layer_incra_snci` | `num_certif` |
| `car_area_imovel` | `layer_car_poligonos_area_imovel` (por UF: `_1` a `_26`) | `cod_imovel` |
| `imo_spu` | `layer_spu_imoveis_uniao` | `num_rip` |
| `pa_rj_*` | Parcelamento solo RJ (PAL/lotes/quadras) | `num_projeto`, `cod_lote`, `cod_quadra` |
| `pa_sp_*` | Parcelamento solo SP (setor/quadra/lotes) | `st_id`, `qd_id`, `st_qd_lo` |

---

## **8\. VARIÁVEIS E CONSTANTES GLOBAIS**

| Variável | Valor / Descrição |
| ----- | ----- |
| `sUrlAjax` | `/includes/mapa-leaflet/consultas-ajax.php` |
| `POLIGONOS_HABILITADOS` | `true` |
| `iDefaultZoomLevel` | `13` |
| `iZoomLimitador` | `16` (zoom mínimo para consulta sem limite de registros) |
| `iLimiteConsultaPontos` | `200` |
| `fFatorSimplificacao` | `0.5` (simplificação de geometrias ArcGIS) |
| \`larguraPadraoBord |  |


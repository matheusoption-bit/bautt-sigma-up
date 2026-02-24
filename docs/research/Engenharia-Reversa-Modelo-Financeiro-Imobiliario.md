# **Arquitetura do Motor de Cálculo e Engenharia Reversa do Modelo de Viabilidade Financeira**

A arquitetura financeira imobiliária estabelece a espinha dorsal de qualquer empreendimento, ditando as diretrizes de viabilidade, os limites de exposição ao risco e a projeção de retornos sobre o capital alocado. A análise profunda do modelo financeiro contido no arquivo de planilhas eletrônicas revela um ecossistema de cálculo desenhado para orquestrar e comparar múltiplos cenários de desenvolvimento imobiliário. O modelo se estrutura a partir de duas metodologias distintas e simultâneas de orçamentação: uma abordagem paramétrica baseada no Custo Unitário Básico (CUB) e uma abordagem analítica fundamentada nas composições de custo do Sistema Nacional de Pesquisa de Custos e Índices da Construção Civil (SINAPI).1

A averiguação rigorosa demonstra que o objetivo primário da ferramenta é fornecer uma base comparativa de cenários para validar a viabilidade de um projeto específico, identificado como "Bautt Construções", localizado no município de Florianópolis, Santa Catarina.1 O empreendimento alvo da simulação principal consiste em uma unidade residencial unifamiliar de alto padrão, com trezentos metros quadrados de área privativa, projetada para gerar um Valor Geral de Venda nominal de exatos quatro milhões e duzentos mil reais.1 Contudo, a integridade da ferramenta encontra-se severamente comprometida por quebras na cadeia de dependências relacionais, evidenciadas por erros sistêmicos de referência em abas de consolidação, o que impacta diretamente a geração de relatórios destinados a instituições financeiras e a equalização de propostas de crédito.1

Este documento técnico mapeia a totalidade da inteligência financeira, o fluxo de dados, as fórmulas matemáticas implícitas e os gargalos estruturais da planilha. O detalhamento a seguir serve como a documentação definitiva e o guia arquitetural para a reconstrução do motor de cálculo em um ambiente de software robusto, escalável e livre das vulnerabilidades inerentes ao uso não estruturado de matrizes eletrônicas.

## **ETAPA 1 — INVENTÁRIO E ESTRUTURA**

A engenharia reversa do modelo exige o mapeamento categórico de todos os componentes planilhados. O sistema é composto por um conjunto de abas que atuam em diferentes camadas de processamento de dados, desde a entrada de premissas brutas até a exportação de formulários de conformidade bancária. A taxonomia das abas permite compreender a arquitetura da informação e a separação de responsabilidades dentro do modelo de cálculo.

A aba denominada SIMULAÇÃO 01 classifica-se primordialmente como uma aba de INPUT, PARÂMETROS e CÁLCULO INTERMEDIÁRIO. Esta interface atua como o painel principal de entrada de dados do usuário. Ela absorve variáveis independentes críticas, tais como a área do lote, a área privativa, o preço de venda por metro quadrado, os prazos de execução escalonados em meses e os custos fixos adicionais que não estão previstos em índices padronizados.1 Simultaneamente, esta aba processa cálculos intermediários vitais, como a equivalência de área regida pela norma ABNT NBR 12.721 e a distribuição dos marcadores binários do cronograma temporal.1

As abas SIMULAÇÃO 02, SIMULAÇÃO 03 e SIMULAÇÃO 04 compartilham a exata mesma classificação de INPUT e PARÂMETROS da primeira simulação. Elas representam estruturas espelhadas concebidas com o intuito de permitir a análise de sensibilidade e testes de estresse financeiro comparativo. No estado atual do documento, estas instâncias encontram-se com valores zerados ou em branco, aguardando a inserção de variáveis independentes para a geração de cenários alternativos de rentabilidade.1

A aba identificada como ORÇ\#1 classifica-se como TABELA DE APOIO e CÁLCULO INTERMEDIÁRIO. Este é o motor analítico de orçamentação da ferramenta. A aba detalha exaustivamente o orçamento de custos diretos da obra com base em códigos de composição do SINAPI, estruturando os gastos em uma hierarquia de quatro níveis analíticos. É neste ambiente que ocorre o processamento do custo real e unitário dos insumos, da mão de obra e a posterior aplicação da taxa de Bonificação e Despesas Indiretas.1

A Planilha1 assume o papel de CONSOLIDAÇÃO. Ela atua como um painel de agregação estático que resume os milhares de itens do orçamento analítico fragmentado na aba ORÇ\#1 em apenas dezoito macroetapas construtivas, tais como Serviços Preliminares, Estrutura, Alvenarias e Instalações Prediais. Esta aba funciona como uma matriz de transição estrita entre o orçamento bruto e os relatórios financeiros de alto nível, culminando em um montante superior a seis milhões de reais.1

A aba COMPARATIVO é designada como RELATÓRIO/OUTPUT. Trata-se do painel de controle financeiro global do projeto. Consiste em uma matriz comparativa que alinha horizontalmente os resultados das quatro simulações, consolidando as despesas matemáticas em categorias macroeconômicas, como custos de terreno, construção, comercialização, seguros e impostos. O seu objetivo é extrair o resultado líquido final e a margem de viabilidade operacional de cada cenário.1

Por fim, a aba RELATÓRIO classifica-se estritamente como RELATÓRIO/OUTPUT. Este documento foi desenhado para atender às exigências de conformidade documental de instituições bancárias, atuando como uma Proposta de Cronograma de Investimento (PCI). O relatório tenta equalizar os dados do orçamento analítico contra os valores adotados para o financiamento, distribuindo os montantes em um fluxo de caixa temporal. Atualmente, esta aba sofre de corrupção estrutural severa, manifestando múltiplos erros de referência.1

A investigação técnica sobre a infraestrutura da planilha revela a ausência completa do uso de Tabelas Estruturadas nativas do Excel e de Nomes Definidos (Named Ranges) para a manipulação de variáveis. A arquitetura baseia-se unicamente em referências absolutas e relativas de endereços de células. Esta abordagem arquitetural rudimentar é a causa primária da fragilidade do modelo, culminando no colapso dos apontamentos algorítmicos observados na aba de equalização bancária.1 Não foram identificados indícios de rotinas automatizadas em Visual Basic for Applications (VBA) ou consultas modeladas via PowerQuery, confirmando que a inteligência de processamento reside inteiramente em fórmulas interligadas nas células visíveis.

## **ETAPA 2 — MAPEAMENTO DO MOTOR FINANCEIRO**

Para que a reconstrução sistêmica da inteligência em formato de código seja precisa, cada módulo financeiro existente deve ser isolado e sua lógica descrita detalhadamente em linguagem natural. O modelo opera através de blocos de processamento que transformam premissas de projeto em demonstrações de resultados.

O módulo de Receita possui o objetivo de determinar o montante total de capital bruto que ingressará no projeto. Este bloco utiliza como inputs a área privativa da unidade (estabelecida em trezentos metros quadrados), o preço estimado de venda por metro quadrado (parametrizado em quatorze mil reais) e a quantidade total de unidades do empreendimento.1 O output gerado é o Valor Geral de Vendas nominal, totalizado em quatro milhões e duzentos mil reais. A fórmula que estrutura este módulo multiplica a área privativa pelo preço unitário e pelo número de unidades. Quanto à sua dependência temporal, o montante é distribuído de forma linear e uniforme ao longo de um período de doze meses, compreendido entre janeiro e dezembro de um ano projetado, injetando uma fração idêntica de capital a cada mês no fluxo de caixa.1 Esta premissa linear ignora a realidade das curvas de absorção mercadológica observadas em transações imobiliárias reais.2

O módulo de Investimentos e Capex ramifica-se em duas metodologias conflitantes dentro do mesmo arquivo. A primeira abordagem é a Engenharia de Custos Paramétricos, cujo objetivo é estabelecer um teto de custo de construção baseado nas diretrizes normativas da ABNT NBR 12.721.3 Os inputs incluem um índice base de Custo Unitário Básico referenciado no padrão R8-A de Santa Catarina (no valor de mil oitocentos e vinte e cinco reais e dez centavos por metro quadrado), aliado a uma listagem de áreas do projeto divididas por tipologia arquitetônica.1

A fórmula deste bloco paramétrico opera em etapas. Primeiramente, calcula-se a área equivalente de construção aplicando coeficientes redutores sobre áreas não habitáveis. Áreas de garagem em subsolo, por exemplo, recebem um coeficiente de zero vírgula setenta e cinco, o que significa que apenas setenta e cinco por cento de sua área real será considerada para o cálculo de custo de construção.1 Terraços descobertos recebem um peso ainda menor, de zero vírgula seis. A soma de todas as áreas ponderadas gera a Área Equivalente Total. O custo base da construção é o produto desta área equivalente pelo índice CUB. Em seguida, o módulo soma custos que a norma técnica não abrange, como fundações especiais, implantação de elevadores e sistemas de ar-condicionado.1 A adição do custo base aos itens extras resulta em um orçamento paramétrico de quatro milhões, quatrocentos e trinta e três mil reais, valor que é diretamente transferido para a aba de consolidação comparativa.1

Simultaneamente, existe o módulo de Orçamentação Executiva, cujo objetivo é calcular o custo estrito de execução através de um levantamento detalhado de insumos. Este bloco utiliza como inputs os quantitativos extraídos de projeto e as composições de preços unitários balizados pelo SINAPI.1 A estrutura agrupa os custos em quatro níveis hierárquicos. O cálculo base de cada serviço é a soma do preço da mão de obra, do custo do material e do valor do equipamento, multiplicada pela quantidade requerida.1 O fator mais crítico deste módulo é a aplicação da Bonificação e Despesas Indiretas (BDI). A fórmula multiplica o custo direto da composição por um fator indexador implícito de um vírgula vinte, indicando a incidência de uma margem de vinte por cento.1 Este módulo gera um total superior a seis milhões de reais, criando um cenário de custos completamente divergente do cenário paramétrico adotado na consolidação principal.1

O módulo voltado para a Aquisição de Terreno e Legalização objetiva consolidar os custos fundiários indispensáveis para a estruturação imobiliária. Ele requer como inputs o valor acordado para o pagamento do lote, o valor venal do imóvel perante a prefeitura e a alíquota do Imposto sobre a Transmissão de Bens Imóveis. O cálculo subtrai o percentual de dois por cento sobre o valor venal de duzentos mil reais, resultando em despesas acessórias que são somadas ao valor principal do terreno.1 O resultado deste módulo é exportado diretamente para o demonstrativo de resultados do projeto.1

O módulo de Opex e Comercialização tem a finalidade de provisionar todas as despesas decorrentes do esforço de vendas, publicidade e gestão gerencial. Os inputs são taxas percentuais predefinidas que incidem sobre duas bases distintas: o Valor Geral de Vendas e o Custo Paramétrico de Obra.1 A formulação matemática extrai cinco por cento do faturamento bruto para comissionamento de corretores, um por cento para a administração de vendas e meio por cento para o orçamento de marketing. A taxa de administração da construtora, por sua vez, é calculada aplicando-se um fator de dez por cento estritamente sobre o montante final derivado da estimativa do CUB.1 Outra taxa relevante é a de regularização imobiliária, parametrizada em três por cento do Valor Geral de Vendas.1

O módulo de Seguros atua como um mitigador financeiro de riscos patrimoniais durante o ciclo de execução e entrega das chaves. A mecânica deste bloco aplica um índice de risco linear e constante de zero vírgula zero oito por cento sobre a base do custo total da construção. Este cálculo é replicado independentemente para três apólices obrigatórias: o Risco de Engenharia, a Assistência Técnica pós-obra e a Garantia de Conclusão da Obra. O somatório dos prêmios constitui a linha de despesas de seguros no resultado final.1

O módulo de Impostos e Custo de Capital reflete o encargo tributário governamental e o custo de oportunidade associado ao financiamento da operação. Para a carga tributária, o sistema aplica uma alíquota fixa e agrupada de quatro por cento sobre a receita total de vendas, não segregando os tributos específicos do Regime Especial de Tributação ou do Lucro Presumido.1 A rotina de custo de capital apresenta uma lógica matemática obscura na estrutura atual. O cálculo exige uma base financeira de um milhão, trezentos e cinquenta e quatro mil reais, associada a uma taxa percentual de dois e meio por cento sob um ciclo de doze meses.1 A formulação exata não está explicitada na interface, mas os princípios de matemática financeira apontam para a apuração de juros sobre o saldo devedor de um financiamento para a aquisição do lote e infraestrutura inicial, operando como o WACC (Custo Médio Ponderado de Capital) do empreendimento.1

Por fim, o módulo de Fluxo de Caixa e Indicadores possui o objetivo de mensurar a atratividade econômica do investimento. Na arquitetura financeira clássica, este módulo requer as projeções de saldo líquido mensal para extrair o Valor Presente Líquido, a Taxa Interna de Retorno e o Payback descontado.5 Contudo, no presente modelo, as fórmulas analíticas destes indicadores encontram-se inoperantes ou ocultas porque o somatório algébrico simples das receitas contra as despesas operacionais resulta em um déficit absoluto alarmante.1 A matemática subjacente não consegue processar um retorno sobre o investimento quando não há inversão do sinal do fluxo de caixa, impedindo a obtenção de uma taxa interna real e limitando a análise à extração da margem operacional negativa de quase setenta por cento sobre o faturamento.1

## **ETAPA 3 — GRAFO DE DEPENDÊNCIAS**

A orquestração da inteligência financeira modelada opera em um formato que pode ser traduzido algoritmica e estruturalmente como um Grafo Direcionado Acíclico. O fluxo delineia a propagação determinística da informação, desde as células embrionárias de parâmetros até os relatórios de conformidade. A topologia a seguir representa a mecânica relacional da planilha.

↓

↓

↓

↓

↓

↓

O fluxo se inicia nos, onde o usuário alimenta o motor com as especificações físicas do lote, a área privativa da unidade, os índices do Custo Unitário Básico, as percentagens de remuneração de terceiros e os quantitativos arquitetônicos na aba de orçamentação.1

A partir deste vetor primário, o modelo se bifurca. Uma vertente do grafo direciona os dados para o, onde a área privativa e o valor do metro quadrado convergem para gerar a Receita de Vendas máxima esperada. Simultaneamente, as áreas excedentes do projeto são submetidas às regras normativas, sofrendo a aplicação dos coeficientes redutores que originarão a área equivalente global da edificação.1

O vetor seguinte aciona o. A área equivalente gerada no passo anterior é multiplicada pelo indexador econômico selecionado. A este produto, injetam-se as parcelas de capital referentes a itens de infraestrutura extraordinária não contemplados na norma técnica, estabelecendo a linha base do teto de gastos do projeto em alto nível.1

Em paralelo, de forma quase independente do fluxo principal, o é instanciado. Este nó do grafo itera sobre a vasta listagem de serviços granulares. Ele agrupa os salários, encargos, custos de locação de equipamentos e suprimentos físicos, aplicando sobre cada pacote uma margem estática de proteção correspondente à Bonificação e Despesas Indiretas. A agregação hierárquica finaliza o levantamento bottom-up do projeto.1

A consolidação converge as informações no. Com a Receita de Vendas e o Custo Paramétrico fixados nos nós anteriores, o sistema propaga essas duas cifras como variáveis globais para determinar o montante a ser pago aos corretores, a parcela devida ao fisco, os prêmios das seguradoras patrimoniais e a fatia exigida pela taxa de administração da construtora.1

O penúltimo nó do sistema é o. Todos os fluxos financeiros negativos, desde a aquisição do lote até o pagamento do capital de terceiros, são somados para formar o bloco de custo consolidado. Este bloco é então confrontado contra a variável de receita total retida em memória.1

O grafo encerra-se nos. A demonstração do resultado do exercício é gerada na aba comparativa. Um processo paralelo deveria instanciar os cálculos no documento de conformidade bancária, exigindo o pareamento temporal das despesas ao longo do cronograma estabelecido.

O detalhamento das dependências revela falhas arquiteturais proeminentes. A dependência cruzada entre as abas que geram a orçamentação detalhada e a interface de apresentação bancária sofreu uma desintegração. As células do nó de consolidação orçamentária para a matriz PCI exibem falhas de referência global. Quando o motor tenta buscar o cruzamento entre o orçamento planejado e a equalização exigida, a falta de estruturação dos arrays bidimensionais resulta na quebra total da lógica de extração temporal.1 Além disso, o documento evita o uso de funções voláteis, o que impede problemas de recálculo contínuo, mas a dependência estrita em células críticas não nomeadas aumenta exponencialmente a probabilidade de erros humanos catastróficos caso uma linha seja adicionada ou excluída no fluxo de inserção de dados.

## **ETAPA 4 — DICIONÁRIO DE DADOS**

A formalização da arquitetura exige a tradução do modelo matemático e de negócios em um esquema de dados tipado e mapeado. A tabela a seguir especifica o dicionário lógico que embasa a reconstrução do motor, detalhando cada variável, seu local de declaração primária e o impacto de suas mutações na matriz de resultados.

| Campo | Aba | Tipo | Função no Modelo | Influencia quais outputs? |
| :---- | :---- | :---- | :---- | :---- |
| Area\_Privativa | SIMULAÇÃO 01 | Numérico (Float) | Variável independente que define a área habitável do projeto. | Escala diretamente a Receita Total (VGV). |
| Preco\_Venda\_M2 | SIMULAÇÃO 01 | Monetário | Premissa de precificação baseada em pesquisa de mercado local. | Determina o teto do VGV. |
| Valor\_Venal | SIMULAÇÃO 01 | Monetário | Base de cálculo tributária do lote perante a prefeitura. | Modula o custo de impostos fundiários. |
| Taxa\_ITBI | SIMULAÇÃO 01 | Percentual | Fator de tributação para aquisição de imóveis (fixado em 2%). | Eleva o custo final da rubrica Terreno. |
| Area\_Real\_Subsolo | SIMULAÇÃO 01 | Numérico (Float) | Especificação métrica de ambientes destinados a estacionamento. | Alimenta a função de equivalência de áreas. |
| Coef\_Equivalencia | SIMULAÇÕES | Array(Float) | Ponderador de custo segundo a norma ABNT NBR 12.721 (0.75, 0.60). | Define a Área Equivalente e o Custo Obra. |
| CUB\_Base | SIMULAÇÃO 01 | Monetário | Indexador econômico estadual macro (Padrão R8-A, R$ 1825.10). | Multiplicador que instiga o orçamento paramétrico. |
| Custos\_Extra\_CUB | SIMULAÇÃO 01 | Array(Monetário) | Variáveis de engenharia especial não englobadas no índice padrão. | Expande significativamente o Custo Obra final. |
| Taxa\_BDI\_Analitico | ORÇ\#1 | Percentual | Margem de lucro e despesa indireta aplicada no orçamento granular. | Infla os Custos Diretos em 20% em todas as instâncias. |
| Taxa\_BDI\_Bancario | RELATÓRIO | Percentual | Taxa exigida na planilha de conformidade de financiamento. | Distorce a apresentação orçamentária (6% vs 20%). |
| Taxa\_Corretagem | SIMULAÇÕES | Percentual | Custo associado à venda do imóvel via terceiros (5%). | Impacta as despesas de Comercialização e a Margem. |
| Taxa\_Marketing | SIMULAÇÕES | Percentual | Verba provisionada para publicidade do empreendimento (0.5%). | Reduz a Receita Líquida na rubrica de Comercialização. |
| Taxa\_Adm\_Obra | SIMULAÇÕES | Percentual | Remuneração gerencial da construtora aplicada sobre o custo base. | Representa um acréscimo de 10% no montante Opex. |
| Taxa\_Seguros | SIMULAÇÕES | Percentual | Prêmio de proteção patrimonial exigido durante a incorporação. | Transforma 0.08% do custo construtivo em passivo. |
| Carga\_Tributaria | SIMULAÇÕES | Percentual | Impostos diretos agregados incidentes sobre as vendas totais (4%). | Compõe a saída de caixa principal em Impostos. |
| Base\_Custo\_Capital | SIMULAÇÕES | Monetário | Saldo devedor teórico que sofre incidência de encargos financeiros. | Gera o montante total de juros passivos a pagar. |
| Taxa\_Juros\_Passivos | SIMULAÇÕES | Percentual | Taxa estipulada para remuneração de credores ou custo de oportunidade. | Dita a severidade do Custo de Capital sobre o fluxo temporal. |
| Cronograma\_Vendas | SIMULAÇÕES | Array(Booleano) | Marcadores mensais indicando o início e a duração da absorção de capital. | Aplaina a curva de ingressos de caixa linearmente. |
| Cronograma\_Obras | SIMULAÇÕES | Array(Booleano) | Marcadores de execução física ditando a ativação de saídas. | Força a descapitalização linear sem aderência à Curva S. |
| Composicao\_SINAPI | ORÇ\#1 | Chave Alfanumérica | Identificador único de serviço ou material referenciado nacionalmente. | Atribui custo unitário exato de M.O. e Material. |

## **ETAPA 5 — OUTPUTS FINAIS**

A maturação do modelo processa a enorme massa de variáveis em indicadores de síntese. A extração dos outputs finais revela a saúde da tese de investimento. O cenário detalhado foca na principal instância validada do documento.

### **Receita Total (Valor Geral de Vendas Nominal)**

O cume da linha de receitas representa o ingresso pecuniário máximo previsto na alienação integral das unidades produzidas. A fórmula matemática aplicada independe do valor temporal do dinheiro e é construída pelo simples produto arquitetônico e mercadológico: a área privativa da unidade (trezentos metros) multiplicada pela precificação do metro quadrado estipulada (quatorze mil reais). O resultado extraído ascende a quatro milhões e duzentos mil reais.1 A sensibilidade deste módulo é extremamente alta, visto que qualquer contração no valor de mercado por restrições de crédito imobiliário na região de Florianópolis colapsa inteiramente a capacidade de pagamento das obrigações assumidas pelo projeto.2

### **EBITDA e Resultado Operacional Líquido**

O indicador de desempenho operacional é obtido após o expurgo das despesas construtivas e das taxas intrínsecas ao negócio. O algoritmo do modelo processa a subtração em cascata: a Receita de Vendas é subtraída pelo custo agregado do terreno, da obra (incluindo as taxas de administração), das aprovações legais, das corretagens, dos prêmios de seguro, da carga tributária e do montante alocado para cobrir o custo de capital.1 O escrutínio analítico demonstra um resultado operacional profundamente deficitário, materializado em uma perda estrutural projetada de dois milhões, novecentos e trinta e quatro mil reais.1 Este output depende maciçamente da indexação do CUB e do volume de capital investido em itens extraordinários, indicando um erro na formulação do produto imobiliário.

### **Margem de Rentabilidade**

A margem exprime a porção percentual retida pelos incorporadores. A fórmula explícita é o quociente entre o Resultado Operacional Líquido e a Receita Total (VGV).1 O motor deduziu a relação decimal de menos zero vírgula seis nove oito seis, o que corresponde a uma margem de rentabilidade severamente negativa de quase setenta por cento sobre o faturamento.1 O cenário indica uma desconexão fatal entre a expectativa de capital a ser gerado por uma casa unifamiliar e a estrutura onerosa de custos comparada à construção de edifícios multifamiliares de grande porte.

### **VPL (Valor Presente Líquido), TIR e Payback**

Os pilares clássicos da análise de investimento ancoram-se no comportamento temporal do dinheiro. O método do Valor Presente Líquido exige o desconto dos saldos líquidos mensais projetados retrocedendo-os ao momento zero por meio de uma Taxa Mínima de Atratividade (TMA). Quando as entradas atuais superam as saídas atualizadas, o projeto exibe viabilidade intrínseca.5 A Taxa Interna de Retorno (TIR) seria computada na resolução da equação polinomial onde o Valor Presente Líquido atinge zero.8 O Payback calcularia o mês exato onde a curva de caixa atinge o *breakeven*.7

A realidade mecânica do documento periciado é contundente: os algoritmos de VPL e TIR encontram-se omitidos dos sumários ou matematicamente inviabilizados.1 Em modelos de simulação Excel, a invocação da função de TIR sobre uma série de saídas de capital onde as entradas não são suficientes para inverter o sinal cumulativo do fluxo de caixa resulta inevitavelmente em erros de convergência algébrica (erros do tipo \#NUM\!). Como a viabilidade básica desaba quase três milhões de reais em perda nominal, o projeto nunca recupera seu capital, tornando o cálculo de Payback inexistente e o retorno um mero abismo conceitual.9

## **ETAPA 6 — RISCOS E PONTOS CRÍTICOS ESTRUTURAIS**

A replicação cega desta estrutura para um ambiente de produção acarreta a propagação de patologias lógicas gravíssimas. A inspeção arquitetural elucida as seguintes falhas que classificam a ferramenta atual como de alto risco auditável:

**Divergência Crônica de Motores de Custos (Shadow Data)** O modelo padece de uma esquizofrenia financeira aguda. O painel principal de simulação de viabilidade apura o custo de obras embasado em parâmetros estatísticos do Custo Unitário Básico (CUB), cravando um teto orçamentário de pouco mais de quatro milhões e quatrocentos mil reais.1 Inadvertidamente, uma aba oculta de orçamentação granular compila exaustivamente as tabelas de referência do SINAPI para calcular a mesma obra, alcançando a impressionante soma de seis milhões e cento e noventa e oito mil reais.1 A inexistência de vínculos sintáticos que force a comunicação entre a teoria do CUB e a realidade do orçamento gera uma dissonância de um milhão e setecentos mil reais que, na atual formatação, jamais alertaria o investidor.

**Duplicidade Paramétrica e Hardcoding Punitivo** O documento manifesta inserções forçadas de valores não parametrizados (hardcoding) em taxas estruturais. A aba de análise do SINAPI aplica uma taxa de vinte por cento a título de Bonificação e Despesas Indiretas sobre os insumos basais para fechar o preço final de venda.1 Paradoxalmente, o relatório desenhado para equalização de crédito e fiscalização de conformidade bancária exibe uma célula congelada apontando para um BDI impositivo de seis por cento.1 A submissão destas documentações para obtenção de financiamentos criaria uma ruptura sistêmica de integridade, expondo a incorporação a sanções de compliance ou desaprovação de crédito imediata.

**Dependências Frágeis (A Síndrome do \#REF\!)** O relatório de apresentação da Proposta de Cronograma de Investimento (PCI) serve como a ponte essencial entre a orçamentação detalhada e a realidade da linha do tempo. No entanto, ele encontra-se em um estado completo de ruína relacional, atulhado de erros lógicos que impedem o rastreamento das células em arrays críticos como a extração de avanços físico e financeiro.1 O rompimento destes links indica manipulação manual irresponsável da base de dados, exclusão de abas intermediárias fundamentais ou incompatibilidades crônicas com ferramentas modernas de matrizes tridimensionais, resultando na morte do relatório analítico mais importante do arquivo.1

**Assimetria de Projeção Temporal Linear** O modelo atua sob o dogma ineficaz de que todos os custos executivos e receitas de vendas distribuem-se de maneira matemática plana, consumindo fatias lineares do orçamento mês após mês em períodos engessados de doze meses.1 A dinâmica imobiliária e de engenharia pesada obedece à distribuição normal de probabilidade ou "Curva S", onde a exigência de capital é esparsa nas fundações, explode na elevação de superestruturas e atenua nos acabamentos.2 A supressão dessa dinâmica altera artificialmente o momento do desembolso, mascarando o instante da exposição máxima ao risco de alavancagem e corrompendo as taxas nominais de custo de dívida alocadas sobre os picos e vales do fluxo financeiro.

**Opacidade no Algoritmo de Capital** A seção consolidada reporta uma despesa contábil de capital estimada em mais de quatrocentos e sessenta e seis mil reais. Este passivo oneroso é originado de uma base sintética declarada de um milhão e trezentos e cinquenta e quatro mil reais, incidindo juros à alíquota de dois e meio por cento por doze meses.1 A origem desta base financeira e os métodos explícitos do regime de juros empregados estão nebulosos. Presume-se o agrupamento contábil do terreno e dos aportes inaugurais, caracterizando uma prática rudimentar e inflexível de modelagem de alavancagem de dívidas que seria reprovada em qualquer auditoria independente ou de custódia institucional.1

## **ETAPA 7 — GUIA TÉCNICO E CHECKLIST DE RECONSTRUÇÃO DO MOTOR EM CÓDIGO**

Para que engenheiros de software e arquitetos de dados transcrevam a complexidade enredada deste arquivo estático em uma aplicação escalável baseada em web ou em microsserviços analíticos, o seguinte guia arquitetônico de implementação sistêmica é rigorosamente impositivo.

### **Entidades de Domínio Necessárias (Esquema de Dados Normalizado)**

A fragmentação informacional da planilha eletrônica deverá ser congregada e encapsulada em um modelo de Entidade-Relacionamento rigoroso:

* Project\_Entity: Repositório central de metadados, congregando nomecciones, limites temporais, endereço ("Florianópolis/SC") e referências de tipologia.  
* Typology\_Matrix: Tabela orientada a armazenar características independentes, tais como as áreas privativas de unidades, valores de conversão (VGV por metro) e coeficientes de eficiência.  
* Parametric\_Rules\_Engine: Mapeamento das regras de ABNT NBR 12.721, possuindo como atributos as tipologias de ambiente ("Garagem", "Terraços") e os vetores estritos que impõem redução na área construtiva (0.75, 0.60).  
* Economic\_Indices\_Log: Tabela versionada e indexada no tempo armazenando histórico de Custo Unitário Básico (CUB), permitindo a inflação dinâmica de custos de engenharia.3  
* Analytical\_SINAPI\_Composition: O coração recursivo da orçamentação bottom-up. Esta estrutura exigirá auto-relação para emular a hierarquia entre os níveis macro e micro (n1 interagindo até n4), fragmentando explicitamente o custo unitário entre os domínios de Material, Labor e Equipment.  
* Fiscal\_Parameter\_Profile: Tabela de isolamento de variáveis macroeconômicas. Variáveis cruciais percentuais, como taxas de administração, prêmios de apólice de seguros patrimoniais e índices imutáveis de transações imobiliárias e fiscais.

### **Regras de Cálculo Essenciais e Algoritmos de Processamento**

A migração da arquitetura exige a construção de *pipelines* isolados e assíncronos:

1. **Refatoração do Algoritmo Paramétrico (Top-Down):** O back-end deve somar as áreas reais arquitetônicas e invocar a tabela de regras normativas para o rebaixamento de metragem. A área equivalente resultante não poderá interagir com instâncias locais do CUB, mas deverá acionar o endpoint externo para aferir a precificação correta.  
2. **Motor de Árvore de Custos SINAPI (Bottom-Up):** A aplicação terá de possuir uma rotina iterativa de percurso em árvore (Tree Traversal). O algoritmo percorrerá as ramificações de insumos base calculando: (Valor\_Mão\_de\_Obra \+ Valor\_Material) \* Quantidade\_Projetada. Em vez de embutir os cálculos na célula, o software exigirá que a incidência de BDI aja globalmente sobre todos os nós da árvore na etapa final de persistência.  
3. **Algoritmo de Conformidade Bancária (API Substituta do RELATÓRIO):** Uma API dedicada deverá ser gerada com o intento único de unificar as rubricas contábeis fragmentadas do SINAPI dentro das macrocategorias restritas aceitas pelas instituições (fundações, superestrutura, fechamentos). Este motor emitirá o cronograma consolidado da aba "PCI Adotado" sem o risco da deleção de metadados.  
4. **Distribuição Temporal por Modelagem Estocástica:** As rotinas devem substituir as distribuições lineares engessadas na matriz da planilha. O back-end invocará algoritmos estatísticos normais (aplicação de curvas S gaussianas e fatores de *Gompertz*) para orquestrar o adensamento financeiro da obra ao longo da variável independente de tempo.

### **Ordem Correta e Obrigatória de Processamento Algorítmico**

A inobservância da dependência algébrica causal provocará deadlocks nos nós do sistema financeiro. O processamento ocorrerá estritamente na seguinte fila metodológica:

1. Ingestão e Processamento da Geometria (Área Equivalente) e Indexação.  
2. Derivação do Faturamento Potencial (VGV) na extremidade final do horizonte simulado.  
3. Aquisição de Terreno parametrizando tributos como gatilhos no período basal (![][image1]).  
4. Invocação separada dos Motores Paramétricos de Obra e da Agregação de Custos Analíticos.  
5. Cálculo em lote das obrigações secundárias atreladas a percentuais fixos (Comissões de comercialização, prêmios de seguro retidos e impostos provisionados sobre VGV faturado).  
6. Construção da matriz temporal cruzando as despesas processadas com os algoritmos de dispersão na curva de meses projetada.  
7. Composição do *Cash-Flow* e extração matemática do endividamento cumulativo, disparando a função do polinômio atuarial para as raízes da Taxa Interna de Retorno e Valor Presente Líquido.

### **Pontos Críticos que Exigem Testes Unitários Sistêmicos**

Para resguardar a sanidade da reengenharia estrutural e proteger os gestores contra deficiências passadas, a esteira de desenvolvimento deverá impor exaustivas asserções algorítmicas no ambiente automatizado de *Continuous Integration*:

* **test\_area\_equivalence\_normalization:** Validar se a fração arquitetônica convertida pelo fator 0.75 gera a exatidão métrica final sem perda de flutuação nas casas decimais exigidas pelos softwares de modelagem civil.  
* **test\_bdi\_propagation\_consistency:** Assegurar que a premissa percentual indexada na configuração global unificada seja propagada incontestavelmente em todos os nós componentes do orçamento final, garantindo que aberrações entre 6% e 20% não coexistam na apresentação executiva.  
* **test\_irr\_and\_npv\_convergence\_on\_stress:** A biblioteca encarregada de extrair o retorno dos investimentos (como métodos de Newton-Raphson para raízes polinomiais) deverá ser bombardeada com matrizes massivas de caixa negativo e positivo, garantindo que o sistema reporte diagnosticamente inviabilidades sem travar em *loops* infinitos quando as projeções se mostrarem cronicamente deprimentes, como aquelas visualizadas ao longo da Simulação 01 do atual documento original.

#### **Referências citadas**

1. PLANILHA ANÁLISE DE VIABILIDADE.xlsx  
2. Real Estate Modeling & Financial Models Using Excel \- The WallStreet School, acessado em fevereiro 23, 2026, [https://www.thewallstreetschool.com/blog/real-estate-modelling/](https://www.thewallstreetschool.com/blog/real-estate-modelling/)  
3. Planilha Abnt NBR 12721 | PDF \- Scribd, acessado em fevereiro 23, 2026, [https://www.scribd.com/document/775685594/Planilha-Abnt-Nbr-12721](https://www.scribd.com/document/775685594/Planilha-Abnt-Nbr-12721)  
4. How to Create a Real Estate Investment Model in Excel \- Financial Edge, acessado em fevereiro 23, 2026, [https://www.fe.training/free-resources/real-estate/how-to-create-a-real-estate-investment-model-in-excel/](https://www.fe.training/free-resources/real-estate/how-to-create-a-real-estate-investment-model-in-excel/)  
5. Métodos de Avaliação de Investimentos: VPL, TIR e Payback \- Romeo Bravo, acessado em fevereiro 23, 2026, [https://romeobravo.com.br/metodos-de-avaliacao-de-investimentos-vpl-tir-e-payback/](https://romeobravo.com.br/metodos-de-avaliacao-de-investimentos-vpl-tir-e-payback/)  
6. Análise de Investimentos no Excel | PDF | Valor Presente líquido | Taxa interna de retorno, acessado em fevereiro 23, 2026, [https://www.scribd.com/presentation/514110532/Analise-de-Viabilidade-Economica-Financeira-no-Excel](https://www.scribd.com/presentation/514110532/Analise-de-Viabilidade-Economica-Financeira-no-Excel)  
7. VPL, TIR, Lucratividade e Payback no Excel \- Baixe a planilha na descrição \- YouTube, acessado em fevereiro 23, 2026, [https://www.youtube.com/watch?v=2qk0SUj29-o](https://www.youtube.com/watch?v=2qk0SUj29-o)  
8. ESTUDO DE VIABILIDADE DE INVESTIMENTO ATRAVÉS DO PAYBACK, VPL E TIR \- Atena Editora, acessado em fevereiro 23, 2026, [https://atenaeditora.com.br/catalogo/dowload-post/84807](https://atenaeditora.com.br/catalogo/dowload-post/84807)  
9. How to Calculate Discounted Payback in Excel (Step by Step) \- YouTube, acessado em fevereiro 23, 2026, [https://www.youtube.com/watch?v=qHXg8Eeqoe8](https://www.youtube.com/watch?v=qHXg8Eeqoe8)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAaCAYAAABVX2cEAAABOElEQVR4Xu2TLUgEQRSAn+CB4pUDQfwJ1gtyQQ2C0WrSIBgN1y2CRQ0XRTCI2MToTxH7dasmEQxWo0VB/d69XZid2XVuLt8HX5i38/fevBUZMijTeIwXEc9wC8dtWTlt/BJboJM38RB/8DGL7eATvuJUb1UJY3iLG15cD/jFjhNbxXuccGIFmnglxauP4o3Yzdac+DKeOOOA7UyXSXzGd5xz4uu464wD9Mo1L6bpfOODWBly6t64L/R0rde+/yGVqnoNhD67Pr9fr5wRnBcrRTTlPMU9/wOsYBcb2Vg3vJOKJo6lqAd1xR5CWcQXsfYKmMU3qU7xVMLNdK72Xw/d9UMstTLP84lwKeFmn2L9l0z0Zikk1SyG/5r6SPrjl75mDO2xAzzCBbzGpcKMRHTDGWxJH0075H/+AJEgQgi3sCx4AAAAAElFTkSuQmCC>
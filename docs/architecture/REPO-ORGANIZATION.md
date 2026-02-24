# Organização recomendada do repositório Bautt SIGMA

- Separar engine, delta e api como serviços independentes.
- Serviços Python com layout `src/<package>` para imports estáveis.
- Manter wrappers temporários para retrocompatibilidade.
- Testes em `tests/` fora do `src/`.

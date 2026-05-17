# agente_medico — Motor de Inferência PCMSO

Motor determinístico que transforma um PGR estruturado em matriz de exames ocupacionais (PCMSO), seguindo o protocolo clínico da Dra. Carolini Polesso (Seconci-GO).

**Status atual:** estrutura inicial — sessão 002.A — sem lógica de inferência.

## O que existe agora

- `motor/tipos.py` — todos os dataclasses e enums do domínio
- `motor/protocolo.py` — carregamento e validação estrutural dos YAMLs do protocolo
- `protocolo/` — vocabulário (agentes, cargos, exames, EPIs), regras e regimes (ANAC)

## O que vem a seguir

- **002.B** — predicados primitivos + estágio gates
- **002.C** — emissão + consolidação com 2-3 regras reais
- **002.D** — pipeline completo + teste de integração Viverde

## Executar testes

```
pytest agente_medico/tests/
```

## Verificar tipos (mypy strict)

```
mypy --strict agente_medico/motor/tipos.py
```

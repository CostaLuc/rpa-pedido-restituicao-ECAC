# Diretório de Status

Este diretório armazena os arquivos de status das empresas processadas pelo RPA e dados bancários.

## Estrutura

```
db/status/
  ├── [grupo1]/
  │     ├── [empresa1].xlsx
  │     ├── [empresa2].xlsx
  │     └── ...
  ├── [grupo2]/
  │     ├── [empresa1]/
  │     │     └── comp_[timestamp].xlsx
  │     ├── [empresa1].xlsx
  │     └── ...
  └── ...
```

## Arquivos de Status

Cada arquivo `[empresa].xlsx` contém:

1. Registros de processamentos RPA
2. Metadados como CPF e dados bancários
3. Status de cada processamento (pendente, concluído, etc.)

## Arquivos de Competência

Cada empresa pode ter um diretório
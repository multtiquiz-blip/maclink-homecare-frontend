# MacLink HomeCare

App em PWA (tablet e celular) para cuidadores de idosos no Brasil.
Registro com um toque, plano de cuidado em peças, painel de pacientes,
gráfico consolidado, PDF como prontuário defensável, IA local opcional.

## Princípios (não negociáveis)

1. Segurança = código fixo. A IA nunca dispara alerta nem marca tarefa.
2. Nenhum número clínico no código; limites por idoso, cadastrados por enfermeiro.
3. O app nunca afirma algo que não aconteceu.
4. Registro não se apaga, se corrige com motivo.
5. Emergência e Falar nunca ficam atrás de login.
6. Dextro só com enfermagem verificada; só enfermeiro libera tarefas.
7. Só dados fictícios em desenvolvimento.
8. Em dúvida, pergunte.

## Stack

- **Frontend:** PWA em Svelte
- **Backend:** Python + FastAPI (local no aparelho; nuvem depois)
- **Banco local:** SQLite no aparelho
- **Banco nuvem:** Neon (PostgreSQL serverless)
- **PDF:** WeasyPrint (HTML→PDF)
- **IA:** Whisper Small/Base/Tiny (STT) + Qwen 0.5B opcional + áudios pré-gravados

## Estrutura

- `frontend/` — PWA em Svelte
- `backend/nucleo/` — regras puras (sem UI, sem HTTP)
- `backend/api/` — rotas FastAPI
- `backend/dados/` — SQLite + migrações
- `backend/ia/` — camada opcional (Whisper, roteador)
- `docs/` — decisões, perfis, PDF, LGPD
- `deploy/` — como rodar em cada ambiente

## Status

Em construção. Piloto na casa da vó da Rose.

## Licença

Proprietária. Todos os direitos reservados.

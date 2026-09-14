# 🎯 Agente de Procura de Emprego — Portugal (Lisboa & Remoto)

Agente inteligente e autónomo desenvolvido especificamente para o perfil de **José Manuel da Silva Monteiro** (Economista Conselheiro, Membro da OCC e detentor de CCP).

O agente pesquisa, valida e analisa ofertas de emprego ativas nos principais portais fidedignos em Portugal nos últimos 15 dias para as áreas de:
- **Direção Financeira (CFO / Diretor Financeiro / Controller)**
- **Consultoria Económica e Estratégica**
- **Assessoria de Administração**
- **Ensino e Explicações de Economia / Finanças / Contabilidade** (incluindo ofertas em **Part-Time**)
- **Compliance e Risco Financeiro**

---

## 🚀 Como Executar

Para correr o agente novamente e atualizar as ofertas:

```bash
cd /Users/josemonteiro/.gemini/antigravity/scratch/job-hunter-agent
./run.sh
```

Ou especificando outro caminho de CV:
```bash
./run.sh /Users/josemonteiro/Downloads/CV_Jose_Monteiro_2026.pdf
```

---

## 📊 Relatórios Gerados

Após cada execução, o agente gera:
1. **[relatorio_vagas.html](file:///Users/josemonteiro/.gemini/antigravity/scratch/job-hunter-agent/relatorio_vagas.html)**: Dashboard visual moderno e interativo. Pode abri-lo no browser com filtros dinâmicos por Part-Time, Remoto e Score de Compatibilidade, e botões com links diretos para cada anúncio.
2. **[relatorio_vagas.md](file:///Users/josemonteiro/.gemini/antigravity/scratch/job-hunter-agent/relatorio_vagas.md)**: Relatório completo em Markdown para consulta rápida ou arquivo.

---

## ⚙️ Configurações (`config.yaml`)

Pode ajustar no ficheiro `config.yaml`:
- **Dias máximos de publicação** (padrão: `15 dias`).
- **Palavras-chave e perfis de pesquisa**.
- **Portais ativos** (Net-Empregos, Sapo Emprego, ITJobs, Alerta Emprego, LinkedIn).
- **Exclusões geográficas** (garantindo exclusivamente o concelho de Lisboa ou trabalho Remoto).

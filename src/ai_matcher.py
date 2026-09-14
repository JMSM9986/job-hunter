import os
import re
from typing import List, Dict, Any, Tuple
from .models import JobOffer, CVProfile

class AIMatcher:
    """Motor de inteligência para resumo de ofertas e correspondência com o CV do utilizador."""
    
    def __init__(self, cv_profile: CVProfile):
        self.cv = cv_profile
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                self.client = None

    def _determine_category(self, text: str) -> str:
        text_lower = text.lower()
        if any(w in text_lower for w in [
            "cfo", "chief financial officer", "diretor financeiro", "diretora financeira", "direção financeira",
            "finance director", "financial director", "head of finance", "financial controller", "controller financeiro",
            "senior financial controller", "finance controller", "senior controller", "fp&a", "finance manager",
            "financial manager", "diretor de finanças"
        ]):
            return "Direção Financeira (CFO)"
        elif any(w in text_lower for w in ["assessor", "administração", "administracao", "conselho", "board", "advisor", "executive advisor", "governance"]):
            return "Assessoria de Administração"
        elif any(w in text_lower for w in [
            "consultor económico", "consultoria económica", "consultor de economia", "economic consultant",
            "valuation", "transaction services", "economic advisory", "estudos económicos", "consultoria", "consultor"
        ]):
            return "Consultoria Económica"
        elif any(w in text_lower for w in ["professor", "docente"]):
            return "Professor de Economia"
        elif any(w in text_lower for w in ["explicador", "explicadores", "formador", "explicações", "explicacoes"]):
            return "Explicador de Economia e Finanças"
        return "Direção Financeira (CFO)"

    def _heuristic_match_and_summarize(self, offer: JobOffer) -> Tuple[float, str, str, List[str], str]:
        """Análise semântica e contextual avançada baseada exclusivamente nos 5 cargos pretendidos."""
        full_text = f"{offer.title} {offer.description}".lower()
        
        score = 55.0
        matched_skills = []
        category = self._determine_category(full_text)
        
        # 1. Alinhamento com Cargos Alvo e Títulos Regulados
        if any(w in full_text for w in ["economista", "economia", "ciências económicas", "consultor económico", "consultoria económica", "valuation"]):
            score += 20.0
            matched_skills.append("Economista Conselheiro (Ordem dos Economistas) & Consultoria")
            
        if any(w in full_text for w in ["diretor financeiro", "cfo", "direção financeira", "finance director", "head of finance", "financial controller", "controller financeiro", "fp&a", "finance manager"]):
            score += 22.0
            matched_skills.append("Liderança e Direção Financeira Executiva (CFO)")
            
        if any(w in full_text for w in ["assessor", "administração", "board", "conselho", "governance"]):
            score += 20.0
            matched_skills.append("Assessoria ao Conselho de Administração & Gestão Estratégica")
            
        if any(w in full_text for w in ["professor", "docente", "formador", "explicador", "ccp"]):
            score += 20.0
            matched_skills.append("Docência / Explicações em Economia e Finanças com CCP")
            
        if any(w in full_text for w in ["crédito", "risco", "compliance", "portefólio"]):
            score += 10.0
            matched_skills.append("25+ anos de Carreira e Gestão de Portefólio no Setor Financeiro")

        # Deteção refinada de Part-Time / Prestação de Serviços
        if any(w in full_text for w in ["part-time", "part time", "parcial", "avença", "prestação de serviços", "prestacao de servicos", "explicador", "explicadores", "horas", "pós-laboral", "pos-laboral"]):
            offer.is_part_time = True

        # Bónus para Part-Time se a vaga for part-time (conforme solicitado)
        if offer.is_part_time:
            score += 8.0

        # Bónus de Senioridade Executiva
        if any(w in full_text for w in ["diretor", "diretora", "head of", "cfo", "chief", "responsável", "coordenador", "sénior", "senior", "assessor", "consultor sénior"]):
            score += 10.0
            matched_skills.append("Nível Executivo / Sénior (25+ anos)")

        # Penalização drástica para posições de nível inicial inadequadas a perfil executivo
        if any(w in full_text for w in ["júnior", "junior", "estágio", "estagio", "trainee", "recém-licenciado"]):
            score -= 50.0

        # Normalização do score (máx 98%, mín 20%)
        score = min(98.0, max(20.0, score))
        
        # Resumo executivo da vaga
        regime_str = "Part-Time" if offer.is_part_time else "Full-Time"
        if offer.is_remote:
            regime_str += " | Remoto / Híbrido"
        else:
            regime_str += f" | Presencial ({offer.location})"
            
        summary = (
            f"Oportunidade para {offer.title} na empresa {offer.company}. "
            f"Regime: {regime_str}. Foco na área de {category}. "
            f"Anúncio publicado há {offer.published_days_ago} dia(s)."
        )
        
        rationale = (
            f"Forte alinhamento com a sua experiência de 25+ anos no setor financeiro. "
            f"Pontos chave identificados: {', '.join(matched_skills[:3]) if matched_skills else 'Gestão e liderança executiva'}."
        )
        
        return round(score, 1), summary, rationale, matched_skills, category

    def analyze_offer(self, offer: JobOffer) -> JobOffer:
        """Processa a oferta atribuindo resumo, fit score e justificação."""
        # Tenta usar a API do Gemini se estiver disponível
        if self.client:
            try:
                prompt = f"""
És um consultor sénior de carreira executiva em Portugal.
Analisa a seguinte oferta de emprego face ao CV em formato ATS de José Manuel da Silva Monteiro:

CV CANDIDATO:
- 25+ anos setor financeiro, Economista Conselheiro (Ordem dos Economistas), Ordem dos Contabilistas Certificados (OCC), CCP (Formador).
- Ex-Coordenador de Unidade de Transição (Santander/Popular), Portfolio Manager, Financial Crime & Compliance Analyst.
- Licenciatura em Gestão, Formação executiva em Decisão em Risco (Nova FCT), Sustentabilidade (Católica), Estratégia (ISEG/Harvard).

OFERTA:
Título: {offer.title}
Empresa: {offer.company}
Local: {offer.location} (Remoto: {offer.is_remote}, Part-time: {offer.is_part_time})
Descrição: {offer.description[:800]}

Produz em formato texto estrito (linhas separadas):
SCORE: [número entre 0 e 100]
CATEGORIA: [Direção Financeira | Consultoria Económica | Assessoria de Administração | Ensino & Explicações | Risco & Compliance]
RESUMO: [Resumo executivo de 2 frases em Português de Portugal destacando missão e regime]
RATIONALE: [1 frase explicando o porquê de se adequar ao perfil do Dr. José Monteiro]
"""
                resp = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                text = resp.text
                
                score_match = re.search(r'SCORE:\s*(\d+)', text)
                cat_match = re.search(r'CATEGORIA:\s*(.+)', text)
                res_match = re.search(r'RESUMO:\s*(.+)', text)
                rat_match = re.search(r'RATIONALE:\s*(.+)', text)
                
                if score_match:
                    offer.fit_score = float(score_match.group(1))
                else:
                    offer.fit_score = 75.0
                    
                offer.category_fit = cat_match.group(1).strip() if cat_match else self._determine_category(offer.title)
                offer.summary = res_match.group(1).strip() if res_match else offer.description[:200]
                offer.match_rationale = rat_match.group(1).strip() if rat_match else "Perfil compatível com a senioridade financeira."
                return offer
            except Exception:
                # Fallback para o modo heurístico em caso de falha de API ou quota
                pass

        score, summary, rationale, matched_skills, category = self._heuristic_match_and_summarize(offer)
        offer.fit_score = score
        offer.summary = summary
        offer.match_rationale = rationale
        offer.matched_skills = matched_skills
        offer.category_fit = category
        return offer

    def rank_and_process(self, offers: List[JobOffer]) -> List[JobOffer]:
        """Processa todas as ofertas e ordena decrescentemente pelo Fit Score."""
        processed = [self.analyze_offer(o) for o in offers]
        processed.sort(key=lambda x: x.fit_score, reverse=True)
        return processed

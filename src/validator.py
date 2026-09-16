import re
from typing import List, Tuple
import httpx
from .models import JobOffer

class JobValidator:
    """Valida requisitos estritos: < 15 dias, anúncio ativo e localização Lisboa/Remoto."""
    
    EXPIRED_PATTERNS = [
        r"an[uú]ncio expirado",
        r"oferta expirada",
        r"esta vaga j[aá] n[aã]o se encontra dispon[ií]vel",
        r"an[uú]ncio inativo",
        r"oferta n[aã]o encontrada",
        r"an[uú]ncio j[aá] foi desativado",
        r"candidaturas encerradas",
        r"vaga preenchida",
        r"o an[uú]ncio que procura j[aá] n[aã]o",
        r"job is no longer available",
        r"this job has expired",
        r"404 - not found",
        r"p[aá]gina n[aã]o encontrada"
    ]

    # Outras cidades e distritos de Portugal que devem ser excluídos a menos que seja Remoto/Online
    OTHER_CITIES = [
        "barcelos", "guimarães", "guimaraes", "felgueiras", "porto", "braga", "coimbra",
        "aveiro", "leiria", "faro", "viseu", "vila real", "viana do castelo", "bragança",
        "braganca", "castelo branco", "guarda", "portalegre", "évora", "evora", "beja",
        "funchal", "madeira", "açores", "ponta delgada", "famalicão", "famalicao", "santo tirso",
        "trofa", "maia", "matosinhos", "gaia", "vila nova de gaia", "espinho", "santa maria da feira",
        "ovar", "marinha grande", "caldas da rainha", "torres vedras", "alenquer", "cartaxo",
        "santarém", "santarem", "tomar", "abrantes", "peniche", "figueira da foz", "covilhã", "covilha",
        "entroncamento", "santiago do cacém", "santiago cacem", "sines", "santo andré", "santo andre",
        "elvas", "portalegre", "ponte de sor", "fátima", "fatima", "ourém", "ourem", "rio maior",
        "loulé", "loule", "albufeira", "portimão", "portimao", "lagos", "tavira", "olhão", "olhao",
        "quarteira", "vilamoura", "silves", "lagos", "vila do conde", "póvoa de varzim", "povoa de varzim",
        "oliveira do bairro", "anadia", "águeda", "agueda", "albergaria", "mealhada", "estarreja", "ilhavo", "ílhavo"
    ]

    IRRELEVANT_SUBJECTS = [
        "físico-química", "fisico-quimica", "fisico-química", "física", "fisica", "química", "quimica",
        "fq", "1ºciclo", "1º ciclo", "1 ciclo", "primária", "geometria", "geometria descritiva",
        "ciências naturais", "biologia", "geologia", "geografia", "história", "português", "francês",
        "inglês", "filosofia", "artes visuais", "educação física", "desporto", "música", "infantil",
        "educador de infância"
    ]

    # Padrões estritamente excluídos: Contabilistas e Vendas / Comercial
    EXCLUDED_ROLES_PATTERNS = [
        # Contabilidade e Contabilistas
        r"\bcontabilista(s)?\b",
        r"\bcontabilidade\b",
        r"\baccountant(s)?\b",
        r"\baccounting\b",
        r"\bt[eé]cnico(a)?\s+(de\s+)?contabilidade",
        r"\badministrativo(a)?\s+(de\s+)?contabilidade",
        r"\brespons[aá]vel\s+(de\s+)?contabilidade",
        r"\bgabinete\s+de\s+contabilidade",
        r"\bpayroll\b",
        r"\bsal[aá]rios\b",
        r"\bcontas\s+a\s+pagar\b",
        r"\bcontas\s+a\s+receber\b",
        r"\btoc\b",
        
        # Vendas, Comercial, Lojas e Retalho
        r"\bvendas?\b",
        r"\bcomercia(l|is)\b",
        r"\bsales\b",
        r"\bvendedor(a)?\b",
        r"\bloja(s)?\b",
        r"\bretalho\b",
        r"\bretail\b",
        r"\bbalc[aã]o\b",
        r"\bdistribui[cç][aã]o\s+alimentar\b",
        r"\bcall\s+center\b",
        r"\btelemarketing\b",
        r"\bapoio\s+ao\s+cliente\b",
        r"\bcustomer\s+support\b",
        r"\bcustomer\s+service\b",
        r"\bcompras\b",
        r"\bcomprador(a)?\b",
        r"\bprocurement\b",
        r"\bbusiness\s+develop(er|ment)\b",
        r"\baccount\s+manager\b",
        r"\bgestor(a)?\s+de\s+clientes\b",
        r"\bgestor(a)?\s+comercial\b",
        r"\bdelegado(a)?\s+comercial\b",
        r"\bpromotor(a)?\b",
        r"\bcategory\s+manager\b"
    ]

    def __init__(self, max_days: int = 15, exclude_suburbs: List[str] = None):
        self.max_days = max_days
        self.exclude_suburbs = [s.lower() for s in (exclude_suburbs or [])]
        self.client = httpx.Client(
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8"
            },
            timeout=10.0,
            follow_redirects=True
        )

    def is_valid_location(self, offer: JobOffer) -> bool:
        """Garante que a localização é estritamente Lisboa (concelho) ou Remoto."""
        loc_lower = offer.location.lower()
        title_lower = offer.title.lower()
        
        # Se indicar claramente online / remoto / teletrabalho, é aceite
        is_remote_explicit = (
            offer.is_remote or 
            "remoto" in loc_lower or "teletrabalho" in loc_lower or "remote" in loc_lower or
            "online" in title_lower or "remoto" in title_lower or "teletrabalho" in title_lower
        )
        if is_remote_explicit:
            offer.is_remote = True
            return True

        has_lisbon_in_title = "lisboa" in title_lower or "lisbon" in title_lower

        # Se o título indicar outra cidade do país sem mencionar Lisboa no título (ex: "- Felgueiras", "- Bragança"), descartar
        for city in self.OTHER_CITIES:
            if re.search(r'\b' + re.escape(city) + r'\b', title_lower) and not has_lisbon_in_title:
                return False

        # Se a localização for noutra cidade/distrito do país sem mencionar Lisboa, descartar
        is_lisbon_explicit = "lisboa" in loc_lower or "lisbon" in loc_lower or has_lisbon_in_title
        if not is_lisbon_explicit:
            for city in self.OTHER_CITIES:
                if re.search(r'\b' + re.escape(city) + r'\b', loc_lower):
                    return False

        # Se for presencial e mencionar concelhos periféricos da AML (fora de Lisboa cidade), descartar
        for suburb in self.exclude_suburbs:
            if re.search(r'\b' + re.escape(suburb) + r'\b', loc_lower) or re.search(r'\b' + re.escape(suburb) + r'\b', title_lower):
                return False

        # Deve indicar Lisboa ou Portugal
        if is_lisbon_explicit or loc_lower == "portugal":
            return True
            
        return False

    def is_relevant_subject(self, offer: JobOffer) -> bool:
        """Garante que a vaga de docência/explicação/ensino é de Economia, Gestão, Finanças ou CCP."""
        title_lower = offer.title.lower()
        for irr in self.IRRELEVANT_SUBJECTS:
            if irr in title_lower:
                # Se mencionar também economia ou gestão ou finanças, analisa
                if not any(k in title_lower for k in ["economia", "gestão", "gestao", "finanças", "financas", "contabilidade"]):
                    return False
        return True

    def is_within_timeframe(self, offer: JobOffer) -> bool:
        """Verifica se foi publicado nos últimos 15 dias."""
        return 0 <= offer.published_days_ago <= self.max_days

    def is_active_online(self, offer: JobOffer) -> Tuple[bool, str]:
        """Testa rapidamente o link com HEAD ou GET rápido de timeout reduzido (2.5s)."""
        # LinkedIn guest API apenas lista vagas ativas. Evitar HEAD/GET que possa originar HTTP 999 ou rate limit
        if "linkedin.com" in offer.url:
            return True, "Ativa (LinkedIn oficial)"

        try:
            # Tenta primeiro HEAD (muito mais rápido, sem descarregar corpo da página)
            resp = self.client.head(offer.url, timeout=2.5)
            if resp.status_code == 200:
                return True, "Ativa"
            elif resp.status_code in [404, 410]:
                return False, f"Página inexistente (HTTP {resp.status_code})"
                
            # Fallback para GET leve se o servidor não suportar HEAD
            resp = self.client.get(offer.url, timeout=2.5)
            if resp.status_code != 200:
                return False, f"Status HTTP {resp.status_code}"
                
            page_text = resp.text.lower()
            for pattern in self.EXPIRED_PATTERNS:
                if re.search(pattern, page_text):
                    return False, "Anúncio expirado/fechado na página de origem"
                    
            return True, "Ativa"
        except Exception:
            # Se der timeout ou proteção de bot, mantém como ativa se a recolha da lista for de hoje/recente
            return True, "Ativa (validação rápida)"

    def is_excluded_role(self, offer: JobOffer) -> bool:
        """Exclui taxativamente ofertas de contabilistas ou vendas/comercial."""
        title_lower = offer.title.lower()

        # Funções estritamente proibidas no cargo:
        # 1. Contabilistas / Guarda-livros / Técnicos de Contabilidade / Faturação / Cobranças
        accountant_titles = [
            r"\bcontabilista(s)?\b",
            r"\bt[eé]cnico(a)?\s+(de\s+)?contabilidade",
            r"\badministrativo(a)?\s+(de\s+)?contabilidade",
            r"\bassistente\s+(de\s+)?contabilidade",
            r"\bgabinete\s+de\s+contabilidade",
            r"\baccountant(s)?\b",
            r"\bstaff\s+accountant\b",
            r"\bjunior\s+accountant\b",
            r"\bsenior\s+accountant\b",
            r"\bchief\s+accountant\b",
            r"\bgeneral\s+ledger\b",
            r"\bbookkeeper\b",
            r"\bbookkeeping\b",
            r"\baccounts\s+payable\b",
            r"\baccounts\s+receivable\b",
            r"\bpayroll\b",
            r"\bprocessamento\s+salarial\b",
            r"\bcontas\s+a\s+pagar\b",
            r"\bcontas\s+a\s+receber\b",
            r"\bfatura[cç][aã]o\b",
            r"\bcobran[cç]as?\b",
            r"\btoc\b"
        ]
        for pattern in accountant_titles:
            if re.search(pattern, title_lower, re.IGNORECASE):
                return True

        # 2. Vendas / Comercial / Lojas / Atendimento
        sales_titles = [
            r"\bvendas?\b",
            r"\bcomercia(l|is)\b",
            r"\bsales\b",
            r"\bvendedor(a)?\b",
            r"\bloja(s)?\b",
            r"\bretalho\b",
            r"\bretail\b",
            r"\bbalc[aã]o\b",
            r"\bcaixa\b",
            r"\bcall\s+center\b",
            r"\btelemarketing\b",
            r"\bapoio\s+ao\s+cliente\b",
            r"\bcustomer\s+support\b",
            r"\bcustomer\s+service\b",
            r"\bpromotor(a)?\b",
            r"\bdelegado(a)?\s+comercial\b",
            r"\bbusiness\s+develop(er|ment)\b",
            r"\baccount\s+manager\b",
            r"\bgestor(a)?\s+de\s+clientes\b",
            r"\bgestor(a)?\s+comercial\b"
        ]
        for pattern in sales_titles:
            if re.search(pattern, title_lower, re.IGNORECASE):
                return True

        # 3. Estágios e Trainees (incompatíveis com perfil executivo sénior de 25+ anos)
        trainee_titles = [
            r"\btrainee(s)?\b",
            r"\best[aá]gio(s)?\b",
            r"\bestagi[aá]rio(a)?\b",
            r"\binternship(s)?\b"
        ]
        for pattern in trainee_titles:
            if re.search(pattern, title_lower, re.IGNORECASE):
                return True

        # Se for função de explicações/docência que mencione assuntos irrelevantes
        is_tutor = any(w in title_lower for w in ["explicador", "explicadores", "professor", "docente", "formador"])
        if is_tutor and not any(w in (title_lower + " " + offer.description).lower() for w in ["economia", "gestão", "gestao", "finanças", "financas"]):
            return True

        return False

    def is_target_role(self, offer: JobOffer) -> bool:
        """Garante que a vaga pertence estritamente a um dos 5 cargos definidos pelo utilizador."""
        title_lower = offer.title.lower()
        desc_lower = (offer.title + " " + offer.description).lower()

        # 1. Consultoria Económica & Regulação / Risco Financeiro
        is_consulting = (
            any(w in title_lower for w in [
                "consultor económico", "consultor economico", "consultoria económica", "consultoria economica",
                "consultor de economia", "análise económica", "analise economica", "economic consultant",
                "economic advisory", "valuation & advisory", "transaction services", "estudos económicos",
                "estudos economicos", "health economics", "risk & regulation", "risk & regulatory",
                "capital management & reporting", "securities services consulting", "compliance & financial crime",
                "financial advisory", "consulting & transformation"
            ]) or
            ("consultor" in title_lower and any(w in desc_lower for w in ["economia", "económico", "economico", "estudos económicos", "estratégia", "banca", "financeiro"])) or
            ("consultoria" in title_lower and any(w in desc_lower for w in ["economia", "económico", "economico", "financeira", "estratégia", "banca"]))
        )

        # 2. Direção Financeira (CFO / Diretor Financeiro) & Funções Financeiras de Topo na Banca
        is_cfo_director = (
            any(w in title_lower for w in [
                "cfo", "chief financial officer", "diretor financeiro", "diretora financeira",
                "direção financeira", "direcao financeira", "head of finance", "finance director",
                "financial director", "diretor de finanças", "diretora de finanças", "diretor administrativo e financeiro",
                "fp&a", "fp-a", "corporate finance", "responsável de corporate finance", "responsavel de corporate finance",
                "financial controller", "controller financeiro", "senior financial controller",
                "finance controller", "senior controller", "capital markets controller", "capital market",
                "capital markets", "p&l reconciliation", "corporate banking", "investment banking", "banca de investimento",
                "finance manager", "financial manager", "responsável financeiro", "responsavel financeiro",
                "controlo de gestão e governação", "controlo de gestão", "financial control", "credit risk stress testing"
            ])
        )

        # 3. Assessoria de Administração
        is_board_advisor = (
            any(w in title_lower for w in [
                "assessor da administração", "assessor da administracao",
                "assessor de administração", "assessor de administracao",
                "assessoria de administração", "assessoria de administracao",
                "assessoria da administração", "assessoria da administracao",
                "board advisor", "executive advisor", "assessor do conselho",
                "assessor de conselho", "assessor da direção", "assessor de direção",
                "assessor executivo", "assessoria executiva", "corporate advisor",
                "board member", "conselho de administração", "non-executive director",
                "corporate governance"
            ])
        )

        # 4. Professor de Economia
        is_professor_econ = (
            ("professor" in title_lower or "docente" in title_lower) and
            any(w in (title_lower + " " + desc_lower) for w in ["economia", "ciências económicas", "ciencias economicas", "macroeconomia", "microeconomia"])
        )

        # 5. Explicador (Economia / Finanças / Ensino Superior)
        is_tutor = (
            "explicador" in title_lower or "explicadores" in title_lower or
            ("explicações" in title_lower and any(w in desc_lower for w in ["economia", "finanças", "financas", "ensino superior"])) or
            ("formador" in title_lower and any(w in desc_lower for w in ["economia", "finanças", "financas", "ccp"]))
        )

        return is_consulting or is_cfo_director or is_board_advisor or is_professor_econ or is_tutor

    def filter_offers(self, offers: List[JobOffer]) -> List[JobOffer]:
        """Validação ultrarrápida: primeiro filtros locais de memória, depois verificação concorrente de rede."""
        import concurrent.futures

        # 1. Filtros instantâneos em memória (elimina logo anúncios fora de prazo, fora de Lisboa ou não conformes)
        pre_filtered = []
        for o in offers:
            if not self.is_within_timeframe(o):
                continue
            if not self.is_valid_location(o):
                continue
            if not self.is_relevant_subject(o):
                continue
            if self.is_excluded_role(o):
                continue
            if not self.is_target_role(o):
                continue
            pre_filtered.append(o)

        if not pre_filtered:
            return []

        # 2. Verificação concorrente de links em paralelo (4 workers controlados para não saturar CPU na cloud)
        valid = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_offer = {executor.submit(self.is_active_online, o): o for o in pre_filtered}
            for future in concurrent.futures.as_completed(future_to_offer):
                offer = future_to_offer[future]
                try:
                    is_active, _ = future.result()
                    if is_active:
                        valid.append(offer)
                except Exception:
                    valid.append(offer)

        return valid

    def close(self):
        self.client.close()

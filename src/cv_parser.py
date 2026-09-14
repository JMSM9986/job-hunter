import re
from pathlib import Path
from typing import Optional, List, Dict, Any
import pypdf
from .models import CVProfile

class ATSCVParser:
    """Parser de CV estruturado segundo o formato ATS (Applicant Tracking System)."""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Ficheiro de CV não encontrado: {file_path}")
            
    def extract_text(self) -> str:
        suffix = self.file_path.suffix.lower()
        if suffix == ".pdf":
            reader = pypdf.PdfReader(str(self.file_path))
            pages_text = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            return "\n".join(pages_text)
        elif suffix in [".txt", ".md"]:
            return self.file_path.read_text(encoding="utf-8", errors="ignore")
        elif suffix == ".docx":
            try:
                import docx
                doc = docx.Document(str(self.file_path))
                return "\n".join([p.text for p in doc.paragraphs if p.text])
            except ImportError:
                raise ImportError("Biblioteca python-docx necessária para ler ficheiros .docx.")
        else:
            raise ValueError(f"Formato não suportado: {suffix}. Utilize PDF, DOCX, TXT ou MD.")

    def parse(self) -> CVProfile:
        cache_path = self.file_path.parent / ".cv_profile_cache.json"
        try:
            current_mtime = self.file_path.stat().st_mtime
            if cache_path.exists():
                import json
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                if cached.get("_mtime") == current_mtime:
                    return CVProfile(
                        name=cached["name"],
                        email=cached["email"],
                        phone=cached["phone"],
                        location=cached["location"],
                        linkedin=cached["linkedin"],
                        professional_title=cached["professional_title"],
                        summary=cached["summary"],
                        specializations=cached["specializations"],
                        certifications=cached["certifications"],
                        experience_years=cached.get("experience_years", 25),
                        experiences=[],
                        education=[],
                        competencies=cached.get("competencies", []),
                        raw_text=cached.get("raw_text", "")
                    )
        except Exception:
            pass

        raw_text = self.extract_text()
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        
        # 1. Nome e Contactos (Típico do cabeçalho ATS)
        name = lines[0] if lines else "Candidato"
        
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', raw_text)
        email = email_match.group(0) if email_match else ""
        
        phone_match = re.search(r'(\+?\d{2,3}\s*)?(\d{3}\s*\d{3}\s*\d{3}|\d{9})', raw_text)
        phone = phone_match.group(0) if phone_match else ""
        
        linkedin_match = re.search(r'(linkedin\.com/in/[\w-]+)', raw_text)
        linkedin = linkedin_match.group(1) if linkedin_match else ""
        
        # Subtítulo profissional
        prof_title = lines[1] if len(lines) > 1 else "Especialista Financeiro e de Gestão"
        
        # 2. Secções ATS canónicas
        sections: Dict[str, List[str]] = {
            "perfil": [],
            "especializacoes": [],
            "certificacoes": [],
            "experiencia": [],
            "formacao": [],
            "competencias": [],
            "outros": []
        }
        
        current_section = "perfil"
        for line in lines[2:]:
            upper_line = line.upper()
            if "PERFIL PROFISSIONAL" in upper_line or "RESUMO" in upper_line:
                current_section = "perfil"
                continue
            elif "ÁREAS DE ESPECIALIZAÇÃO" in upper_line or "ESPECIALIZAÇÃO" in upper_line:
                current_section = "especializacoes"
                continue
            elif "CERTIFICAÇÕES" in upper_line or "ASSOCIAÇÕES" in upper_line:
                current_section = "certificacoes"
                continue
            elif "EXPERIÊNCIA PROFISSIONAL" in upper_line or "EXPERIÊNCIA" in upper_line:
                current_section = "experiencia"
                continue
            elif "FORMAÇÃO ACADÉMICA" in upper_line or "EDUCAÇÃO" in upper_line:
                current_section = "formacao"
                continue
            elif "COMPETÊNCIAS" in upper_line or "OUTRAS COMPETÊNCIAS" in upper_line or "SKILLS" in upper_line:
                current_section = "competencias"
                continue
            elif "ATIVIDADES" in upper_line or "INTERESSES" in upper_line:
                current_section = "outros"
                continue
                
            sections[current_section].append(line)
            
        summary = " ".join(sections["perfil"])
        specializations = [line.lstrip("•-* ").strip() for line in sections["especializacoes"] if line.strip()]
        certifications = [line.lstrip("•-* ").strip() for line in sections["certificacoes"] if line.strip()]
        competencies = [line.lstrip("•-* ").strip() for line in sections["competencias"] if line.strip()]
        
        # Anos de experiência (inferido ou baseado nos 25 anos explícitos)
        exp_match = re.search(r'mais de (\d+)\s+anos de experiência', raw_text, re.IGNORECASE)
        experience_years = int(exp_match.group(1)) if exp_match else 25
        
        return CVProfile(
            name=name,
            email=email,
            phone=phone,
            location="Lisboa, Portugal",
            linkedin=linkedin,
            professional_title=prof_title,
            summary=summary,
            specializations=specializations,
            certifications=certifications,
            experience_years=experience_years,
            experiences=[], # detalhe preservado no raw_text e nas secções
            education=[],
            competencies=competencies,
            raw_text=raw_text
        )

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

@dataclass
class JobOffer:
    id: str
    title: str
    company: str
    location: str
    is_remote: bool
    is_part_time: bool
    publication_date: datetime
    published_days_ago: int
    url: str
    source_portal: str
    description: str = ""
    requirements: List[str] = field(default_factory=list)
    salary: Optional[str] = None
    contract_type: Optional[str] = None
    
    # Preenchido pelo Matcher:
    fit_score: float = 0.0 # 0 a 100
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    summary: str = ""
    match_rationale: str = ""
    category_fit: str = "" # "Direção Financeira", "Consultoria Económica", "Assessoria", "Ensino & Explicações"

@dataclass
class CVProfile:
    name: str
    email: str
    phone: str
    location: str
    linkedin: str
    professional_title: str
    summary: str
    specializations: List[str]
    certifications: List[str]
    experience_years: int
    experiences: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    competencies: List[str]
    raw_text: str

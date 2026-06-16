from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class PersonTarget:
    name: str
    email: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[str] = None
    # Identité
    emails_found: List[str] = field(default_factory=list)
    usernames_found: List[str] = field(default_factory=list)
    social_profiles: Dict[str, str] = field(default_factory=dict)
    # GitHub
    github_data: Dict = field(default_factory=dict)
    # Fuites
    breaches: List[Dict] = field(default_factory=list)
    # Comportement
    activity_hours: Dict = field(default_factory=dict)
    writing_style: Dict = field(default_factory=dict)
    interests: List[str] = field(default_factory=list)
    # Géolocalisation
    locations: List[Dict] = field(default_factory=list)
    exif_data: List[Dict] = field(default_factory=list)
    checkins: List[Dict] = field(default_factory=list)
    # Réseau de relations
    connections: List[Dict] = field(default_factory=list)
    family: List[Dict] = field(default_factory=list)
    # Analyse IA
    ai_summary: str = ""
    risk_score: int = 0
    correlations: List[str] = field(default_factory=list)

@dataclass
class CompanyTarget:
    domain: str
    name: Optional[str] = None
    org: Optional[str] = None
    # Infrastructure
    ips: List[str] = field(default_factory=list)
    subdomains: List[str] = field(default_factory=list)
    asn: Dict = field(default_factory=dict)
    dns_records: Dict = field(default_factory=dict)
    ssl_certs: List[Dict] = field(default_factory=list)
    # Cloud
    s3_buckets: List[str] = field(default_factory=list)
    azure_blobs: List[str] = field(default_factory=list)
    cloud_assets: List[Dict] = field(default_factory=list)
    # Shodan
    shodan_data: Dict = field(default_factory=dict)
    open_ports: List[int] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    cves: List[str] = field(default_factory=list)
    # Secrets
    exposed_secrets: List[Dict] = field(default_factory=list)
    github_data: Dict = field(default_factory=dict)
    # Employés
    employees: List[Dict] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    # Darkweb
    darkweb_mentions: List[Dict] = field(default_factory=list)
    leaked_credentials: List[Dict] = field(default_factory=list)
    # Analyse IA
    ai_summary: str = ""
    risk_score: int = 0
    correlations: List[str] = field(default_factory=list)

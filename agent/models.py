"""
Pydantic data models for the Composio 100 Apps Research Pipeline.
Defines schemas for seeds, crawl signals, predictions, verifications, and benchmarks.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class AppSeed(BaseModel):
    id: int
    name: str
    category: str
    hint: str

class CrawlSignal(BaseModel):
    has_oauth: bool = False
    has_apikey: bool = False
    has_basic_auth: bool = False
    has_bearer: bool = False
    has_graphql: bool = False
    has_rest: bool = False
    has_cli: bool = False
    has_mcp: bool = False
    has_free_tier: bool = False
    has_trial: bool = False
    has_sales_gate: bool = False
    has_pricing_wall: bool = False

class CrawlResult(BaseModel):
    valid: bool
    status_code: Optional[int] = None
    final_url: str = ""
    title: str = ""
    signals: CrawlSignal = Field(default_factory=CrawlSignal)
    error: Optional[str] = None

class AppRecord(BaseModel):
    id: int
    name: str
    category: str
    one_liner: str
    website: str
    docs_url: str
    auth_methods: List[str]
    auth_details: str
    self_serve_status: str
    self_serve_details: str
    api_surface: str
    api_breadth: str
    mcp_status: str
    buildability_verdict: str
    blocker_summary: str
    composio_fit: str
    evidence_url: str = ""
    evidence_source: str = "Official Vendor Developer Documentation"
    evidence_summary: str = ""
    confidence: float = 1.0
    needs_human_review: bool = False
    verification_status: str = "Automated Verified"
    verification_notes: Optional[str] = None

class AuditRecord(BaseModel):
    app_id: int
    name: str
    category: str
    audited_by: str
    audit_date: str
    fields_audited: List[str]
    evidence_inspected_url: str
    ground_truth_verdict: str
    ground_truth_self_serve: str
    pass1_agent_verdict: str
    pass2_agent_verdict: str
    pass1_verdict_match: bool
    pass2_verdict_match: bool
    human_rationale: str
    review_decision: str

class FieldAccuracy(BaseModel):
    verdict_acc: float
    self_serve_acc: float
    surface_acc: float
    mcp_acc: float
    overall_accuracy: float

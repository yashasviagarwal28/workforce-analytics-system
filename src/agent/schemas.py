from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
class TriageClassification(str, Enum):
    dismiss="dismiss"; escalate="escalate"; needs_more_data="needs_more_data"
class EvidenceItem(BaseModel):
    fact:str=Field(min_length=1,max_length=500); source:str=Field(min_length=1,max_length=100)
class TriageDecision(BaseModel):
    classification:TriageClassification; confidence:float=Field(ge=0,le=1); summary:str=Field(min_length=1,max_length=1200)
    evidence:List[EvidenceItem]=Field(default_factory=list); missing_information:List[str]=Field(default_factory=list)
    recommended_action:str=Field(min_length=1,max_length=500); tools_used:List[str]=Field(default_factory=list)
    model:Optional[str]=None; prompt_version:str="v1"
class TriageJobResponse(BaseModel):
    job_id:str; punch_id:str; status:str; error:Optional[str]=None
class TriageResultResponse(BaseModel):
    job_id:str; punch_id:str; status:str; decision:Optional[TriageDecision]=None; error:Optional[str]=None

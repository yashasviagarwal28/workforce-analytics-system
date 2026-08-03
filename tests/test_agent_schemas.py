import pytest
from pydantic import ValidationError
from src.agent.schemas import TriageDecision
def test_valid_decision():
 d=TriageDecision(classification="escalate",confidence=.9,summary="Unusual shift.",evidence=[{"fact":"16 hours worked","source":"current_record"}],missing_information=[],recommended_action="Human review");assert d.classification.value=="escalate"
def test_invalid_confidence():
 with pytest.raises(ValidationError):TriageDecision(classification="dismiss",confidence=2,summary="x",evidence=[],missing_information=[],recommended_action="x")

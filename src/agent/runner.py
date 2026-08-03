import json,os
from openai import OpenAI
from src.agent.prompts import SYSTEM_PROMPT_V1,build_initial_context
from src.agent.schemas import EvidenceItem,TriageDecision
from src.agent.tool_definitions import TOOLS
from src.agent.tools import execute_tool,get_flagged_record
class AgentRunError(RuntimeError):pass
class OpsPulseAgent:
    def __init__(self,model=None,max_iterations=4,max_data_tool_calls=3):
        self.model=model or os.getenv("OPENAI_MODEL","gpt-5-mini"); self.max_iterations=max_iterations; self.max_data_tool_calls=max_data_tool_calls; self.client=OpenAI()
    def triage(self,punch_id:str)->TriageDecision:
        inputs=[{"role":"system","content":SYSTEM_PROMPT_V1},{"role":"user","content":build_initial_context(get_flagged_record(punch_id))}]; used=[]; count=0
        for _ in range(self.max_iterations):
            r=self.client.responses.create(model=self.model,input=inputs,tools=TOOLS,tool_choice="auto"); inputs.extend(r.output)
            calls=[x for x in r.output if getattr(x,"type",None)=="function_call"]
            if not calls: raise AgentRunError("Model returned no function call.")
            for c in calls:
                a=json.loads(c.arguments)
                if c.name=="submit_triage_decision": return TriageDecision(classification=a["classification"],confidence=a["confidence"],summary=a["summary"],evidence=[EvidenceItem(**e) for e in a["evidence"]],missing_information=a["missing_information"],recommended_action=a["recommended_action"],tools_used=used,model=self.model,prompt_version="v1")
                count+=1
                if count>self.max_data_tool_calls: raise AgentRunError("Too many data tool calls.")
                result=execute_tool(c.name,a); used.append(c.name); inputs.append({"type":"function_call_output","call_id":c.call_id,"output":json.dumps(result)})
        raise AgentRunError("Maximum iterations exceeded.")

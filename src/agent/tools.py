from pathlib import Path
from typing import Any,Dict
import pandas as pd
PUNCHES=Path("data/processed/punches.parquet"); SCORES=Path("data/processed/anomaly_scores.parquet")
class AgentDataError(RuntimeError): pass
def _punches():
    if not PUNCHES.exists(): raise AgentDataError("Run ETL first.")
    return pd.read_parquet(PUNCHES)
def _scores():
    if not SCORES.exists(): raise AgentDataError("Run model training first.")
    return pd.read_parquet(SCORES)
def _row(row):
    out={}
    for k,v in row.to_dict().items():
        if isinstance(v,pd.Timestamp): out[k]=v.isoformat()
        elif pd.isna(v): out[k]=None
        elif hasattr(v,"item"): out[k]=v.item()
        else: out[k]=v
    return out
def get_flagged_record(punch_id:str)->Dict[str,Any]:
    m=_punches().merge(_scores()[["punch_id","anomaly_score","predicted_anomaly","reason_hint"]],on="punch_id",validate="one_to_one")
    x=m[m.punch_id==punch_id]
    if x.empty: raise AgentDataError(f"Unknown punch_id: {punch_id}")
    if not bool(x.iloc[0]["predicted_anomaly"]): raise AgentDataError("Record is not flagged.")
    return _row(x.iloc[0])
def get_employee_history(employee_id:str,days:int=90)->Dict[str,Any]:
    d=_punches().copy(); d["clock_in"]=pd.to_datetime(d["clock_in"]); d=d[d.employee_id==employee_id]
    if d.empty:return {"employee_id":employee_id,"record_count":0}
    d=d[d.clock_in>=d.clock_in.max()-pd.Timedelta(days=days)].sort_values("clock_in")
    return {"employee_id":employee_id,"days":days,"record_count":int(len(d)),"mean_worked_hours":round(float(d.worked_hours.mean()),3),"max_worked_hours":round(float(d.worked_hours.max()),3),"mean_overtime_hours":round(float(d.daily_overtime_hours.mean()),3),"overtime_shift_count":int((d.daily_overtime_hours>0).sum()),"recent_records":[_row(r) for _,r in d.tail(12).iterrows()]}
def get_department_baseline(department_id:str,days:int=90)->Dict[str,Any]:
    d=_punches().copy(); d["clock_in"]=pd.to_datetime(d["clock_in"]); d=d[d.department_id==department_id]
    if d.empty:return {"department_id":department_id,"record_count":0}
    d=d[d.clock_in>=d.clock_in.max()-pd.Timedelta(days=days)]
    return {"department_id":department_id,"days":days,"record_count":int(len(d)),"mean_worked_hours":round(float(d.worked_hours.mean()),3),"p95_worked_hours":round(float(d.worked_hours.quantile(.95)),3),"mean_overtime_hours":round(float(d.daily_overtime_hours.mean()),3),"p95_overtime_hours":round(float(d.daily_overtime_hours.quantile(.95)),3)}
def get_shift_context(punch_id:str)->Dict[str,Any]:
    d=_punches(); x=d[d.punch_id==punch_id]
    if x.empty: raise AgentDataError(f"Unknown punch_id: {punch_id}")
    return _row(x.iloc[0])
def execute_tool(name:str,args:Dict[str,Any])->Dict[str,Any]:
    if name=="get_employee_history": return get_employee_history(**args)
    if name=="get_department_baseline": return get_department_baseline(**args)
    if name=="get_shift_context": return get_shift_context(**args)
    raise AgentDataError(f"Unsupported tool: {name}")

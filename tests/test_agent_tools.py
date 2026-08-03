import pandas as pd
from src.agent import tools
def test_employee_history(monkeypatch):
 d=pd.DataFrame([{"punch_id":"P1","employee_id":"E1","department_id":"D1","clock_in":"2026-01-01T08:00:00","clock_out":"2026-01-01T17:00:00","worked_hours":9.,"daily_overtime_hours":1.,"arrival_minutes":0.,"departure_minutes":60.},{"punch_id":"P2","employee_id":"E1","department_id":"D1","clock_in":"2026-01-02T08:00:00","clock_out":"2026-01-02T16:00:00","worked_hours":8.,"daily_overtime_hours":0.,"arrival_minutes":0.,"departure_minutes":0.}]);monkeypatch.setattr(tools,"_punches",lambda:d.copy());r=tools.get_employee_history("E1",90);assert r["record_count"]==2 and r["overtime_shift_count"]==1

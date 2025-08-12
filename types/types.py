from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass
class Appointment:
    id: str
    timestamp: datetime
    patient_name: str
    mrn: str
    date: str
    time: str
    provider: str
    reason: str
    status: Literal["pending", "scheduled", "cancelled"]

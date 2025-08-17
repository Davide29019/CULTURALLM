
from typing import Any

from fastapi import HTTPException


def timeout(current_time: Any, last_active: Any, timeout_seconds: int):
    if last_active is not None:
        elapsed = current_time - last_active
        print(current_time, last_active)
        if elapsed > timeout_seconds:
            raise HTTPException(status_code=401, detail="Sessione scaduta per inattività")
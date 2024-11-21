# models.py

from typing import Optional
from pydantic import BaseModel

class ProjectData(BaseModel):
    description: str
    test_description: Optional[str] = None
    # Add other fields if necessary

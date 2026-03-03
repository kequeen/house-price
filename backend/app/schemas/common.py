from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ApiResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[dict | list] = None


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[dict]

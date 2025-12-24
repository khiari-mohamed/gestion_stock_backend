from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PaginationParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=500)

class DateRangeFilter(BaseModel):
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    magasin_id: str

class BulkDeleteRequest(BaseModel):
    ids: list[str] = Field(..., min_items=1)

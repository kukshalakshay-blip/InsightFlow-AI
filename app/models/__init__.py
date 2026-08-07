"""Pydantic models for InsightFlow-AI (example)."""
from pydantic import BaseModel


class ExampleModel(BaseModel):
    id: int
    name: str

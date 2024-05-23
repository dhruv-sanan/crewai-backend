from typing import List
from pydantic import BaseModel


class NamedUrl(BaseModel):
    name: str
    url: str


class PositionInfo(BaseModel):
    company: str
    position: str
    name: str
    blog_articles_urls: List[str]
    youtube_interviews_urls: List[NamedUrl]


class PositionInfoList(BaseModel):
    positions: List[PositionInfo]


class EmailInfo(BaseModel):
    subject: str
    content: str


class ScoreInfo(BaseModel):
    score: int
    explanation: str

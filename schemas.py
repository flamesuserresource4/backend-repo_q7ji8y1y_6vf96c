"""
Database Schemas

Define MongoDB collection schemas using Pydantic models.
Each model name (lowercased) maps to a collection name.

Examples:
- User -> "user"
- Project -> "project"
"""

from pydantic import BaseModel, Field, HttpUrl, EmailStr
from typing import List, Optional
from datetime import datetime


class Project(BaseModel):
    title: str = Field(..., description="Project title")
    slug: str = Field(..., description="Unique identifier")
    description: str = Field(..., description="Short description")
    tech: List[str] = Field(default_factory=list, description="Tech tags")
    image: Optional[HttpUrl] = Field(None, description="Cover image URL")
    repo_url: Optional[HttpUrl] = Field(None, description="GitHub repo URL")
    live_url: Optional[HttpUrl] = Field(None, description="Live demo URL")
    featured: bool = Field(default=False, description="Featured on home")
    stars: Optional[int] = Field(default=None, description="GitHub stars cache")


class Testimonial(BaseModel):
    name: str
    role: Optional[str] = None
    quote: str
    avatar: Optional[HttpUrl] = None
    company: Optional[str] = None
    highlight: Optional[bool] = False


class GuestbookEntry(BaseModel):
    name: str
    message: str
    avatar: Optional[HttpUrl] = None
    website: Optional[HttpUrl] = None


class BucketItem(BaseModel):
    title: str
    done: bool = False
    notes: Optional[str] = None


class UseItem(BaseModel):
    category: str
    name: str
    description: Optional[str] = None
    link: Optional[HttpUrl] = None


class BlogPost(BaseModel):
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: Optional[str] = None
    tags: List[str] = []
    cover_image: Optional[HttpUrl] = None
    published: bool = False
    published_at: Optional[datetime] = None


class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    message: str
    subject: Optional[str] = None
    source: Optional[str] = None

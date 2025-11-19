import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson.objectid import ObjectId
import requests

from database import db, create_document, get_documents
from schemas import Project, Testimonial, GuestbookEntry, BucketItem, UseItem, BlogPost, ContactMessage

app = FastAPI(title="Portfolio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class DBItem(BaseModel):
    id: str


def serialize_doc(doc):
    if not doc:
        return doc
    d = dict(doc)
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    return d


@app.get("/")
def root():
    return {"message": "Portfolio Backend is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": os.getenv("DATABASE_NAME") or "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["connection_status"] = "Connected"
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but error: {str(e)[:80]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response


# Projects
@app.get("/api/projects")
def list_projects(featured: Optional[bool] = None, limit: int = 50):
    query = {}
    if featured is not None:
        query["featured"] = featured
    items = get_documents("project", query, limit)
    return [serialize_doc(i) for i in items]


@app.post("/api/projects")
def create_project(project: Project):
    _id = create_document("project", project)
    return {"id": _id}


# Testimonials
@app.get("/api/testimonials")
def list_testimonials(limit: int = 50):
    items = get_documents("testimonial", {}, limit)
    return [serialize_doc(i) for i in items]


@app.post("/api/testimonials")
def create_testimonial(item: Testimonial):
    _id = create_document("testimonial", item)
    return {"id": _id}


# Guestbook
@app.get("/api/guestbook")
def list_guestbook(limit: int = 100):
    items = get_documents("guestbookentry", {}, limit)
    return [serialize_doc(i) for i in items]


@app.post("/api/guestbook")
def sign_guestbook(entry: GuestbookEntry):
    _id = create_document("guestbookentry", entry)
    return {"id": _id}


# Bucket List
@app.get("/api/bucket")
def list_bucket(limit: int = 100):
    items = get_documents("bucketitem", {}, limit)
    return [serialize_doc(i) for i in items]


@app.post("/api/bucket")
def add_bucket(item: BucketItem):
    _id = create_document("bucketitem", item)
    return {"id": _id}


# Uses
@app.get("/api/uses")
def list_uses(limit: int = 200):
    items = get_documents("useitem", {}, limit)
    return [serialize_doc(i) for i in items]


@app.post("/api/uses")
def add_use(item: UseItem):
    _id = create_document("useitem", item)
    return {"id": _id}


# Blog
@app.get("/api/blog")
def list_blog(published: Optional[bool] = True, limit: int = 50):
    query = {}
    if published is not None:
        query["published"] = published
    items = get_documents("blogpost", query, limit)
    return [serialize_doc(i) for i in items]


@app.get("/api/blog/{slug}")
def get_blog(slug: str):
    items = get_documents("blogpost", {"slug": slug}, 1)
    if not items:
        raise HTTPException(status_code=404, detail="Post not found")
    return serialize_doc(items[0])


@app.post("/api/blog")
def create_blog(post: BlogPost):
    _id = create_document("blogpost", post)
    return {"id": _id}


# Contact
@app.post("/api/contact")
def contact(message: ContactMessage):
    _id = create_document("contactmessage", message)
    return {"id": _id, "status": "received"}


# GitHub helpers
GITHUB_API = "https://api.github.com"


@app.get("/api/stats/github")
def github_stats(user: str):
    headers = {"Accept": "application/vnd.github+json"}
    # Optional: token to raise rate limits if provided
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    user_resp = requests.get(f"{GITHUB_API}/users/{user}", headers=headers, timeout=10)
    if user_resp.status_code != 200:
        raise HTTPException(status_code=user_resp.status_code, detail=user_resp.text)

    # Sum stars across first 100 repos (most cases sufficient)
    repos_resp = requests.get(
        f"{GITHUB_API}/users/{user}/repos?per_page=100&sort=updated",
        headers=headers,
        timeout=10,
    )
    stars = 0
    if repos_resp.status_code == 200:
        for r in repos_resp.json():
            stars += int(r.get("stargazers_count", 0))

    data = user_resp.json()
    return {
        "followers": data.get("followers", 0),
        "public_repos": data.get("public_repos", 0),
        "stars": stars,
    }


@app.get("/api/github/repos")
def github_repos(user: str, limit: int = 12):
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(
        f"{GITHUB_API}/users/{user}/repos?per_page={min(limit, 100)}&sort=updated",
        headers=headers,
        timeout=10,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    repos = resp.json()
    mapped = [
        {
            "name": r.get("name"),
            "full_name": r.get("full_name"),
            "description": r.get("description"),
            "html_url": r.get("html_url"),
            "language": r.get("language"),
            "stargazers_count": r.get("stargazers_count"),
            "forks_count": r.get("forks_count"),
            "topics": r.get("topics", []),
            "homepage": r.get("homepage"),
        }
        for r in repos
    ]
    return mapped


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

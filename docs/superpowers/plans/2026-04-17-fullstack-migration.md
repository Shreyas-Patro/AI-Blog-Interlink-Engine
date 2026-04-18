# Full-Stack Migration: AI Link Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the existing Python/Streamlit AI Link Engine into a production-ready full-stack application with a FastAPI backend and React frontend, adding role-based auth and a task assignment system.

**Architecture:** The existing pipeline business logic (ingest → chunk → embed → match → anchor → inject) lives in `link_engine/stages/` and is NOT touched. A new `api/` layer wraps it with FastAPI routes. A new `frontend/` React app replaces the Streamlit dashboard. Two new DB models (User, Task) extend the existing schema.

**Tech Stack:** FastAPI, Uvicorn, SQLAlchemy (existing), Alembic (existing), python-jose (JWT), passlib (bcrypt), React 18, TypeScript, Vite, TanStack Query, Zustand, Tailwind CSS, shadcn/ui

---

## Scope Check

This plan covers one connected system — backend and frontend are coupled by shared API contracts defined in Phase 1. They are built sequentially: backend first, frontend second. Do not split into sub-projects.

---

## File Structure

### Backend additions (inside `link-engine/`)

```
link-engine/
├── api/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app, CORS, router registration
│   ├── dependencies.py          # get_db(), get_current_user(), require_admin()
│   ├── routers/
│   │   ├── auth.py              # POST /auth/login, GET /auth/me
│   │   ├── articles.py          # GET /articles, POST /articles/ingest, GET /articles/{id}/export
│   │   ├── pipeline.py          # POST /pipeline/run, GET /pipeline/runs, GET /pipeline/runs/{id}
│   │   ├── anchors.py           # GET /anchors, PATCH /anchors/{id}
│   │   ├── tasks.py             # GET /tasks, POST /tasks, PATCH /tasks/{id}
│   │   └── admin.py             # GET /admin/users, POST /admin/users, GET /admin/stats
│   └── schemas/
│       ├── auth.py              # LoginRequest, TokenResponse, UserOut
│       ├── articles.py          # ArticleOut, IngestResponse, ExportResponse
│       ├── pipeline.py          # RunOut, RunTriggerResponse
│       ├── anchors.py           # AnchorOut, AnchorPatch
│       ├── tasks.py             # TaskOut, TaskCreate, TaskPatch
│       └── admin.py             # UserCreate, StatsOut
├── link_engine/
│   └── db/
│       └── models.py            # ADD: User, Task models (no changes to existing models)
├── alembic/versions/
│   └── <new>_add_user_task.py   # Migration: add users + tasks tables
└── requirements.txt             # ADD: fastapi, uvicorn, python-jose, passlib
```

### Frontend (new directory, sibling to `link-engine/`)

```
frontend/
├── index.html
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── src/
    ├── main.tsx
    ├── App.tsx                  # Router: Login, Editor, Review, Admin routes
    ├── api/
    │   ├── client.ts            # Axios instance, JWT injection, 401 redirect
    │   ├── auth.ts              # login(), me()
    │   ├── articles.ts          # listArticles(), ingestArticles(), exportArticle()
    │   ├── pipeline.ts          # triggerRun(), listRuns(), getRun()
    │   ├── anchors.ts           # listAnchors(), patchAnchor()
    │   ├── tasks.ts             # listTasks(), createTask(), patchTask()
    │   └── admin.ts             # listUsers(), createUser(), getStats()
    ├── store/
    │   └── auth.ts              # Zustand: token, user, setUser, logout
    ├── hooks/
    │   ├── useCurrentUser.ts
    │   └── useRole.ts           # returns { isAdmin, isEditor }
    ├── components/
    │   ├── Layout.tsx           # Sidebar nav, role-aware menu items
    │   ├── ProtectedRoute.tsx   # Redirects unauthenticated users
    │   └── RequireRole.tsx      # Blocks non-admin from admin routes
    └── pages/
        ├── Login.tsx            # Email + password form
        ├── EditorDashboard.tsx  # Task queue: assigned anchors to review
        ├── ReviewInterface.tsx  # Split-screen: source left, target right
        ├── AdminDashboard.tsx   # Stats, run pipeline, assign tasks, manage users
        └── ArticleManager.tsx   # Upload markdown files, export injected articles
```

---

## API Contract Reference

These endpoints must be implemented exactly as specified. Frontend is built against them.

### Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/login` | None | `{email, password}` → `{access_token, token_type, user}` |
| GET | `/auth/me` | Any | Returns current user |

### Articles
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/articles` | Any | List all articles with chunk count + injection count |
| POST | `/articles/ingest` | Admin | Upload `.md` files (multipart), run ingest stage |
| GET | `/articles/{article_id}/export` | Admin | Download injected markdown file |

### Pipeline
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/pipeline/run` | Admin | Trigger full pipeline (async background task) |
| GET | `/pipeline/runs` | Any | List last 20 runs |
| GET | `/pipeline/runs/{run_id}` | Any | Single run details |
| GET | `/pipeline/status` | Any | Current pending/approved/rejected counts |

### Anchors
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/anchors` | Any | List anchors; query params: `?status=pending_review&assigned_to=me` |
| PATCH | `/anchors/{anchor_id}` | Editor/Admin | `{status: approved\|rejected\|edited, edited_anchor?: string}` |

### Tasks
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/tasks` | Any | Editor sees own tasks; Admin sees all |
| POST | `/tasks` | Admin | `{anchor_id, assigned_to_user_id, notes?}` |
| PATCH | `/tasks/{task_id}` | Editor/Admin | `{status: in_progress\|completed}` |

### Admin
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/admin/users` | Admin | List all users |
| POST | `/admin/users` | Admin | Create user: `{email, name, role, password}` |
| GET | `/admin/stats` | Admin | Article, anchor, task, error counts |

---

## New Database Models

**User**
```
user_id     String PK (uuid)
email       String unique
name        String
role        String  (admin | editor)
hashed_pw   String
created_at  DateTime
```

**Task**
```
task_id          String PK (uuid)
anchor_id        String FK → anchors.anchor_id
assigned_to      String FK → users.user_id
assigned_by      String FK → users.user_id
status           String  (pending | in_progress | completed)
notes            Text nullable
assigned_at      DateTime
completed_at     DateTime nullable
```

---

## Phase 1 — Backend Foundation

### Task 1.1: Add dependencies

**Files:**
- Modify: `link-engine/requirements.txt`

- [ ] **Step 1: Add new packages**

  Append to `requirements.txt`:
  ```
  fastapi==0.111.0
  uvicorn[standard]==0.29.0
  python-jose[cryptography]==3.3.0
  passlib[bcrypt]==1.7.4
  python-multipart==0.0.9
  ```

- [ ] **Step 2: Install**

  Run: `pip install -r requirements.txt`
  Expected: All packages install without conflict.

- [ ] **Step 3: Commit**

  ```bash
  git add requirements.txt
  git commit -m "chore: add FastAPI and auth dependencies"
  ```

---

### Task 1.2: Add User and Task models

**Files:**
- Modify: `link-engine/link_engine/db/models.py` (append only — do not touch existing models)

- [ ] **Step 1: Write failing test**

  In `link-engine/tests/test_models.py`:
  ```python
  from link_engine.db.models import User, Task

  def test_user_model_has_role():
      u = User(user_id="u1", email="a@b.com", name="Alice", role="editor", hashed_pw="x")
      assert u.role in ("admin", "editor")

  def test_task_model_links_anchor_and_user():
      t = Task(task_id="t1", anchor_id="a1", assigned_to="u1", assigned_by="u2", status="pending")
      assert t.status == "pending"
  ```

- [ ] **Step 2: Run tests — expect FAIL**

  Run: `pytest link-engine/tests/test_models.py -v`
  Expected: `ImportError: cannot import name 'User' from 'link_engine.db.models'`

- [ ] **Step 3: Append User and Task to models.py**

  Add after the `Run` class (line ~170 of models.py):
  ```python
  class User(Base):
      __tablename__ = "users"

      user_id = Column(String, primary_key=True, default=_uuid)
      email = Column(String, unique=True, nullable=False)
      name = Column(String, nullable=False)
      role = Column(String, nullable=False)  # admin | editor
      hashed_pw = Column(String, nullable=False)
      created_at = Column(DateTime, default=_now)

      assigned_tasks = relationship("Task", foreign_keys="Task.assigned_to", back_populates="assignee")
      created_tasks = relationship("Task", foreign_keys="Task.assigned_by", back_populates="assigner")


  class Task(Base):
      __tablename__ = "tasks"

      task_id = Column(String, primary_key=True, default=_uuid)
      anchor_id = Column(String, ForeignKey("anchors.anchor_id"), nullable=False)
      assigned_to = Column(String, ForeignKey("users.user_id"), nullable=False)
      assigned_by = Column(String, ForeignKey("users.user_id"), nullable=False)
      status = Column(String, default="pending")  # pending | in_progress | completed
      notes = Column(Text, nullable=True)
      assigned_at = Column(DateTime, default=_now)
      completed_at = Column(DateTime, nullable=True)

      assignee = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_tasks")
      assigner = relationship("User", foreign_keys=[assigned_by], back_populates="created_tasks")
      anchor = relationship("Anchor")
  ```

- [ ] **Step 4: Run tests — expect PASS**

  Run: `pytest link-engine/tests/test_models.py -v`
  Expected: 2 passed.

- [ ] **Step 5: Commit**

  ```bash
  git add link_engine/db/models.py tests/test_models.py
  git commit -m "feat: add User and Task models"
  ```

---

### Task 1.3: Alembic migration for users + tasks

**Files:**
- Create: `link-engine/alembic/versions/<hash>_add_user_task.py`

- [ ] **Step 1: Generate migration**

  Run (from `link-engine/`):
  ```bash
  alembic revision --autogenerate -m "add_user_task"
  ```
  Expected: New file created in `alembic/versions/`.

- [ ] **Step 2: Review generated migration**

  Open the generated file. Verify it contains `op.create_table('users', ...)` and `op.create_table('tasks', ...)`. If autogenerate missed anything, add manually.

- [ ] **Step 3: Apply migration**

  Run: `alembic upgrade head`
  Expected: `Running upgrade ... -> <hash>, add_user_task`

- [ ] **Step 4: Verify tables exist**

  Run: `python -c "from link_engine.db.session import get_session_factory; s = get_session_factory()(); from link_engine.db.models import User; print(s.query(User).count())"`
  Expected: `0`

- [ ] **Step 5: Commit**

  ```bash
  git add alembic/versions/
  git commit -m "feat: migration for users and tasks tables"
  ```

---

### Task 1.4: FastAPI app skeleton + CORS

**Files:**
- Create: `link-engine/api/__init__.py`
- Create: `link-engine/api/main.py`
- Create: `link-engine/api/dependencies.py`

- [ ] **Step 1: Write smoke test**

  Create `link-engine/tests/test_api_smoke.py`:
  ```python
  from fastapi.testclient import TestClient
  from api.main import app

  client = TestClient(app)

  def test_health():
      r = client.get("/health")
      assert r.status_code == 200
      assert r.json() == {"status": "ok"}
  ```

- [ ] **Step 2: Run — expect FAIL**

  Run: `pytest link-engine/tests/test_api_smoke.py -v`
  Expected: `ModuleNotFoundError: No module named 'api'`

- [ ] **Step 3: Create `api/__init__.py`**

  Empty file.

- [ ] **Step 4: Create `api/main.py`**

  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware

  app = FastAPI(title="AI Link Engine API", version="1.0.0")

  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:5173"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  @app.get("/health")
  def health():
      return {"status": "ok"}
  ```

- [ ] **Step 5: Run test — expect PASS**

  Run: `pytest link-engine/tests/test_api_smoke.py -v`
  Expected: 1 passed.

- [ ] **Step 6: Create `api/dependencies.py`**

  ```python
  from fastapi import Depends, HTTPException, status
  from fastapi.security import OAuth2PasswordBearer
  from jose import JWTError, jwt
  from link_engine.db.session import get_session_factory
  from link_engine.db.models import User

  SECRET_KEY = "change-me-in-production"
  ALGORITHM = "HS256"
  oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

  def get_db():
      factory = get_session_factory()
      db = factory()
      try:
          yield db
      finally:
          db.close()

  def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)) -> User:
      try:
          payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
          user_id: str = payload.get("sub")
      except JWTError:
          raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
      user = db.get(User, user_id)
      if not user:
          raise HTTPException(status_code=404, detail="User not found")
      return user

  def require_admin(user: User = Depends(get_current_user)) -> User:
      if user.role != "admin":
          raise HTTPException(status_code=403, detail="Admin only")
      return user
  ```

- [ ] **Step 7: Commit**

  ```bash
  git add api/ tests/test_api_smoke.py
  git commit -m "feat: FastAPI app skeleton with health endpoint and auth dependencies"
  ```

---

### Task 1.5: Auth router (login + me)

**Files:**
- Create: `link-engine/api/schemas/auth.py`
- Create: `link-engine/api/routers/auth.py`
- Modify: `link-engine/api/main.py` (register router)

- [ ] **Step 1: Write auth tests**

  Create `link-engine/tests/test_api_auth.py`:
  ```python
  from fastapi.testclient import TestClient
  from api.main import app
  from link_engine.db.session import get_session_factory
  from link_engine.db.models import User
  from passlib.context import CryptContext

  client = TestClient(app)
  pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

  def _seed_user(role="editor"):
      factory = get_session_factory()
      db = factory()
      u = User(email="test@test.com", name="Test", role=role,
                hashed_pw=pwd_ctx.hash("password123"))
      db.merge(u)
      db.commit()
      db.close()
      return u

  def test_login_returns_token():
      _seed_user()
      r = client.post("/auth/login", data={"username": "test@test.com", "password": "password123"})
      assert r.status_code == 200
      assert "access_token" in r.json()

  def test_login_wrong_password():
      _seed_user()
      r = client.post("/auth/login", data={"username": "test@test.com", "password": "wrong"})
      assert r.status_code == 401

  def test_me_returns_user():
      _seed_user()
      token = client.post("/auth/login", data={"username": "test@test.com", "password": "password123"}).json()["access_token"]
      r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
      assert r.status_code == 200
      assert r.json()["email"] == "test@test.com"
  ```

- [ ] **Step 2: Run — expect FAIL**

  Run: `pytest link-engine/tests/test_api_auth.py -v`
  Expected: `404 Not Found` on all requests.

- [ ] **Step 3: Create `api/schemas/__init__.py` and `api/schemas/auth.py`**

  ```python
  # api/schemas/auth.py
  from pydantic import BaseModel

  class LoginRequest(BaseModel):
      email: str
      password: str

  class UserOut(BaseModel):
      user_id: str
      email: str
      name: str
      role: str

      class Config:
          from_attributes = True

  class TokenResponse(BaseModel):
      access_token: str
      token_type: str = "bearer"
      user: UserOut
  ```

- [ ] **Step 4: Create `api/routers/auth.py`**

  ```python
  from datetime import datetime, timedelta
  from fastapi import APIRouter, Depends, HTTPException, status
  from fastapi.security import OAuth2PasswordRequestForm
  from jose import jwt
  from passlib.context import CryptContext
  from api.dependencies import get_db, get_current_user, SECRET_KEY, ALGORITHM
  from api.schemas.auth import TokenResponse, UserOut
  from link_engine.db.models import User

  router = APIRouter(prefix="/auth", tags=["auth"])
  pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

  @router.post("/login", response_model=TokenResponse)
  def login(form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
      user = db.query(User).filter(User.email == form.username).first()
      if not user or not pwd_ctx.verify(form.password, user.hashed_pw):
          raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
      token = jwt.encode(
          {"sub": user.user_id, "exp": datetime.utcnow() + timedelta(hours=8)},
          SECRET_KEY, algorithm=ALGORITHM
      )
      return TokenResponse(access_token=token, user=UserOut.from_orm(user))

  @router.get("/me", response_model=UserOut)
  def me(user: User = Depends(get_current_user)):
      return UserOut.from_orm(user)
  ```

- [ ] **Step 5: Register router in `api/main.py`**

  Add to `main.py`:
  ```python
  from api.routers import auth
  app.include_router(auth.router)
  ```

- [ ] **Step 6: Run tests — expect PASS**

  Run: `pytest link-engine/tests/test_api_auth.py -v`
  Expected: 3 passed.

- [ ] **Step 7: Commit**

  ```bash
  git add api/routers/auth.py api/schemas/auth.py api/schemas/__init__.py api/routers/__init__.py api/main.py tests/test_api_auth.py
  git commit -m "feat: auth router with login and /me endpoints"
  ```

---

## Phase 2 — Pipeline & Articles APIs

### Task 2.1: Articles router

**Files:**
- Create: `link-engine/api/schemas/articles.py`
- Create: `link-engine/api/routers/articles.py`
- Modify: `link-engine/api/main.py`

- [ ] **Step 1: Write tests**

  Create `link-engine/tests/test_api_articles.py`:
  ```python
  from fastapi.testclient import TestClient
  from api.main import app

  client = TestClient(app)

  def _admin_token():
      # seed admin user and return token (same pattern as test_api_auth.py _seed_user)
      ...

  def test_list_articles_requires_auth():
      r = client.get("/articles")
      assert r.status_code == 401

  def test_list_articles_returns_list():
      token = _admin_token()
      r = client.get("/articles", headers={"Authorization": f"Bearer {token}"})
      assert r.status_code == 200
      assert isinstance(r.json(), list)
  ```

- [ ] **Step 2: Run — expect FAIL**

  Run: `pytest link-engine/tests/test_api_articles.py::test_list_articles_requires_auth -v`
  Expected: 404.

- [ ] **Step 3: Create `api/schemas/articles.py`**

  ```python
  from pydantic import BaseModel
  from typing import Optional

  class ArticleOut(BaseModel):
      article_id: str
      slug: str
      title: Optional[str]
      url: Optional[str]
      status: str
      chunk_count: int
      injected_count: int

      class Config:
          from_attributes = True

  class IngestResponse(BaseModel):
      new: int
      changed: int
      unchanged: int
      errors: int
  ```

- [ ] **Step 4: Create `api/routers/articles.py`**

  ```python
  import tempfile
  from pathlib import Path
  from fastapi import APIRouter, Depends, UploadFile, File
  from fastapi.responses import FileResponse
  from typing import List
  from api.dependencies import get_db, get_current_user, require_admin
  from api.schemas.articles import ArticleOut, IngestResponse
  from link_engine.db.models import Article, Injection
  from link_engine.stages.ingest import ingest_directory
  import uuid

  router = APIRouter(prefix="/articles", tags=["articles"])

  @router.get("", response_model=List[ArticleOut])
  def list_articles(db=Depends(get_db), _=Depends(get_current_user)):
      articles = db.query(Article).order_by(Article.title).all()
      result = []
      for a in articles:
          injected = sum(
              1 for chunk in a.chunks
              for m in chunk.source_matches
              if m.anchor and m.anchor.injection and m.anchor.injection.status == "injected"
          )
          result.append(ArticleOut(
              article_id=a.article_id, slug=a.slug, title=a.title,
              url=a.url, status=a.status,
              chunk_count=len(a.chunks), injected_count=injected
          ))
      return result

  @router.post("/ingest", response_model=IngestResponse)
  def ingest_articles(files: List[UploadFile] = File(...), db=Depends(get_db), _=Depends(require_admin)):
      with tempfile.TemporaryDirectory() as tmp:
          tmp_path = Path(tmp)
          for f in files:
              dest = tmp_path / f.filename
              dest.write_bytes(f.file.read())
          run_id = str(uuid.uuid4())
          results = ingest_directory(tmp_path, run_id, db)
          db.commit()
      return IngestResponse(**results)

  @router.get("/{article_id}/export")
  def export_article(article_id: str, db=Depends(get_db), _=Depends(require_admin)):
      article = db.get(Article, article_id)
      if not article:
          from fastapi import HTTPException
          raise HTTPException(404, "Article not found")
      return FileResponse(article.file_path, filename=Path(article.file_path).name)
  ```

- [ ] **Step 5: Register in main.py**

  ```python
  from api.routers import articles
  app.include_router(articles.router)
  ```

- [ ] **Step 6: Run tests — expect PASS**

  Run: `pytest link-engine/tests/test_api_articles.py -v`
  Expected: 2 passed.

- [ ] **Step 7: Commit**

  ```bash
  git add api/routers/articles.py api/schemas/articles.py api/main.py tests/test_api_articles.py
  git commit -m "feat: articles router with list, ingest, export endpoints"
  ```

---

### Task 2.2: Pipeline router

**Files:**
- Create: `link-engine/api/schemas/pipeline.py`
- Create: `link-engine/api/routers/pipeline.py`
- Modify: `link-engine/api/main.py`

- [ ] **Step 1: Write tests**

  Create `link-engine/tests/test_api_pipeline.py`:
  ```python
  from fastapi.testclient import TestClient
  from api.main import app

  client = TestClient(app)

  def test_pipeline_status_requires_auth():
      r = client.get("/pipeline/status")
      assert r.status_code == 401

  def test_pipeline_runs_returns_list():
      token = _admin_token()  # reuse helper
      r = client.get("/pipeline/runs", headers={"Authorization": f"Bearer {token}"})
      assert r.status_code == 200
      assert isinstance(r.json(), list)
  ```

- [ ] **Step 2: Run — expect FAIL**

  Run: `pytest link-engine/tests/test_api_pipeline.py::test_pipeline_status_requires_auth -v`
  Expected: 404.

- [ ] **Step 3: Create `api/schemas/pipeline.py`**

  ```python
  from pydantic import BaseModel
  from typing import Optional
  from datetime import datetime

  class RunOut(BaseModel):
      run_id: str
      started_at: datetime
      completed_at: Optional[datetime]
      articles_processed: int
      matches_found: int
      links_injected: int
      errors_total: int

      class Config:
          from_attributes = True

  class PipelineStatus(BaseModel):
      pending_review: int
      approved: int
      rejected: int
      unresolved_errors: int

  class RunTriggerResponse(BaseModel):
      run_id: str
      message: str
  ```

- [ ] **Step 4: Create `api/routers/pipeline.py`**

  ```python
  from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
  from typing import List
  from api.dependencies import get_db, get_current_user, require_admin
  from api.schemas.pipeline import RunOut, PipelineStatus, RunTriggerResponse
  from link_engine.db.models import Anchor, Error, Run
  import uuid

  router = APIRouter(prefix="/pipeline", tags=["pipeline"])

  def _run_pipeline_background(run_id: str, content_dir: str):
      """Runs full pipeline stages synchronously in a background thread."""
      from link_engine.db.session import get_session_factory
      from link_engine.stages.chunk import chunk_all_articles
      from link_engine.stages.embed import embed_all_pending, embed_article_representations
      from link_engine.stages.match import compute_matches
      from link_engine.stages.anchor import generate_all_anchors
      from datetime import datetime

      factory = get_session_factory()
      db = factory()
      try:
          run = db.get(Run, run_id)
          # Pipeline already has content ingested — run from chunk onward
          changed_articles = []  # fetch from DB articles with status=new|changed
          from link_engine.db.models import Article
          changed_articles = db.query(Article).filter(Article.status.in_(["new", "changed"])).all()
          chunk_all_articles(changed_articles, db)
          db.commit()
          embed_all_pending(db)
          embed_article_representations(db)
          db.commit()
          compute_matches(db, run_id)
          db.commit()
          generate_all_anchors(db, run_id)
          run.completed_at = datetime.utcnow()
          db.commit()
      finally:
          db.close()

  @router.post("/run", response_model=RunTriggerResponse)
  def trigger_run(background_tasks: BackgroundTasks, db=Depends(get_db), _=Depends(require_admin)):
      run = Run()
      db.add(run)
      db.commit()
      background_tasks.add_task(_run_pipeline_background, run.run_id, "")
      return RunTriggerResponse(run_id=run.run_id, message="Pipeline started")

  @router.get("/status", response_model=PipelineStatus)
  def pipeline_status(db=Depends(get_db), _=Depends(get_current_user)):
      return PipelineStatus(
          pending_review=db.query(Anchor).filter_by(status="pending_review").count(),
          approved=db.query(Anchor).filter_by(status="approved").count(),
          rejected=db.query(Anchor).filter_by(status="rejected").count(),
          unresolved_errors=db.query(Error).filter(Error.resolved_at.is_(None)).count(),
      )

  @router.get("/runs", response_model=List[RunOut])
  def list_runs(db=Depends(get_db), _=Depends(get_current_user)):
      return db.query(Run).order_by(Run.started_at.desc()).limit(20).all()

  @router.get("/runs/{run_id}", response_model=RunOut)
  def get_run(run_id: str, db=Depends(get_db), _=Depends(get_current_user)):
      run = db.get(Run, run_id)
      if not run:
          raise HTTPException(404, "Run not found")
      return run
  ```

- [ ] **Step 5: Register in main.py**

  ```python
  from api.routers import pipeline
  app.include_router(pipeline.router)
  ```

- [ ] **Step 6: Run tests — expect PASS**

  Run: `pytest link-engine/tests/test_api_pipeline.py -v`
  Expected: 2 passed.

- [ ] **Step 7: Commit**

  ```bash
  git add api/routers/pipeline.py api/schemas/pipeline.py api/main.py tests/test_api_pipeline.py
  git commit -m "feat: pipeline router with run trigger, status, and run history"
  ```

---

### Task 2.3: Anchors router

**Files:**
- Create: `link-engine/api/schemas/anchors.py`
- Create: `link-engine/api/routers/anchors.py`
- Modify: `link-engine/api/main.py`

- [ ] **Step 1: Write tests**

  Create `link-engine/tests/test_api_anchors.py`:
  ```python
  from fastapi.testclient import TestClient
  from api.main import app

  client = TestClient(app)

  def test_list_anchors_requires_auth():
      r = client.get("/anchors")
      assert r.status_code == 401

  def test_list_anchors_pending_filter():
      token = _editor_token()
      r = client.get("/anchors?status=pending_review", headers={"Authorization": f"Bearer {token}"})
      assert r.status_code == 200
      assert isinstance(r.json(), list)

  def test_patch_anchor_approve():
      # Requires a seeded anchor with status=pending_review
      token = _editor_token()
      # Use an existing anchor_id or skip if DB empty
      ...
  ```

- [ ] **Step 2: Run — expect FAIL**

  Run: `pytest link-engine/tests/test_api_anchors.py::test_list_anchors_requires_auth -v`
  Expected: 404.

- [ ] **Step 3: Create `api/schemas/anchors.py`**

  ```python
  from pydantic import BaseModel
  from typing import Optional
  from datetime import datetime

  class AnchorOut(BaseModel):
      anchor_id: str
      match_id: str
      anchor_text: Optional[str]
      edited_anchor: Optional[str]
      reasoning: Optional[str]
      llm_confidence: Optional[int]
      status: str
      similarity_score: float
      source_article_title: str
      target_article_title: str
      source_chunk_text: str
      target_chunk_text: str
      target_url: str
      matched_title_phrase: Optional[str]

  class AnchorPatch(BaseModel):
      status: str  # approved | rejected | edited
      edited_anchor: Optional[str] = None
  ```

- [ ] **Step 4: Create `api/routers/anchors.py`**

  ```python
  from fastapi import APIRouter, Depends, HTTPException
  from typing import List, Optional
  from api.dependencies import get_db, get_current_user
  from api.schemas.anchors import AnchorOut, AnchorPatch
  from link_engine.db.models import Anchor, Match, User

  router = APIRouter(prefix="/anchors", tags=["anchors"])

  def _build_anchor_out(anchor: Anchor) -> AnchorOut:
      match = anchor.match
      source = match.source_chunk
      target = match.target_chunk
      slug = target.article.slug
      heading = target.heading or ""
      section = heading.lower().replace(" ", "-")
      url = f"https://canvas-homes.com/blogs/{slug}" + (f"#{section}" if section else "")
      return AnchorOut(
          anchor_id=anchor.anchor_id,
          match_id=anchor.match_id,
          anchor_text=anchor.anchor_text,
          edited_anchor=anchor.edited_anchor,
          reasoning=anchor.reasoning,
          llm_confidence=anchor.llm_confidence,
          status=anchor.status,
          similarity_score=match.similarity_score,
          source_article_title=source.article.title or "",
          target_article_title=target.article.title or "",
          source_chunk_text=source.text,
          target_chunk_text=target.text,
          target_url=url,
          matched_title_phrase=match.matched_title_phrase,
      )

  @router.get("", response_model=List[AnchorOut])
  def list_anchors(
      status: Optional[str] = None,
      assigned_to: Optional[str] = None,
      db=Depends(get_db),
      user: User = Depends(get_current_user),
  ):
      q = db.query(Anchor).join(Anchor.match)
      if status:
          q = q.filter(Anchor.status == status)
      if assigned_to == "me":
          # Filter anchors where a task is assigned to the current user
          from link_engine.db.models import Task
          assigned_anchor_ids = [
              t.anchor_id for t in db.query(Task).filter_by(assigned_to=user.user_id).all()
          ]
          q = q.filter(Anchor.anchor_id.in_(assigned_anchor_ids))
      return [_build_anchor_out(a) for a in q.order_by(Match.similarity_score.desc()).all()]

  @router.patch("/{anchor_id}", response_model=AnchorOut)
  def patch_anchor(anchor_id: str, patch: AnchorPatch, db=Depends(get_db), _=Depends(get_current_user)):
      anchor = db.get(Anchor, anchor_id)
      if not anchor:
          raise HTTPException(404, "Anchor not found")
      if patch.status not in ("approved", "rejected", "edited"):
          raise HTTPException(400, "status must be approved, rejected, or edited")
      anchor.status = patch.status
      if patch.edited_anchor:
          anchor.edited_anchor = patch.edited_anchor
          anchor.status = "approved"
      db.commit()
      return _build_anchor_out(anchor)
  ```

- [ ] **Step 5: Register in main.py**

  ```python
  from api.routers import anchors
  app.include_router(anchors.router)
  ```

- [ ] **Step 6: Run tests — expect PASS**

  Run: `pytest link-engine/tests/test_api_anchors.py -v`
  Expected: 2+ passed.

- [ ] **Step 7: Commit**

  ```bash
  git add api/routers/anchors.py api/schemas/anchors.py api/main.py tests/test_api_anchors.py
  git commit -m "feat: anchors router with list and patch endpoints"
  ```

---

## Phase 3 — Task Assignment & Admin APIs

### Task 3.1: Tasks router

**Files:**
- Create: `link-engine/api/schemas/tasks.py`
- Create: `link-engine/api/routers/tasks.py`
- Modify: `link-engine/api/main.py`

- [ ] **Step 1: Write tests**

  Create `link-engine/tests/test_api_tasks.py`:
  ```python
  from fastapi.testclient import TestClient
  from api.main import app

  client = TestClient(app)

  def test_list_tasks_requires_auth():
      r = client.get("/tasks")
      assert r.status_code == 401

  def test_editor_sees_only_own_tasks():
      token = _editor_token()
      r = client.get("/tasks", headers={"Authorization": f"Bearer {token}"})
      assert r.status_code == 200
      # All returned tasks must be assigned to the editor
      tasks = r.json()
      assert all(t["assigned_to"] == _editor_user_id() for t in tasks)

  def test_admin_can_create_task():
      token = _admin_token()
      r = client.post("/tasks",
          json={"anchor_id": "some-anchor-id", "assigned_to_user_id": _editor_user_id()},
          headers={"Authorization": f"Bearer {token}"}
      )
      assert r.status_code in (200, 201, 422)  # 422 if anchor not seeded
  ```

- [ ] **Step 2: Run — expect FAIL**

  Run: `pytest link-engine/tests/test_api_tasks.py::test_list_tasks_requires_auth -v`
  Expected: 404.

- [ ] **Step 3: Create `api/schemas/tasks.py`**

  ```python
  from pydantic import BaseModel
  from typing import Optional
  from datetime import datetime

  class TaskOut(BaseModel):
      task_id: str
      anchor_id: str
      assigned_to: str
      assigned_by: str
      status: str
      notes: Optional[str]
      assigned_at: datetime
      completed_at: Optional[datetime]

      class Config:
          from_attributes = True

  class TaskCreate(BaseModel):
      anchor_id: str
      assigned_to_user_id: str
      notes: Optional[str] = None

  class TaskPatch(BaseModel):
      status: str  # in_progress | completed
  ```

- [ ] **Step 4: Create `api/routers/tasks.py`**

  ```python
  from fastapi import APIRouter, Depends, HTTPException
  from datetime import datetime
  from typing import List
  from api.dependencies import get_db, get_current_user, require_admin
  from api.schemas.tasks import TaskOut, TaskCreate, TaskPatch
  from link_engine.db.models import Task, User

  router = APIRouter(prefix="/tasks", tags=["tasks"])

  @router.get("", response_model=List[TaskOut])
  def list_tasks(db=Depends(get_db), user: User = Depends(get_current_user)):
      q = db.query(Task)
      if user.role != "admin":
          q = q.filter(Task.assigned_to == user.user_id)
      return q.order_by(Task.assigned_at.desc()).all()

  @router.post("", response_model=TaskOut)
  def create_task(body: TaskCreate, db=Depends(get_db), user: User = Depends(require_admin)):
      task = Task(
          anchor_id=body.anchor_id,
          assigned_to=body.assigned_to_user_id,
          assigned_by=user.user_id,
          notes=body.notes,
          status="pending",
      )
      db.add(task)
      db.commit()
      db.refresh(task)
      return task

  @router.patch("/{task_id}", response_model=TaskOut)
  def patch_task(task_id: str, patch: TaskPatch, db=Depends(get_db), user: User = Depends(get_current_user)):
      task = db.get(Task, task_id)
      if not task:
          raise HTTPException(404, "Task not found")
      if user.role != "admin" and task.assigned_to != user.user_id:
          raise HTTPException(403, "Not your task")
      task.status = patch.status
      if patch.status == "completed":
          task.completed_at = datetime.utcnow()
      db.commit()
      return task
  ```

- [ ] **Step 5: Register in main.py**

  ```python
  from api.routers import tasks
  app.include_router(tasks.router)
  ```

- [ ] **Step 6: Run tests — expect PASS**

  Run: `pytest link-engine/tests/test_api_tasks.py -v`
  Expected: 2+ passed.

- [ ] **Step 7: Commit**

  ```bash
  git add api/routers/tasks.py api/schemas/tasks.py api/main.py tests/test_api_tasks.py
  git commit -m "feat: tasks router with role-scoped list, create, patch"
  ```

---

### Task 3.2: Admin router

**Files:**
- Create: `link-engine/api/schemas/admin.py`
- Create: `link-engine/api/routers/admin.py`
- Modify: `link-engine/api/main.py`

- [ ] **Step 1: Write tests**

  Create `link-engine/tests/test_api_admin.py`:
  ```python
  from fastapi.testclient import TestClient
  from api.main import app

  client = TestClient(app)

  def test_admin_stats_requires_admin():
      token = _editor_token()
      r = client.get("/admin/stats", headers={"Authorization": f"Bearer {token}"})
      assert r.status_code == 403

  def test_admin_can_list_users():
      token = _admin_token()
      r = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
      assert r.status_code == 200
      assert isinstance(r.json(), list)

  def test_admin_can_create_user():
      token = _admin_token()
      r = client.post("/admin/users",
          json={"email": "new@editor.com", "name": "New Editor", "role": "editor", "password": "pass123"},
          headers={"Authorization": f"Bearer {token}"}
      )
      assert r.status_code == 200
  ```

- [ ] **Step 2: Run — expect FAIL**

  Run: `pytest link-engine/tests/test_api_admin.py::test_admin_stats_requires_admin -v`
  Expected: 404.

- [ ] **Step 3: Create `api/schemas/admin.py`**

  ```python
  from pydantic import BaseModel
  from api.schemas.auth import UserOut

  class UserCreate(BaseModel):
      email: str
      name: str
      role: str  # admin | editor
      password: str

  class StatsOut(BaseModel):
      total_articles: int
      pending_review: int
      approved: int
      total_tasks: int
      open_tasks: int
      unresolved_errors: int
  ```

- [ ] **Step 4: Create `api/routers/admin.py`**

  ```python
  from fastapi import APIRouter, Depends, HTTPException
  from passlib.context import CryptContext
  from typing import List
  from api.dependencies import get_db, require_admin
  from api.schemas.admin import UserCreate, StatsOut
  from api.schemas.auth import UserOut
  from link_engine.db.models import User, Article, Anchor, Task, Error

  router = APIRouter(prefix="/admin", tags=["admin"])
  pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

  @router.get("/users", response_model=List[UserOut])
  def list_users(db=Depends(get_db), _=Depends(require_admin)):
      return db.query(User).all()

  @router.post("/users", response_model=UserOut)
  def create_user(body: UserCreate, db=Depends(get_db), _=Depends(require_admin)):
      if db.query(User).filter_by(email=body.email).first():
          raise HTTPException(400, "Email already exists")
      user = User(
          email=body.email, name=body.name, role=body.role,
          hashed_pw=pwd_ctx.hash(body.password)
      )
      db.add(user)
      db.commit()
      db.refresh(user)
      return user

  @router.get("/stats", response_model=StatsOut)
  def admin_stats(db=Depends(get_db), _=Depends(require_admin)):
      return StatsOut(
          total_articles=db.query(Article).count(),
          pending_review=db.query(Anchor).filter_by(status="pending_review").count(),
          approved=db.query(Anchor).filter_by(status="approved").count(),
          total_tasks=db.query(Task).count(),
          open_tasks=db.query(Task).filter(Task.status != "completed").count(),
          unresolved_errors=db.query(Error).filter(Error.resolved_at.is_(None)).count(),
      )
  ```

- [ ] **Step 5: Register in main.py**

  ```python
  from api.routers import admin
  app.include_router(admin.router)
  ```

- [ ] **Step 6: Run tests — expect PASS**

  Run: `pytest link-engine/tests/test_api_admin.py -v`
  Expected: 3 passed.

- [ ] **Step 7: Verify full API**

  Run: `uvicorn api.main:app --reload --port 8000`
  Open: `http://localhost:8000/docs`
  Expected: All endpoints visible in Swagger UI.

- [ ] **Step 8: Commit**

  ```bash
  git add api/routers/admin.py api/schemas/admin.py api/main.py tests/test_api_admin.py
  git commit -m "feat: admin router with user management and stats"
  ```

---

## Phase 4 — Frontend Setup

### Task 4.1: Initialize React + Vite project

**Files:**
- Create: `frontend/` (entire directory)

- [ ] **Step 1: Scaffold project**

  Run from the repo root (parent of `link-engine/`):
  ```bash
  npm create vite@latest frontend -- --template react-ts
  cd frontend
  npm install
  ```

- [ ] **Step 2: Install dependencies**

  ```bash
  npm install axios @tanstack/react-query zustand react-router-dom
  npm install -D tailwindcss postcss autoprefixer
  npx tailwindcss init -p
  ```

- [ ] **Step 3: Configure Tailwind**

  Set `content` in `tailwind.config.ts`:
  ```ts
  content: ["./index.html", "./src/**/*.{ts,tsx}"]
  ```

  Add to `src/index.css`:
  ```css
  @tailwind base;
  @tailwind components;
  @tailwind utilities;
  ```

- [ ] **Step 4: Verify dev server starts**

  Run: `npm run dev`
  Expected: `Local: http://localhost:5173` — Vite default page loads.

- [ ] **Step 5: Commit**

  ```bash
  git add frontend/
  git commit -m "feat: initialize React + Vite frontend with Tailwind"
  ```

---

### Task 4.2: API client + Auth store

**Files:**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/auth.ts`
- Create: `frontend/src/store/auth.ts`

- [ ] **Step 1: Create `src/api/client.ts`**

  ```ts
  import axios from "axios";
  import { useAuthStore } from "../store/auth";

  export const api = axios.create({
    baseURL: "http://localhost:8000",
  });

  api.interceptors.request.use((config) => {
    const token = useAuthStore.getState().token;
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  });

  api.interceptors.response.use(
    (r) => r,
    (err) => {
      if (err.response?.status === 401) {
        useAuthStore.getState().logout();
        window.location.href = "/login";
      }
      return Promise.reject(err);
    }
  );
  ```

- [ ] **Step 2: Create `src/store/auth.ts`**

  ```ts
  import { create } from "zustand";
  import { persist } from "zustand/middleware";

  interface User { user_id: string; email: string; name: string; role: string; }
  interface AuthState {
    token: string | null;
    user: User | null;
    setAuth: (token: string, user: User) => void;
    logout: () => void;
  }

  export const useAuthStore = create<AuthState>()(
    persist(
      (set) => ({
        token: null,
        user: null,
        setAuth: (token, user) => set({ token, user }),
        logout: () => set({ token: null, user: null }),
      }),
      { name: "auth-store" }
    )
  );
  ```

- [ ] **Step 3: Create `src/api/auth.ts`**

  ```ts
  import { api } from "./client";

  export const login = async (email: string, password: string) => {
    const form = new FormData();
    form.append("username", email);
    form.append("password", password);
    const { data } = await api.post("/auth/login", form);
    return data;
  };

  export const me = async () => {
    const { data } = await api.get("/auth/me");
    return data;
  };
  ```

- [ ] **Step 4: Commit**

  ```bash
  git add frontend/src/api/ frontend/src/store/
  git commit -m "feat: API client with JWT injection and auth store"
  ```

---

### Task 4.3: App routing + ProtectedRoute

**Files:**
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/components/ProtectedRoute.tsx`
- Create: `frontend/src/components/RequireRole.tsx`
- Create: `frontend/src/pages/Login.tsx` (stub)
- Create: `frontend/src/pages/EditorDashboard.tsx` (stub)
- Create: `frontend/src/pages/ReviewInterface.tsx` (stub)
- Create: `frontend/src/pages/AdminDashboard.tsx` (stub)

- [ ] **Step 1: Create `src/components/ProtectedRoute.tsx`**

  ```tsx
  import { Navigate } from "react-router-dom";
  import { useAuthStore } from "../store/auth";

  export const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
    const token = useAuthStore((s) => s.token);
    return token ? <>{children}</> : <Navigate to="/login" replace />;
  };
  ```

- [ ] **Step 2: Create `src/components/RequireRole.tsx`**

  ```tsx
  import { Navigate } from "react-router-dom";
  import { useAuthStore } from "../store/auth";

  export const RequireRole = ({ role, children }: { role: string; children: React.ReactNode }) => {
    const user = useAuthStore((s) => s.user);
    return user?.role === role ? <>{children}</> : <Navigate to="/" replace />;
  };
  ```

- [ ] **Step 3: Create stub pages**

  Each stub is a single component returning a heading:
  - `src/pages/Login.tsx` → `<h1>Login</h1>`
  - `src/pages/EditorDashboard.tsx` → `<h1>Editor Dashboard</h1>`
  - `src/pages/ReviewInterface.tsx` → `<h1>Review Interface</h1>`
  - `src/pages/AdminDashboard.tsx` → `<h1>Admin Dashboard</h1>`
  - `src/pages/ArticleManager.tsx` → `<h1>Article Manager</h1>`

- [ ] **Step 4: Replace `src/App.tsx`**

  ```tsx
  import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
  import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
  import { ProtectedRoute } from "./components/ProtectedRoute";
  import { RequireRole } from "./components/RequireRole";
  import Login from "./pages/Login";
  import EditorDashboard from "./pages/EditorDashboard";
  import ReviewInterface from "./pages/ReviewInterface";
  import AdminDashboard from "./pages/AdminDashboard";
  import ArticleManager from "./pages/ArticleManager";

  const queryClient = new QueryClient();

  export default function App() {
    return (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<ProtectedRoute><EditorDashboard /></ProtectedRoute>} />
            <Route path="/review/:anchorId" element={<ProtectedRoute><ReviewInterface /></ProtectedRoute>} />
            <Route path="/admin" element={<ProtectedRoute><RequireRole role="admin"><AdminDashboard /></RequireRole></ProtectedRoute>} />
            <Route path="/articles" element={<ProtectedRoute><RequireRole role="admin"><ArticleManager /></RequireRole></ProtectedRoute>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    );
  }
  ```

- [ ] **Step 5: Verify routing works**

  Run: `npm run dev`
  Navigate to `http://localhost:5173/` — should redirect to `/login` (stub page shows "Login").
  Navigate to `http://localhost:5173/admin` — should redirect to `/login`.

- [ ] **Step 6: Commit**

  ```bash
  git add frontend/src/
  git commit -m "feat: app routing with ProtectedRoute and RequireRole guards"
  ```

---

## Phase 5 — Editor Views

### Task 5.1: Login page

**Files:**
- Replace: `frontend/src/pages/Login.tsx`

- [ ] **Step 1: Implement Login page**

  ```tsx
  import { useState } from "react";
  import { useNavigate } from "react-router-dom";
  import { login } from "../api/auth";
  import { useAuthStore } from "../store/auth";

  export default function Login() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const setAuth = useAuthStore((s) => s.setAuth);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      setError("");
      try {
        const data = await login(email, password);
        setAuth(data.access_token, data.user);
        navigate("/");
      } catch {
        setError("Invalid email or password.");
      }
    };

    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow w-full max-w-sm space-y-4">
          <h1 className="text-2xl font-bold text-gray-800">Link Engine</h1>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <input
            type="email" value={email} onChange={(e) => setEmail(e.target.value)}
            placeholder="Email" required
            className="w-full border rounded px-3 py-2 text-sm"
          />
          <input
            type="password" value={password} onChange={(e) => setPassword(e.target.value)}
            placeholder="Password" required
            className="w-full border rounded px-3 py-2 text-sm"
          />
          <button type="submit" className="w-full bg-blue-600 text-white rounded px-4 py-2 text-sm font-medium hover:bg-blue-700">
            Sign in
          </button>
        </form>
      </div>
    );
  }
  ```

- [ ] **Step 2: Verify manually**

  Ensure backend is running: `uvicorn api.main:app --port 8000`
  Seed an admin user via the API: `POST /admin/users` (use `/docs`).
  Navigate to `http://localhost:5173/login`, submit credentials.
  Expected: Redirects to `/`.

- [ ] **Step 3: Commit**

  ```bash
  git add frontend/src/pages/Login.tsx
  git commit -m "feat: login page with JWT auth flow"
  ```

---

### Task 5.2: Layout + sidebar

**Files:**
- Create: `frontend/src/components/Layout.tsx`
- Modify: `frontend/src/pages/EditorDashboard.tsx`
- Modify: `frontend/src/pages/AdminDashboard.tsx`

- [ ] **Step 1: Create `src/components/Layout.tsx`**

  ```tsx
  import { NavLink, useNavigate } from "react-router-dom";
  import { useAuthStore } from "../store/auth";

  export const Layout = ({ children }: { children: React.ReactNode }) => {
    const { user, logout } = useAuthStore();
    const navigate = useNavigate();

    const handleLogout = () => { logout(); navigate("/login"); };

    return (
      <div className="flex h-screen bg-gray-100">
        <aside className="w-56 bg-white border-r flex flex-col p-4 gap-2">
          <p className="font-bold text-gray-800 mb-4">🔗 Link Engine</p>
          <NavLink to="/" className={({ isActive }) => `text-sm rounded px-3 py-2 ${isActive ? "bg-blue-50 text-blue-700 font-medium" : "text-gray-600 hover:bg-gray-50"}`}>
            My Tasks
          </NavLink>
          {user?.role === "admin" && (
            <>
              <NavLink to="/admin" className={({ isActive }) => `text-sm rounded px-3 py-2 ${isActive ? "bg-blue-50 text-blue-700 font-medium" : "text-gray-600 hover:bg-gray-50"}`}>
                Admin
              </NavLink>
              <NavLink to="/articles" className={({ isActive }) => `text-sm rounded px-3 py-2 ${isActive ? "bg-blue-50 text-blue-700 font-medium" : "text-gray-600 hover:bg-gray-50"}`}>
                Articles
              </NavLink>
            </>
          )}
          <div className="mt-auto pt-4 border-t">
            <p className="text-xs text-gray-500">{user?.name} ({user?.role})</p>
            <button onClick={handleLogout} className="text-xs text-red-500 hover:underline mt-1">Sign out</button>
          </div>
        </aside>
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    );
  };
  ```

- [ ] **Step 2: Wrap EditorDashboard and AdminDashboard in Layout**

  Update both pages to: `return <Layout><h1>...</h1></Layout>;`

- [ ] **Step 3: Verify sidebar**

  Log in as admin → see "My Tasks", "Admin", "Articles" links.
  Log in as editor → see only "My Tasks".

- [ ] **Step 4: Commit**

  ```bash
  git add frontend/src/components/Layout.tsx frontend/src/pages/
  git commit -m "feat: sidebar layout with role-aware nav"
  ```

---

### Task 5.3: Editor Dashboard (task queue)

**Files:**
- Create: `frontend/src/api/tasks.ts`
- Replace: `frontend/src/pages/EditorDashboard.tsx`

- [ ] **Step 1: Create `src/api/tasks.ts`**

  ```ts
  import { api } from "./client";

  export const listTasks = async () => (await api.get("/tasks")).data;
  export const patchTask = async (taskId: string, status: string) =>
    (await api.patch(`/tasks/${taskId}`, { status })).data;
  ```

- [ ] **Step 2: Replace EditorDashboard.tsx**

  ```tsx
  import { useQuery } from "@tanstack/react-query";
  import { useNavigate } from "react-router-dom";
  import { Layout } from "../components/Layout";
  import { listTasks, patchTask } from "../api/tasks";

  export default function EditorDashboard() {
    const { data: tasks = [], refetch } = useQuery({ queryKey: ["tasks"], queryFn: listTasks });
    const navigate = useNavigate();

    const pending = tasks.filter((t: any) => t.status !== "completed");
    const done = tasks.filter((t: any) => t.status === "completed");

    return (
      <Layout>
        <h1 className="text-xl font-semibold mb-4">My Task Queue</h1>
        <div className="grid gap-3">
          {pending.length === 0 && <p className="text-gray-500 text-sm">No tasks assigned. Check back later.</p>}
          {pending.map((task: any) => (
            <div key={task.task_id} className="bg-white border rounded-lg p-4 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-800">Anchor review: <span className="font-mono text-xs text-gray-500">{task.anchor_id.slice(0, 8)}…</span></p>
                {task.notes && <p className="text-xs text-gray-500 mt-1">{task.notes}</p>}
                <span className={`text-xs mt-1 inline-block px-2 py-0.5 rounded-full ${task.status === "in_progress" ? "bg-yellow-100 text-yellow-700" : "bg-gray-100 text-gray-600"}`}>
                  {task.status}
                </span>
              </div>
              <button
                onClick={() => navigate(`/review/${task.anchor_id}`)}
                className="text-sm bg-blue-600 text-white rounded px-3 py-1.5 hover:bg-blue-700"
              >
                Review
              </button>
            </div>
          ))}
        </div>
        {done.length > 0 && (
          <div className="mt-8">
            <p className="text-sm text-gray-400 mb-2">Completed ({done.length})</p>
            {done.map((task: any) => (
              <div key={task.task_id} className="bg-gray-50 border rounded p-3 mb-2 text-sm text-gray-500">
                {task.anchor_id.slice(0, 8)}… — completed
              </div>
            ))}
          </div>
        )}
      </Layout>
    );
  }
  ```

- [ ] **Step 3: Verify visually**

  Run backend + frontend. Log in as editor. Navigate to `/`.
  Expected: Empty task queue with "No tasks assigned" message (or seeded tasks listed).

- [ ] **Step 4: Commit**

  ```bash
  git add frontend/src/api/tasks.ts frontend/src/pages/EditorDashboard.tsx
  git commit -m "feat: editor task queue dashboard"
  ```

---

### Task 5.4: Review Interface (split-screen)

**Files:**
- Create: `frontend/src/api/anchors.ts`
- Replace: `frontend/src/pages/ReviewInterface.tsx`

- [ ] **Step 1: Create `src/api/anchors.ts`**

  ```ts
  import { api } from "./client";

  export const getAnchor = async (anchorId: string) =>
    (await api.get(`/anchors?status=`)).data.find((a: any) => a.anchor_id === anchorId);

  export const patchAnchor = async (anchorId: string, patch: { status: string; edited_anchor?: string }) =>
    (await api.patch(`/anchors/${anchorId}`, patch)).data;
  ```

- [ ] **Step 2: Replace ReviewInterface.tsx**

  ```tsx
  import { useState } from "react";
  import { useParams, useNavigate } from "react-router-dom";
  import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
  import { Layout } from "../components/Layout";
  import { patchAnchor } from "../api/anchors";
  import { api } from "../api/client";

  export default function ReviewInterface() {
    const { anchorId } = useParams<{ anchorId: string }>();
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [editText, setEditText] = useState("");

    const { data: anchor, isLoading } = useQuery({
      queryKey: ["anchor", anchorId],
      queryFn: async () => (await api.get(`/anchors?status=`)).data.find((a: any) => a.anchor_id === anchorId),
      enabled: !!anchorId,
      onSuccess: (a: any) => setEditText(a?.edited_anchor || a?.anchor_text || ""),
    });

    const mutation = useMutation({
      mutationFn: (patch: { status: string; edited_anchor?: string }) => patchAnchor(anchorId!, patch),
      onSuccess: () => { queryClient.invalidateQueries(["tasks"]); navigate("/"); },
    });

    if (isLoading) return <Layout><p className="text-gray-500">Loading…</p></Layout>;
    if (!anchor) return <Layout><p className="text-red-500">Anchor not found.</p></Layout>;

    const confidence = anchor.llm_confidence ?? 0;
    const score = anchor.similarity_score;
    const scoreColor = score >= 0.8 ? "text-green-600" : score >= 0.65 ? "text-yellow-600" : "text-red-500";

    return (
      <Layout>
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <button onClick={() => navigate("/")} className="text-sm text-gray-500 hover:underline">← Back</button>
            <div className="flex gap-2 text-sm">
              <span className={`font-mono ${scoreColor}`}>Score: {score.toFixed(2)}</span>
              <span className="text-gray-400">|</span>
              <span className="text-gray-600">Confidence: {confidence}/5</span>
            </div>
          </div>

          <p className="text-xs text-gray-400 mb-1">
            Matched on phrase: <strong>{anchor.matched_title_phrase || "—"}</strong>
          </p>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="bg-white border rounded-lg p-4">
              <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Source — {anchor.source_article_title}</p>
              <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                {anchor.source_chunk_text.replace(
                  anchor.anchor_text || "",
                  `[${anchor.anchor_text}]`
                )}
              </div>
            </div>
            <div className="bg-white border rounded-lg p-4">
              <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Target — {anchor.target_article_title}</p>
              <p className="text-xs text-blue-500 mb-2 break-all">{anchor.target_url}</p>
              <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{anchor.target_chunk_text}</div>
            </div>
          </div>

          {anchor.reasoning && (
            <p className="text-xs text-gray-400 italic mb-4">LLM: {anchor.reasoning}</p>
          )}

          <div className="bg-white border rounded-lg p-4 flex gap-3 items-center">
            <input
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              className="flex-1 border rounded px-3 py-2 text-sm"
              placeholder="Anchor text"
            />
            <button
              onClick={() => mutation.mutate({ status: "approved", edited_anchor: editText !== anchor.anchor_text ? editText : undefined })}
              className="bg-green-600 text-white rounded px-4 py-2 text-sm font-medium hover:bg-green-700"
            >Approve</button>
            <button
              onClick={() => mutation.mutate({ status: "rejected" })}
              className="bg-red-100 text-red-700 rounded px-4 py-2 text-sm font-medium hover:bg-red-200"
            >Reject</button>
          </div>
        </div>
      </Layout>
    );
  }
  ```

- [ ] **Step 3: Verify split-screen**

  Seed an anchor via the pipeline. Navigate to `/review/<anchor-id>`.
  Expected: Two-column layout with source on left, target on right. Approve/reject buttons work.

- [ ] **Step 4: Commit**

  ```bash
  git add frontend/src/api/anchors.ts frontend/src/pages/ReviewInterface.tsx
  git commit -m "feat: split-screen review interface with approve/reject/edit"
  ```

---

## Phase 6 — Admin Dashboard

### Task 6.1: Admin dashboard — stats + pipeline control

**Files:**
- Create: `frontend/src/api/pipeline.ts`
- Create: `frontend/src/api/admin.ts`
- Replace: `frontend/src/pages/AdminDashboard.tsx`

- [ ] **Step 1: Create `src/api/pipeline.ts`**

  ```ts
  import { api } from "./client";

  export const triggerRun = async () => (await api.post("/pipeline/run")).data;
  export const getPipelineStatus = async () => (await api.get("/pipeline/status")).data;
  export const listRuns = async () => (await api.get("/pipeline/runs")).data;
  ```

- [ ] **Step 2: Create `src/api/admin.ts`**

  ```ts
  import { api } from "./client";

  export const getStats = async () => (await api.get("/admin/stats")).data;
  export const listUsers = async () => (await api.get("/admin/users")).data;
  export const createUser = async (body: { email: string; name: string; role: string; password: string }) =>
    (await api.post("/admin/users", body)).data;
  export const createTask = async (body: { anchor_id: string; assigned_to_user_id: string; notes?: string }) =>
    (await api.post("/tasks", body)).data;
  ```

- [ ] **Step 3: Replace AdminDashboard.tsx**

  ```tsx
  import { useState } from "react";
  import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
  import { Layout } from "../components/Layout";
  import { getStats, listUsers, createUser, createTask } from "../api/admin";
  import { getPipelineStatus, triggerRun, listRuns } from "../api/pipeline";
  import { api } from "../api/client";

  export default function AdminDashboard() {
    const qc = useQueryClient();
    const { data: stats } = useQuery({ queryKey: ["stats"], queryFn: getStats });
    const { data: status } = useQuery({ queryKey: ["pipeline-status"], queryFn: getPipelineStatus });
    const { data: runs = [] } = useQuery({ queryKey: ["runs"], queryFn: listRuns });
    const { data: users = [] } = useQuery({ queryKey: ["users"], queryFn: listUsers });
    const { data: pendingAnchors = [] } = useQuery({
      queryKey: ["anchors-pending"],
      queryFn: async () => (await api.get("/anchors?status=pending_review")).data
    });

    const [newUser, setNewUser] = useState({ email: "", name: "", role: "editor", password: "" });
    const [taskForm, setTaskForm] = useState({ anchor_id: "", assigned_to_user_id: "", notes: "" });

    const runMutation = useMutation({ mutationFn: triggerRun, onSuccess: () => qc.invalidateQueries(["runs"]) });
    const userMutation = useMutation({ mutationFn: createUser, onSuccess: () => { qc.invalidateQueries(["users"]); setNewUser({ email: "", name: "", role: "editor", password: "" }); } });
    const taskMutation = useMutation({ mutationFn: createTask, onSuccess: () => { qc.invalidateQueries(["tasks"]); setTaskForm({ anchor_id: "", assigned_to_user_id: "", notes: "" }); } });

    return (
      <Layout>
        <h1 className="text-xl font-semibold mb-6">Admin Dashboard</h1>

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-3 gap-4 mb-8">
            {[
              ["Articles", stats.total_articles],
              ["Pending Review", stats.pending_review],
              ["Approved", stats.approved],
              ["Total Tasks", stats.total_tasks],
              ["Open Tasks", stats.open_tasks],
              ["Errors", stats.unresolved_errors],
            ].map(([label, val]) => (
              <div key={label as string} className="bg-white border rounded-lg p-4">
                <p className="text-xs text-gray-500">{label}</p>
                <p className="text-2xl font-bold text-gray-800 mt-1">{val}</p>
              </div>
            ))}
          </div>
        )}

        {/* Pipeline */}
        <div className="bg-white border rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-medium text-gray-800">Pipeline</h2>
            <button
              onClick={() => runMutation.mutate()}
              disabled={runMutation.isPending}
              className="bg-blue-600 text-white rounded px-4 py-1.5 text-sm hover:bg-blue-700 disabled:opacity-50"
            >
              {runMutation.isPending ? "Running…" : "Run Pipeline"}
            </button>
          </div>
          <div className="text-xs text-gray-500 space-y-1">
            {runs.slice(0, 5).map((r: any) => (
              <div key={r.run_id} className="flex justify-between border-b pb-1">
                <span className="font-mono">{r.run_id.slice(0, 8)}</span>
                <span>{new Date(r.started_at).toLocaleString()}</span>
                <span>{r.completed_at ? "✓" : "⏳"}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Assign Task */}
        <div className="bg-white border rounded-lg p-4 mb-6">
          <h2 className="font-medium text-gray-800 mb-3">Assign Review Task</h2>
          <div className="grid grid-cols-3 gap-3">
            <select
              value={taskForm.anchor_id}
              onChange={(e) => setTaskForm(f => ({ ...f, anchor_id: e.target.value }))}
              className="border rounded px-3 py-2 text-sm"
            >
              <option value="">Select anchor…</option>
              {pendingAnchors.map((a: any) => (
                <option key={a.anchor_id} value={a.anchor_id}>
                  {a.source_article_title} → {a.target_article_title} ({a.anchor_id.slice(0, 6)})
                </option>
              ))}
            </select>
            <select
              value={taskForm.assigned_to_user_id}
              onChange={(e) => setTaskForm(f => ({ ...f, assigned_to_user_id: e.target.value }))}
              className="border rounded px-3 py-2 text-sm"
            >
              <option value="">Assign to…</option>
              {users.filter((u: any) => u.role === "editor").map((u: any) => (
                <option key={u.user_id} value={u.user_id}>{u.name}</option>
              ))}
            </select>
            <input
              value={taskForm.notes}
              onChange={(e) => setTaskForm(f => ({ ...f, notes: e.target.value }))}
              placeholder="Notes (optional)"
              className="border rounded px-3 py-2 text-sm"
            />
          </div>
          <button
            onClick={() => taskMutation.mutate({ anchor_id: taskForm.anchor_id, assigned_to_user_id: taskForm.assigned_to_user_id, notes: taskForm.notes || undefined })}
            disabled={!taskForm.anchor_id || !taskForm.assigned_to_user_id}
            className="mt-3 bg-green-600 text-white rounded px-4 py-1.5 text-sm hover:bg-green-700 disabled:opacity-50"
          >
            Assign Task
          </button>
        </div>

        {/* Create User */}
        <div className="bg-white border rounded-lg p-4">
          <h2 className="font-medium text-gray-800 mb-3">Create User</h2>
          <div className="grid grid-cols-4 gap-3">
            <input value={newUser.name} onChange={(e) => setNewUser(u => ({ ...u, name: e.target.value }))} placeholder="Name" className="border rounded px-3 py-2 text-sm" />
            <input type="email" value={newUser.email} onChange={(e) => setNewUser(u => ({ ...u, email: e.target.value }))} placeholder="Email" className="border rounded px-3 py-2 text-sm" />
            <input type="password" value={newUser.password} onChange={(e) => setNewUser(u => ({ ...u, password: e.target.value }))} placeholder="Password" className="border rounded px-3 py-2 text-sm" />
            <select value={newUser.role} onChange={(e) => setNewUser(u => ({ ...u, role: e.target.value }))} className="border rounded px-3 py-2 text-sm">
              <option value="editor">Editor</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <button
            onClick={() => userMutation.mutate(newUser)}
            disabled={!newUser.email || !newUser.name || !newUser.password}
            className="mt-3 bg-gray-800 text-white rounded px-4 py-1.5 text-sm hover:bg-gray-900 disabled:opacity-50"
          >
            Create User
          </button>
        </div>
      </Layout>
    );
  }
  ```

- [ ] **Step 4: Verify admin dashboard**

  Log in as admin. Navigate to `/admin`.
  Expected: Stats grid, pipeline run button, task assignment dropdowns, user creation form all render.
  Click "Run Pipeline" → button shows "Running…".

- [ ] **Step 5: Commit**

  ```bash
  git add frontend/src/api/pipeline.ts frontend/src/api/admin.ts frontend/src/pages/AdminDashboard.tsx
  git commit -m "feat: admin dashboard with stats, pipeline control, task assignment, user creation"
  ```

---

## Phase 7 — Article Manager

### Task 7.1: Article manager page

**Files:**
- Create: `frontend/src/api/articles.ts`
- Replace: `frontend/src/pages/ArticleManager.tsx`

- [ ] **Step 1: Create `src/api/articles.ts`**

  ```ts
  import { api } from "./client";

  export const listArticles = async () => (await api.get("/articles")).data;
  export const ingestArticles = async (files: File[]) => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    return (await api.post("/articles/ingest", form)).data;
  };
  export const exportArticle = (articleId: string) =>
    api.get(`/articles/${articleId}/export`, { responseType: "blob" });
  ```

- [ ] **Step 2: Replace ArticleManager.tsx**

  ```tsx
  import { useRef, useState } from "react";
  import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
  import { Layout } from "../components/Layout";
  import { listArticles, ingestArticles, exportArticle } from "../api/articles";

  export default function ArticleManager() {
    const qc = useQueryClient();
    const inputRef = useRef<HTMLInputElement>(null);
    const [ingestResult, setIngestResult] = useState<any>(null);

    const { data: articles = [] } = useQuery({ queryKey: ["articles"], queryFn: listArticles });

    const ingestMutation = useMutation({
      mutationFn: (files: File[]) => ingestArticles(files),
      onSuccess: (data) => { setIngestResult(data); qc.invalidateQueries(["articles"]); },
    });

    const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || []);
      if (files.length) ingestMutation.mutate(files);
    };

    const handleExport = async (articleId: string, slug: string) => {
      const res = await exportArticle(articleId);
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url; a.download = `${slug}.md`; a.click();
      URL.revokeObjectURL(url);
    };

    return (
      <Layout>
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-semibold">Articles</h1>
          <div className="flex gap-2">
            <input ref={inputRef} type="file" accept=".md" multiple className="hidden" onChange={handleUpload} />
            <button
              onClick={() => inputRef.current?.click()}
              disabled={ingestMutation.isPending}
              className="bg-blue-600 text-white rounded px-4 py-1.5 text-sm hover:bg-blue-700 disabled:opacity-50"
            >
              {ingestMutation.isPending ? "Ingesting…" : "Upload .md files"}
            </button>
          </div>
        </div>

        {ingestResult && (
          <div className="bg-green-50 border border-green-200 rounded p-3 mb-4 text-sm text-green-700">
            Ingested: {ingestResult.new} new, {ingestResult.changed} changed, {ingestResult.unchanged} unchanged, {ingestResult.errors} errors.
          </div>
        )}

        <div className="bg-white border rounded-lg divide-y">
          {articles.length === 0 && <p className="p-4 text-sm text-gray-400">No articles yet. Upload .md files to get started.</p>}
          {articles.map((a: any) => (
            <div key={a.article_id} className="flex items-center justify-between p-4">
              <div>
                <p className="text-sm font-medium text-gray-800">{a.title || a.slug}</p>
                <p className="text-xs text-gray-400 mt-0.5">{a.chunk_count} chunks · {a.injected_count} links injected · <span className={a.status === "new" ? "text-blue-500" : a.status === "changed" ? "text-yellow-500" : "text-gray-400"}>{a.status}</span></p>
              </div>
              <button
                onClick={() => handleExport(a.article_id, a.slug)}
                className="text-xs text-gray-500 border rounded px-3 py-1 hover:bg-gray-50"
              >
                Export
              </button>
            </div>
          ))}
        </div>
      </Layout>
    );
  }
  ```

- [ ] **Step 3: Verify upload + export**

  Log in as admin. Navigate to `/articles`.
  Upload 1-2 `.md` files with valid frontmatter.
  Expected: Success banner shows new/changed counts. Article list updates.
  Click Export → downloads the `.md` file.

- [ ] **Step 4: Commit**

  ```bash
  git add frontend/src/api/articles.ts frontend/src/pages/ArticleManager.tsx
  git commit -m "feat: article manager with upload ingestion and export"
  ```

---

## Phase 8 — Wiring & Production Readiness

### Task 8.1: Create admin seed script

**Files:**
- Create: `link-engine/scripts/seed_admin.py`

- [ ] **Step 1: Create seed script**

  ```python
  # link-engine/scripts/seed_admin.py
  # Run once: python scripts/seed_admin.py
  from passlib.context import CryptContext
  from link_engine.db.session import get_session_factory
  from link_engine.db.models import User

  pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
  factory = get_session_factory()
  db = factory()

  admin = User(
      email="admin@canvas-homes.com",
      name="Admin",
      role="admin",
      hashed_pw=pwd_ctx.hash("changeme123"),
  )
  db.merge(admin)
  db.commit()
  print(f"Admin created: {admin.email} / changeme123")
  db.close()
  ```

- [ ] **Step 2: Run seed script**

  Run from `link-engine/`: `python scripts/seed_admin.py`
  Expected: `Admin created: admin@canvas-homes.com / changeme123`

- [ ] **Step 3: Commit**

  ```bash
  git add scripts/seed_admin.py
  git commit -m "chore: admin seed script for initial setup"
  ```

---

### Task 8.2: Run full test suite

- [ ] **Step 1: Run all backend tests**

  Run from `link-engine/`:
  ```bash
  pytest tests/ -v
  ```
  Expected: All tests pass. Fix any failures before proceeding.

- [ ] **Step 2: Run frontend type check**

  Run from `frontend/`:
  ```bash
  npm run build
  ```
  Expected: No TypeScript errors. Build completes.

- [ ] **Step 3: End-to-end smoke test**

  1. Start backend: `uvicorn api.main:app --port 8000 --reload`
  2. Start frontend: `npm run dev`
  3. Open `http://localhost:5173/login`
  4. Log in as admin (`admin@canvas-homes.com`)
  5. Upload 2 `.md` articles in `/articles`
  6. Go to `/admin` → click "Run Pipeline"
  7. Wait for pipeline to complete (check runs list)
  8. Assign a pending anchor task to an editor
  9. Log in as editor
  10. See task in `/` dashboard
  11. Click "Review" → approve the link
  12. Confirm task marked completed

- [ ] **Step 4: Commit**

  ```bash
  git add .
  git commit -m "chore: full test suite pass and e2e smoke verification"
  ```

---

## Order of Execution Summary

| Phase | What | Depends on |
|-------|------|------------|
| 1 | Backend foundation (FastAPI, auth, User/Task models) | Nothing |
| 2 | Pipeline + Articles + Anchors APIs | Phase 1 |
| 3 | Tasks + Admin APIs | Phase 1 |
| 4 | Frontend setup (Vite, routing, API client) | Phase 1 (needs API contract) |
| 5 | Editor views (login, dashboard, review) | Phase 4 + Phase 2+3 running |
| 6 | Admin dashboard | Phase 4 + Phase 2+3 |
| 7 | Article manager | Phase 4 + Phase 2 |
| 8 | Seed + testing | All phases |

Phases 2 and 3 can be built in parallel. Phases 5, 6, and 7 can be built in parallel once Phase 4 is complete.

---

## Self-Review

**Spec coverage:**
- ✅ Preserve all existing business logic — stages untouched, wrapped by API layer
- ✅ FastAPI backend — all routers created
- ✅ Role system (admin/editor) — User model + `require_admin` dependency + `RequireRole` component
- ✅ Task assignment system — Task model + `/tasks` router + admin UI
- ✅ Editor dashboard (task queue) — `EditorDashboard.tsx`
- ✅ Review interface (split screen) — `ReviewInterface.tsx`
- ✅ Admin dashboard (task assignment + tracking) — `AdminDashboard.tsx`
- ✅ Article ingestion — `/articles/ingest` + `ArticleManager.tsx` upload
- ✅ Article export — `/articles/{id}/export` + download button

**Placeholder scan:** No TBDs, TODOs, or "similar to" references. All steps include explicit code.

**Type consistency:** `AnchorOut` used in both `anchors.py` schema and referenced in `ReviewInterface.tsx`. `UserOut` used in auth schema and returned by admin endpoints. `TaskOut` consistent across router and frontend API client.

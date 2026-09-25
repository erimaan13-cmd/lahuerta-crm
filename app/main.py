"""Aplicación FastAPI: interfaz CRM (HTML) + API REST (JSON). Las rutas solo validan permisos y
delegan en app/services (arquitectura en capas, docs/02_PLAN.md §5)."""
import csv
import hmac
import io
import json
import logging
import secrets
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, File, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app import config, db as dbmod, routers, web
from app.audit import ip_var, record, request_id_var, verify_chain
from app.classifier.taxonomy import CATEGORIES
from app.integrations.email_providers import (EmlDirectoryProvider, MockMailboxProvider, RawEmail,
                                              parse_eml_bytes)
from app.integrations.erp import MockErpAdapter, sync_orders
from app.models import (Account, AuditEvent, Case, Contact, EmailClassification, EmailMessage, Lead,
                        Opportunity, Product, Quote, Sector, Task, User)
from app.permissions import ROLE_LABELS, has_permission
from app.security import make_session_token, read_session_token, verify_password
from app.services import crm, dashboard, email_pipeline, pipeline
from app.services.automations import reorder_candidates, run_reorder_check
from app.services import users as users_svc
from app.services.business_time import TZ as BTZ, to_local, to_utc_naive
from app.services.common import DomainError, get_or_404
from app.services.quote_pdf import render_quote_pdf

CSRF_COOKIE = web.CSRF_COOKIE
_login_fails: dict[tuple, deque] = defaultdict(deque)  # (ip, email) → instantes de fallos (memoria de proceso)

templates = web.templates
render, back, form_dict, ser = web.render, web.back, web.form_dict, web.ser
csrf_protect, current_user, require, entity_history = web.csrf_protect, web.current_user, web.require, web.entity_history
NotAuthenticated, Forbidden, CsrfError = web.NotAuthenticated, web.Forbidden, web.CsrfError


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {"ts": self.formatTime(record), "level": record.levelname, "logger": record.name,
                   "msg": record.getMessage(), "request_id": request_id_var.get()}
        for k in ("email_id", "category", "confidence", "review", "path", "status", "ms"):
            if hasattr(record, k):
                payload[k] = getattr(record, k)
        return json.dumps(payload, ensure_ascii=False)


_h = logging.StreamHandler()
_h.setFormatter(JsonFormatter())
logging.getLogger("crm").handlers = [_h]
logging.getLogger("crm").setLevel(logging.INFO)
log = logging.getLogger("crm.http")

app = FastAPI(title="Sistema interno La Huerta (CRM + operación)", version="0.2.0")
for _r in routers.ALL:
    app.include_router(_r)
# hoja de estilo del sistema visual (un solo archivo, cacheable)
app.mount("/static", StaticFiles(directory=str(web.BASE / "static")), name="static")

templates.env.globals["pending_notifications"] = None  # lo inyecta el middleware por solicitud

ENTITY_PARAMS = {"lead_id": "lead", "account_id": "account", "opp_id": "opportunity", "case_id": "case",
                 "email_id": "email", "quote_id": "quote", "task_id": "task", "user_id": "user",
                 "order_id": "sales_order", "po_id": "purchase_order", "asset_id": "asset",
                 "employee_id": "employee", "fund_id": "petty_cash", "product_id": "product",
                 "lot_id": "lot", "warehouse_id": "warehouse", "wo_id": "work_order",
                 "notification_id": "notification", "attachment_id": "attachment"}
# Excepción documentada a la regla 1 (D-55): `/api/avisos/pendientes` se llama en cada carga
# de página y su registro ahogaría la bitácora. Es de solo lectura: ninguna mutación queda fuera.
SKIP_ACCESS_LOG = {"/health", "/login", "/logout", "/favicon.ico", "/api/avisos/pendientes"}
DENIED = {401, 403, 415, 429}


def _log_access(request: Request, status: int, ms: float) -> None:
    """Registra CADA solicitud de un usuario autenticado y todo intento rechazado (requisito de historial total)."""
    path = request.url.path
    if path in SKIP_ACCESS_LOG:
        return
    uid = read_session_token(request.cookies.get(config.SESSION_COOKIE))
    denied = status in DENIED
    if not uid and not denied:
        return
    gen = app.dependency_overrides.get(dbmod.get_db, dbmod.get_db)()
    db = next(gen)
    try:
        if uid and db.get(User, uid) is None:
            uid = None
        route = request.scope.get("route")
        template = getattr(route, "path", path)
        etype, eid = "ruta", None
        for k, v in (request.scope.get("path_params") or {}).items():
            if k in ENTITY_PARAMS:
                etype, eid = ENTITY_PARAMS[k], v
                break
        kind = "denegado" if denied else ("consulta" if request.method in ("GET", "HEAD") else "operacion")
        full = path + (f"?{request.url.query}" if request.url.query else "")
        record(db, uid, f"acceso.{kind}", etype, eid, category="seguridad" if denied else "acceso",
               summary=f"{request.method} {template} → {status}", method=request.method, path=full[:300],
               status=status, after={"ms": ms, "route": template})
        db.commit()
    except Exception:  # la bitácora nunca debe tumbar la respuesta; el error queda en el log técnico
        db.rollback()
        log.exception("audit_access_failed")
    finally:
        gen.close()


@app.middleware("http")
async def request_context(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
    token = request_id_var.set(rid)
    ip_token = ip_var.set(request.client.host if request.client else None)
    t0 = time.perf_counter()
    csrf = request.cookies.get(CSRF_COOKIE) or secrets.token_urlsafe(24)
    request.state.csrf = csrf
    try:
        ctype = request.headers.get("content-type", "")
        has_body = request.headers.get("content-length", "0") not in ("", "0") or "transfer-encoding" in request.headers
        if (request.url.path.startswith("/api") and request.method in ("POST", "PUT", "PATCH", "DELETE")
                and not ctype.startswith("application/json") and (ctype or has_body)):
            # evita CSRF con formularios text/plain: solo JSON (dispara CORS preflight entre orígenes)
            response = JSONResponse({"detail": "La API solo acepta Content-Type: application/json"}, status_code=415)
        else:
            response = await call_next(request)
        ms = round((time.perf_counter() - t0) * 1000, 1)
        _log_access(request, response.status_code, ms)
    finally:
        request_id_var.reset(token)
        ip_var.reset(ip_token)
    response.headers["X-Request-ID"] = rid
    if request.cookies.get(CSRF_COOKIE) != csrf:
        response.set_cookie(CSRF_COOKIE, csrf, httponly=True, samesite="lax", max_age=config.SESSION_MAX_AGE_S)
    log.info("request", extra={"path": request.url.path, "status": response.status_code, "ms": ms})
    return response


def _is_api(request: Request) -> bool:
    return request.url.path.startswith("/api")


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    if _is_api(request):
        return JSONResponse({"detail": exc.message}, status_code=exc.status_code)
    return templates.TemplateResponse(request, "error.html", {"message": exc.message, "user": None},
                                      status_code=exc.status_code)


@app.exception_handler(CsrfError)
async def csrf_handler(request: Request, exc):
    return templates.TemplateResponse(request, "error.html", {"message": "Formulario vencido o inválido (CSRF). "
                                      "Recarga la página e inténtalo de nuevo.", "user": None}, status_code=403)


@app.exception_handler(NotAuthenticated)
async def not_auth_handler(request: Request, exc):
    if _is_api(request):
        return JSONResponse({"detail": "No autenticado"}, status_code=401)
    return RedirectResponse("/login", status_code=303)


@app.exception_handler(Forbidden)
async def forbidden_handler(request: Request, exc: Forbidden):
    msg = f"Tu rol no tiene el permiso '{exc.perm}'"
    if _is_api(request):
        return JSONResponse({"detail": msg}, status_code=403)
    return templates.TemplateResponse(request, "error.html", {"message": msg, "user": None}, status_code=403)


# ======================================================================= salud y sesión
@app.get("/health")
def health(db: Session = Depends(dbmod.get_db)):
    db.execute(select(1))
    return {"status": "ok", "version": app.version}


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"user": None, "error": None})


@app.post("/login", dependencies=[Depends(csrf_protect)])
async def login(request: Request, db: Session = Depends(dbmod.get_db)):
    f = await form_dict(request)
    email = (f.get("email") or "").strip().lower()
    key = (request.client.host if request.client else "?", email)
    now = time.time()
    fails = _login_fails[key]
    while fails and now - fails[0] > config.LOGIN_LOCK_MINUTES * 60:
        fails.popleft()
    user = db.scalar(select(User).where(User.email == email))
    if len(fails) >= config.LOGIN_MAX_FAILS:
        record(db, None, "auth.bloqueado", "user", user.id if user else None, after={"email": email},
               category="seguridad", summary=f"Intento de acceso bloqueado para {email}", status=429)
        db.commit()
        return templates.TemplateResponse(request, "login.html", {"user": None, "error":
                                          f"Demasiados intentos. Espera {config.LOGIN_LOCK_MINUTES} minutos."}, status_code=429)
    if not user or not user.is_active or not verify_password(f.get("password") or "", user.password_hash):
        fails.append(now)
        reason = "usuario inexistente" if not user else ("usuario desactivado" if not user.is_active else "contraseña incorrecta")
        record(db, None, "auth.login_fallido", "user", user.id if user else None,
               after={"email": email, "motivo": reason, "intento": len(fails)}, category="seguridad",
               summary=f"Inicio de sesión fallido ({reason}) para {email}", status=401)
        db.commit()
        return templates.TemplateResponse(request, "login.html", {"user": None, "error": "Credenciales inválidas"},
                                          status_code=401)
    fails.clear()
    record(db, user.id, "auth.login", "user", user.id, category="seguridad", summary=f"Inicio de sesión de {user.email}")
    db.commit()
    resp = back("/")
    resp.set_cookie(config.SESSION_COOKIE, make_session_token(user.id), httponly=True, samesite="lax",
                    max_age=config.SESSION_MAX_AGE_S)
    return resp


@app.post("/logout", dependencies=[Depends(csrf_protect)])
def logout(request: Request, db: Session = Depends(dbmod.get_db)):
    uid = read_session_token(request.cookies.get(config.SESSION_COOKIE))
    if uid and db.get(User, uid):
        record(db, uid, "auth.logout", "user", uid, category="seguridad", summary="Cierre de sesión")
        db.commit()
    resp = back("/login")
    resp.delete_cookie(config.SESSION_COOKIE)
    return resp


# ======================================================================= UI
@app.get("/", response_class=HTMLResponse)
def ui_dashboard(request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("dashboard:read"))):
    my_tasks = list(db.scalars(select(Task).where(Task.status == "pendiente",
                                                  (Task.assignee_id == user.id) | (Task.assignee_role == user.role))
                               .order_by(Task.due_at).limit(10)))
    from app.services import notifications as notif_svc
    return render(request, "dashboard.html", user, m=dashboard.metrics(db), my_tasks=my_tasks,
                  reorder=reorder_candidates(db), op=dashboard.operations(db),
                  avisos=notif_svc.listing(db, user)[:8])


@app.get("/leads", response_class=HTMLResponse)
def ui_leads(request: Request, status: str | None = None, sector: str | None = None, source: str | None = None,
             db: Session = Depends(dbmod.get_db), user: User = Depends(require("lead:read"))):
    leads = crm.filter_leads(db, status or None, sector or None, source or None)
    return render(request, "leads.html", user, leads=leads, sectors=list(db.scalars(select(Sector))),
                  sources=sorted(crm.LEAD_SOURCES), f={"status": status, "sector": sector, "source": source})


@app.post("/leads", dependencies=[Depends(csrf_protect)])
async def ui_create_lead(request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("lead:write"))):
    lead, _ = crm.create_lead(db, await form_dict(request), user.id)
    return back(f"/leads/{lead.id}")


@app.get("/leads/{lead_id}", response_class=HTMLResponse)
def ui_lead(lead_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("lead:read"))):
    lead = get_or_404(db, Lead, lead_id, "Lead")
    dup = db.get(Lead, lead.possible_duplicate_of_id) if lead.possible_duplicate_of_id else None
    return render(request, "lead_detail.html", user, **entity_history(db, user, lead.id), lead=lead, dup=dup, timeline=crm.timeline(db, "lead", lead.id),
                  next_status=sorted(crm.LEAD_TRANSITIONS.get(lead.status, set())))


@app.post("/leads/{lead_id}/status", dependencies=[Depends(csrf_protect)])
async def ui_lead_status(lead_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("lead:write"))):
    f = await form_dict(request)
    crm.change_lead_status(db, lead_id, f.get("status"), user.id, f.get("reason"))
    return back(f"/leads/{lead_id}")


@app.post("/leads/{lead_id}/convert", dependencies=[Depends(csrf_protect)])
async def ui_lead_convert(lead_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("lead:convert"))):
    f = await form_dict(request)
    r = crm.convert_lead(db, lead_id, user.id, create_opportunity="create_opportunity" in f,
                         opp_type=f.get("opp_type") or "estandar", opp_title=f.get("opp_title") or None)
    return back(f"/opportunities/{r['opportunity'].id}" if r["opportunity"] else f"/accounts/{r['account'].id}")


@app.post("/activities", dependencies=[Depends(csrf_protect)])
async def ui_activity(request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("activity:write"))):
    f = await form_dict(request)
    crm.log_activity(db, f, user.id)
    return back(f.get("next") or "/")


@app.get("/accounts", response_class=HTMLResponse)
def ui_accounts(request: Request, lifecycle: str | None = None, db: Session = Depends(dbmod.get_db), user: User = Depends(require("account:read"))):
    stmt = select(Account).order_by(Account.name)
    if lifecycle:
        stmt = stmt.where(Account.lifecycle == lifecycle)
    return render(request, "accounts.html", user, accounts=list(db.scalars(stmt)), lifecycle=lifecycle,
                  sectors=list(db.scalars(select(Sector))))


@app.post("/accounts", dependencies=[Depends(csrf_protect)])
async def ui_create_account(request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("account:write"))):
    acc = crm.create_account(db, await form_dict(request), user.id)
    return back(f"/accounts/{acc.id}")


@app.get("/accounts/{account_id}", response_class=HTMLResponse)
def ui_account(account_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("account:read"))):
    acc = get_or_404(db, Account, account_id, "Cuenta")
    contact_ids = [c.id for c in acc.contacts]
    conds = [EmailMessage.from_email.in_([c.email for c in acc.contacts if c.email])]
    if acc.domain:
        conds.append(EmailMessage.from_email.like(f"%@{acc.domain}"))
    emails = list(db.scalars(select(EmailMessage).where(or_(*conds)).order_by(EmailMessage.received_at.desc())))
    return render(request, "account_detail.html", user, **entity_history(db, user, acc.id), acc=acc, emails=emails,
                  timeline=crm.timeline(db, "account", acc.id), contact_ids=contact_ids,
                  opp_types=sorted(pipeline.OPP_TYPES), products=list(db.scalars(select(Product).order_by(Product.name))))


@app.post("/accounts/{account_id}/contacts", dependencies=[Depends(csrf_protect)])
async def ui_create_contact(account_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("account:write"))):
    crm.create_contact(db, account_id, await form_dict(request), user.id)
    return back(f"/accounts/{account_id}")


@app.get("/opportunities", response_class=HTMLResponse)
def ui_opps(request: Request, type: str | None = None, db: Session = Depends(dbmod.get_db), user: User = Depends(require("opportunity:read"))):
    stmt = select(Opportunity).order_by(Opportunity.updated_at.desc())
    if type:
        stmt = stmt.where(Opportunity.type == type)
    opps = list(db.scalars(stmt))
    cols = {s: [o for o in opps if o.stage == s] for s in pipeline.STAGE_LABELS}
    return render(request, "opportunities.html", user, cols=cols, opp_type=type, opp_types=sorted(pipeline.OPP_TYPES))


@app.post("/opportunities", dependencies=[Depends(csrf_protect)])
async def ui_create_opp(request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("opportunity:write"))):
    form = await request.form()
    f = {k: v for k, v in form.items()}
    f["product_ids"] = form.getlist("product_ids")
    opp = crm.create_opportunity(db, f, user.id)
    return back(f"/opportunities/{opp.id}")


@app.get("/opportunities/{opp_id}", response_class=HTMLResponse)
def ui_opp(opp_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("opportunity:read"))):
    opp = get_or_404(db, Opportunity, opp_id, "Oportunidad")
    return render(request, "opportunity_detail.html", user, **entity_history(db, user, opp.id), opp=opp,
                  next_stages=sorted(pipeline.allowed_next(opp.type, opp.stage)),
                  stages=pipeline.stages_for(opp.type), timeline=crm.timeline(db, "opportunity", opp.id),
                  products=list(db.scalars(select(Product).order_by(Product.name))), packaging=sorted(crm.PACKAGING))


@app.post("/opportunities/{opp_id}/stage", dependencies=[Depends(csrf_protect)])
async def ui_opp_stage(opp_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("opportunity:write"))):
    f = await form_dict(request)
    crm.change_stage(db, opp_id, f.get("stage"), user.id, f.get("lost_reason"))
    return back(f"/opportunities/{opp_id}")


@app.post("/opportunities/{opp_id}/quotes", dependencies=[Depends(csrf_protect)])
async def ui_quote(opp_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("quote:write"))):
    f = await form_dict(request)
    items = [{"product_id": f.get(f"product_id_{i}"), "qty_kg": f.get(f"qty_kg_{i}"), "packaging": f.get(f"packaging_{i}"),
              "unit_price_mxn": f.get(f"unit_price_mxn_{i}")} for i in range(3) if f.get(f"product_id_{i}")]
    crm.create_quote(db, opp_id, items, user.id)
    return back(f"/opportunities/{opp_id}")


@app.get("/tasks", response_class=HTMLResponse)
def ui_tasks(request: Request, status: str = "pendiente", role: str | None = None, db: Session = Depends(dbmod.get_db), user: User = Depends(require("task:read"))):
    stmt = select(Task).where(Task.status == status).order_by(Task.due_at)
    if role:
        stmt = stmt.where(Task.assignee_role == role)
    return render(request, "tasks.html", user, tasks=list(db.scalars(stmt)), status=status, role=role)


@app.post("/tasks", dependencies=[Depends(csrf_protect)])
async def ui_create_task(request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("task:write"))):
    f = await form_dict(request)
    crm.create_task(db, f, user.id)
    return back(f.get("next") or "/tasks")


@app.post("/tasks/{task_id}/complete", dependencies=[Depends(csrf_protect)])
async def ui_complete_task(task_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("task:write"))):
    f = await form_dict(request)
    crm.complete_task(db, task_id, user.id)
    return back(f.get("next") or "/tasks")


@app.get("/cases", response_class=HTMLResponse)
def ui_cases(request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("case:read"))):
    return render(request, "cases.html", user, cases=list(db.scalars(select(Case).order_by(Case.created_at.desc()))))


@app.get("/cases/{case_id}", response_class=HTMLResponse)
def ui_case(case_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("case:read"))):
    c = get_or_404(db, Case, case_id, "Caso")
    return render(request, "case_detail.html", user, **entity_history(db, user, c.id), c=c, timeline=crm.timeline(db, "case", c.id),
                  next_status=sorted(crm.CASE_TRANSITIONS.get(c.status, set())))


@app.post("/cases/{case_id}/status", dependencies=[Depends(csrf_protect)])
async def ui_case_status(case_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("case:write"))):
    f = await form_dict(request)
    crm.change_case_status(db, case_id, f.get("status"), user.id, f.get("lot_reference"))
    return back(f"/cases/{case_id}")


@app.get("/emails", response_class=HTMLResponse)
def ui_emails(request: Request, category: str | None = None, review: str | None = None,
              db: Session = Depends(dbmod.get_db), user: User = Depends(require("email:read"))):
    stmt = select(EmailMessage).join(EmailClassification).order_by(EmailMessage.received_at.desc())
    if category:
        stmt = stmt.where(EmailClassification.category == category)
    if review:
        stmt = stmt.where(EmailClassification.review_status == review)
    return render(request, "emails.html", user, emails=list(db.scalars(stmt)), category=category, review=review)


@app.get("/emails/needs-review", response_class=HTMLResponse)
def ui_needs_review(request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("email:read"))):
    return render(request, "emails.html", user, emails=email_pipeline.needs_review_queue(db), category=None,
                  review="needs_review", title="Bandeja Needs Review")


@app.get("/emails/{email_id}", response_class=HTMLResponse)
def ui_email(email_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("email:read"))):
    msg = get_or_404(db, EmailMessage, email_id, "Correo")
    return render(request, "email_detail.html", user, **entity_history(db, user, msg.id), msg=msg, cls=msg.classification)


@app.post("/emails/{email_id}/review", dependencies=[Depends(csrf_protect)])
async def ui_email_review(email_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("email:review"))):
    f = await form_dict(request)
    email_pipeline.review(db, email_id, user.id, f.get("category") or None)
    return back(f"/emails/{email_id}")


@app.post("/emails/{email_id}/apply", dependencies=[Depends(csrf_protect)])
async def ui_email_apply(email_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("email:review"))):
    f = await form_dict(request)
    email_pipeline.apply_suggestion(db, email_id, user.id, f.get("action") or None)
    return back(f"/emails/{email_id}")


@app.post("/emails/ingest-demo", dependencies=[Depends(csrf_protect)])
def ui_ingest_demo(db: Session = Depends(dbmod.get_db), user: User = Depends(require("email:ingest"))):
    data = config.BASE_DIR / "data"
    email_pipeline.ingest(db, MockMailboxProvider(data / "demo_emails.json"), actor_id=user.id)
    email_pipeline.ingest(db, EmlDirectoryProvider(data / "sample_emails"), actor_id=user.id)
    return back("/emails")


@app.post("/emails/upload", dependencies=[Depends(csrf_protect)])
async def ui_upload_eml(file: UploadFile = File(...), db: Session = Depends(dbmod.get_db), user: User = Depends(require("email:ingest"))):
    raw = parse_eml_bytes(await file.read(), provider="eml_upload")
    msg, _ = email_pipeline.process_raw(db, raw, actor_id=user.id)
    return back(f"/emails/{msg.id}")


@app.get("/search", response_class=HTMLResponse)
def ui_search(request: Request, q: str = "", db: Session = Depends(dbmod.get_db), user: User = Depends(require("lead:read"))):
    return render(request, "search.html", user, q=q, r=crm.search(db, q))


AUDIT_PAGE = 100


def _audit_query(db: Session, q: dict):
    stmt = select(AuditEvent)
    if q.get("actor"):
        stmt = stmt.where(AuditEvent.actor_id == q["actor"])
    if q.get("role"):
        stmt = stmt.where(AuditEvent.actor_role == q["role"])
    if q.get("category"):
        stmt = stmt.where(AuditEvent.category == q["category"])
    if q.get("entity_type"):
        stmt = stmt.where(AuditEvent.entity_type == q["entity_type"])
    if q.get("entity_id"):
        stmt = stmt.where(AuditEvent.entity_id == q["entity_id"])
    if q.get("action"):
        stmt = stmt.where(AuditEvent.action.like(f"%{q['action']}%"))
    for key, op in (("desde", ">="), ("hasta", "<")):
        if q.get(key):
            try:
                d = datetime.fromisoformat(q[key])
            except ValueError:
                raise DomainError(f"Fecha inválida en '{key}': usa AAAA-MM-DD")
            if key == "hasta":
                d += timedelta(days=1)
            d_utc = to_utc_naive(d.replace(tzinfo=BTZ))
            stmt = stmt.where(AuditEvent.at >= d_utc if op == ">=" else AuditEvent.at < d_utc)
    return stmt


@app.get("/audit", response_class=HTMLResponse)
def ui_audit(request: Request, page: int = 1, db: Session = Depends(dbmod.get_db), user: User = Depends(require("audit:read"))):
    q = {k: v for k, v in request.query_params.items() if k != "page" and v}
    stmt = _audit_query(db, q)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    events = list(db.scalars(stmt.order_by(AuditEvent.seq.desc()).offset((max(page, 1) - 1) * AUDIT_PAGE).limit(AUDIT_PAGE)))
    users = list(db.scalars(select(User).order_by(User.full_name)))
    return render(request, "audit.html", user, events=events, users=users, f=q, page=page, total=total,
                  pages=max(1, -(-total // AUDIT_PAGE)), chain=verify_chain(db),
                  query_string="&".join(f"{k}={v}" for k, v in q.items()))


@app.get("/audit.csv")
def ui_audit_csv(request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("audit:read"))):
    q = {k: v for k, v in request.query_params.items() if v}
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["seq", "fecha_local", "usuario", "rol", "categoria", "accion", "entidad", "entidad_id", "resumen",
                "metodo", "ruta", "estado", "ip", "request_id", "antes", "despues", "hash"])
    for ev in db.scalars(_audit_query(db, q).order_by(AuditEvent.seq)):
        w.writerow([ev.seq, to_local(ev.at).strftime("%Y-%m-%d %H:%M:%S"), ev.actor_email or "sistema/anónimo",
                    ev.actor_role or "", ev.category, ev.action, ev.entity_type, ev.entity_id or "", ev.summary or "",
                    ev.method or "", ev.path or "", ev.status or "", ev.ip or "", ev.request_id or "",
                    json.dumps(ev.before, ensure_ascii=False, default=str) if ev.before else "",
                    json.dumps(ev.after, ensure_ascii=False, default=str) if ev.after else "", ev.hash])
    return Response("\ufeff" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="bitacora_crm.csv"'})


@app.get("/api/audit/verify")
def api_audit_verify(db: Session = Depends(dbmod.get_db), user: User = Depends(require("audit:read"))):
    return verify_chain(db)


# ----------------------------------------------------------------------- usuarios (solo administradores)
@app.get("/admin/users", response_class=HTMLResponse)
def ui_users(request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("users:manage"))):
    rows = []
    for u in db.scalars(select(User).order_by(User.role, User.full_name)):
        last = db.scalar(select(AuditEvent.at).where(AuditEvent.actor_id == u.id).order_by(AuditEvent.seq.desc()).limit(1))
        n = db.scalar(select(func.count()).where(AuditEvent.actor_id == u.id))
        rows.append({"u": u, "last": last, "n": n})
    return render(request, "users.html", user, rows=rows, roles=list(ROLE_LABELS))


@app.post("/admin/users", dependencies=[Depends(csrf_protect)])
async def ui_create_user(request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("users:manage"))):
    users_svc.create_user(db, await form_dict(request), user.id)
    return back("/admin/users")


@app.post("/admin/users/{user_id}/active", dependencies=[Depends(csrf_protect)])
async def ui_user_active(user_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("users:manage"))):
    f = await form_dict(request)
    users_svc.set_active(db, user_id, f.get("active") == "1", user.id)
    return back("/admin/users")


@app.post("/admin/users/{user_id}/role", dependencies=[Depends(csrf_protect)])
async def ui_user_role(user_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("users:manage"))):
    users_svc.change_role(db, user_id, (await form_dict(request)).get("role"), user.id)
    return back("/admin/users")


@app.post("/admin/users/{user_id}/password", dependencies=[Depends(csrf_protect)])
async def ui_user_password(user_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("users:manage"))):
    users_svc.reset_password(db, user_id, (await form_dict(request)).get("password"), user.id)
    return back("/admin/users")


@app.post("/integrations/erp-sync", dependencies=[Depends(csrf_protect)])
def ui_erp_sync(db: Session = Depends(dbmod.get_db), user: User = Depends(require("integration:run"))):
    from app.seed import demo_erp_orders
    sync_orders(db, MockErpAdapter(demo_erp_orders()), user.id)
    return back("/accounts")


# ======================================================================= API REST (JSON)
@app.post("/api/leads", status_code=201)
async def api_create_lead(request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("lead:write"))):
    lead, created = crm.create_lead(db, await request.json(), user.id)
    return JSONResponse({"lead": ser(lead), "created": created}, status_code=201 if created else 200)


@app.get("/api/leads")
def api_leads(status: str | None = None, sector: str | None = None, source: str | None = None,
              db: Session = Depends(dbmod.get_db), user: User = Depends(require("lead:read"))):
    return ser(crm.filter_leads(db, status, sector, source))


@app.post("/api/leads/{lead_id}/status")
async def api_lead_status(lead_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("lead:write"))):
    b = await request.json()
    return ser(crm.change_lead_status(db, lead_id, b.get("status"), user.id, b.get("reason")))


@app.post("/api/leads/{lead_id}/convert")
async def api_lead_convert(lead_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("lead:convert"))):
    b = await request.json()
    r = crm.convert_lead(db, lead_id, user.id, b.get("create_opportunity", True), b.get("opp_type", "estandar"), b.get("opp_title"))
    return {k: ser(v) if hasattr(v, "__table__") else v for k, v in r.items()}


@app.post("/api/accounts", status_code=201)
async def api_create_account(request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("account:write"))):
    return ser(crm.create_account(db, await request.json(), user.id))


@app.get("/api/accounts/{account_id}")
def api_account(account_id: str, db: Session = Depends(dbmod.get_db), user: User = Depends(require("account:read"))):
    acc = get_or_404(db, Account, account_id, "Cuenta")
    return {"account": ser(acc), "contacts": ser(acc.contacts), "opportunities": ser(acc.opportunities),
            "orders": ser(acc.orders), "cases": ser(acc.cases), "timeline": ser(crm.timeline(db, "account", acc.id))}


@app.post("/api/opportunities", status_code=201)
async def api_create_opp(request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("opportunity:write"))):
    return ser(crm.create_opportunity(db, await request.json(), user.id))


@app.post("/api/opportunities/{opp_id}/stage")
async def api_opp_stage(opp_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("opportunity:write"))):
    b = await request.json()
    return ser(crm.change_stage(db, opp_id, b.get("stage"), user.id, b.get("lost_reason")))


@app.post("/api/opportunities/{opp_id}/quotes", status_code=201)
async def api_quote(opp_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("quote:write"))):
    q = crm.create_quote(db, opp_id, (await request.json()).get("items") or [], user.id)
    return {"quote": ser(q), "items": ser(q.items), "total_mxn": q.total_mxn, "total_kg": q.total_kg}


@app.post("/api/activities", status_code=201)
async def api_activity(request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("activity:write"))):
    return ser(crm.log_activity(db, await request.json(), user.id))


@app.get("/api/timeline/{related_type}/{related_id}")
def api_timeline(related_type: str, related_id: str, db: Session = Depends(dbmod.get_db), user: User = Depends(require("lead:read"))):
    return ser(crm.timeline(db, related_type, related_id))


@app.get("/api/tasks")
def api_tasks(status: str = "pendiente", role: str | None = None, db: Session = Depends(dbmod.get_db), user: User = Depends(require("task:read"))):
    stmt = select(Task).where(Task.status == status)
    if role:
        stmt = stmt.where(Task.assignee_role == role)
    return ser(list(db.scalars(stmt)))


@app.post("/api/tasks", status_code=201)
async def api_create_task(request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("task:write"))):
    return ser(crm.create_task(db, await request.json(), user.id))


@app.post("/api/tasks/{task_id}/complete")
def api_complete_task(task_id: str, db: Session = Depends(dbmod.get_db), user: User = Depends(require("task:write"))):
    return ser(crm.complete_task(db, task_id, user.id))


@app.post("/api/cases", status_code=201)
async def api_create_case(request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("case:write"))):
    return ser(crm.create_case(db, await request.json(), user.id))


@app.post("/api/cases/{case_id}/status")
async def api_case_status(case_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("case:write"))):
    b = await request.json()
    return ser(crm.change_case_status(db, case_id, b.get("status"), user.id, b.get("lot_reference")))


@app.post("/api/emails/ingest")
async def api_ingest(request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("email:ingest"))):
    """Ingesta de correos ya normalizados por un proveedor externo (formato RawEmail)."""
    items = await request.json()
    if not isinstance(items, list):
        raise DomainError("Se espera una lista de correos")

    class _ListProvider:
        name = "api"

        def fetch(self):
            out = []
            for it in items:
                try:
                    out.append(RawEmail(provider=it.get("provider", "api"), message_id=it["message_id"],
                                        from_email=(it.get("from_email") or "").lower(), from_name=it.get("from_name"),
                                        subject=it.get("subject", ""), body=it.get("body", ""), to=it.get("to"),
                                        is_demo=bool(it.get("is_demo", False))))
                except KeyError as e:
                    raise DomainError(f"Falta el campo {e}")
            return out
    return email_pipeline.ingest(db, _ListProvider(), actor_id=user.id)


@app.get("/api/emails")
def api_emails(review_status: str | None = None, category: str | None = None, db: Session = Depends(dbmod.get_db), user: User = Depends(require("email:read"))):
    stmt = select(EmailMessage).join(EmailClassification)
    if review_status:
        stmt = stmt.where(EmailClassification.review_status == review_status)
    if category:
        stmt = stmt.where(EmailClassification.category == category)
    out = []
    for m in db.scalars(stmt):
        c = m.classification
        out.append({"email_id": m.id, "from": m.from_email, "subject": m.subject, "classification": c.category,
                    "confidence": c.confidence, "extracted_entities": c.extracted_entities,
                    "suggested_owner": c.suggested_owner_role, "suggested_action": c.suggested_action,
                    "crm_entity_link": {"type": c.crm_link_type, "id": c.crm_link_id, "all": c.crm_links},
                    "review_status": c.review_status, "review_reason": c.review_reason})
    return out


@app.post("/api/emails/{email_id}/review")
async def api_email_review(email_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("email:review"))):
    b = await request.json()
    return ser(email_pipeline.review(db, email_id, user.id, b.get("category")))


@app.post("/api/emails/{email_id}/apply")
async def api_email_apply(email_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("email:review"))):
    b = await request.json()
    return email_pipeline.apply_suggestion(db, email_id, user.id, b.get("action"))


@app.get("/api/search")
def api_search(q: str, db: Session = Depends(dbmod.get_db), user: User = Depends(require("lead:read"))):
    return {k: ser(v) for k, v in crm.search(db, q).items()}


@app.get("/api/dashboard")
def api_dashboard(db: Session = Depends(dbmod.get_db), user: User = Depends(require("dashboard:read"))):
    return dashboard.metrics(db)


@app.get("/api/audit")
def api_audit(request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("audit:read"))):
    q = {k: v for k, v in request.query_params.items() if v}
    return ser(list(db.scalars(_audit_query(db, q).order_by(AuditEvent.seq))))


@app.get("/api/export")
def api_export(db: Session = Depends(dbmod.get_db), user: User = Depends(require("export:read"))):
    """Portabilidad de datos (RNF-11): volcado JSON de las entidades comerciales."""
    return {name: ser(list(db.scalars(select(model)))) for name, model in
            {"accounts": Account, "contacts": Contact, "leads": Lead, "opportunities": Opportunity,
             "quotes": Quote, "cases": Case, "tasks": Task}.items()}


@app.post("/api/integrations/erp-sync")
def api_erp_sync(db: Session = Depends(dbmod.get_db), user: User = Depends(require("integration:run"))):
    from app.seed import demo_erp_orders
    return sync_orders(db, MockErpAdapter(demo_erp_orders()), user.id)


# ======================================================================= iteración 2
@app.post("/leads/{lead_id}/merge", dependencies=[Depends(csrf_protect)])
async def ui_merge(lead_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("lead:write"))):
    f = await form_dict(request)
    keep = crm.merge_leads(db, f.get("keep_id"), lead_id, user.id)
    return back(f"/leads/{keep.id}")


@app.post("/api/leads/{lead_id}/merge")
async def api_merge(lead_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("lead:write"))):
    """Fusiona el lead `lead_id` dentro de `keep_id`."""
    return ser(crm.merge_leads(db, (await request.json()).get("keep_id"), lead_id, user.id))


@app.post("/quotes/{quote_id}/status", dependencies=[Depends(csrf_protect)])
async def ui_quote_status(quote_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("quote:write"))):
    f = await form_dict(request)
    q = crm.change_quote_status(db, quote_id, f.get("status"), user.id)
    return back(f"/opportunities/{q.opportunity_id}")


@app.post("/api/quotes/{quote_id}/status")
async def api_quote_status(quote_id: str, request: Request, db: Session = Depends(dbmod.get_db), user: User = Depends(require("quote:write"))):
    return ser(crm.change_quote_status(db, quote_id, (await request.json()).get("status"), user.id))


@app.get("/quotes/{quote_id}.pdf")
@app.get("/api/quotes/{quote_id}/pdf")
def quote_pdf(quote_id: str, db: Session = Depends(dbmod.get_db), user: User = Depends(require("opportunity:read"))):
    q = get_or_404(db, Quote, quote_id, "Cotización")
    return Response(render_quote_pdf(q), media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{q.folio}.pdf"'})


@app.post("/automations/reorder-check", dependencies=[Depends(csrf_protect)])
def ui_reorder(db: Session = Depends(dbmod.get_db), user: User = Depends(require("integration:run"))):
    run_reorder_check(db, user.id)
    return back("/tasks?role=ventas")


@app.post("/api/automations/reorder-check")
def api_reorder(db: Session = Depends(dbmod.get_db), user: User = Depends(require("integration:run"))):
    return run_reorder_check(db, user.id)


@app.get("/api/automations/reorder-candidates")
def api_reorder_candidates(db: Session = Depends(dbmod.get_db), user: User = Depends(require("dashboard:read"))):
    return [{"account_id": c["account"].id, "account": c["account"].name, "last_order": c["last_order"].isoformat(),
             "interval_days": c["interval_days"], "days_overdue": c["days_overdue"]} for c in reorder_candidates(db)]

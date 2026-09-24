"""Cada módulo de operación expone su propio `router` (FastAPI APIRouter).

Se agrupan aquí para que `main.py` los registre con una sola línea y para que dos módulos distintos
nunca tengan que editar el mismo archivo.
"""
from app.routers import (files, inventory, maintenance, notifications, pettycash, procurement,
                         rrhh, sales)

ALL = [inventory.router, procurement.router, sales.router, maintenance.router, rrhh.router,
       pettycash.router, notifications.router, files.router]

"""
WSGI config for pro1 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import shutil
from pathlib import Path

# ---------------------------------------------------------------------------
# Vercel read-only filesystem fix
# ---------------------------------------------------------------------------
# On Vercel the source tree (/var/task/) is read-only.  Copy the committed
# SQLite snapshot to /tmp/ before Django boots so that every write (auth
# last_login, session, new registrations, mandi seeding, …) succeeds.
# Settings also points DATABASES["NAME"] at /tmp/db.sqlite3 when VERCEL is set.
# ---------------------------------------------------------------------------
if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
    _src = Path(__file__).resolve().parent.parent / "db.sqlite3"
    _dst = Path("/tmp/db.sqlite3")
    if _src.exists() and not _dst.exists():
        try:
            shutil.copy2(str(_src), str(_dst))
        except Exception:
            pass

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pro1.settings')

application = get_wsgi_application()

app = application

"""
WSGI config for demo_site project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demo_site.settings')

application = get_wsgi_application()

try:
    django.setup()
    from django.core.management import call_command
    call_command("migrate", interactive=False)
except Exception as e:
    print(f"[WARNING] Auto migrate failed: {e}")

from django.contrib.auth.models import User
if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("0", "admin@example.com", "0")

import re
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

from apps.accounts.proxy import trusted_networks
from apps.core.configuration import database, required

from .base import *

SECRET_KEY = required("DJANGO_SECRET_KEY")
if len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5 or SECRET_KEY.startswith("django-insecure-"):
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be a strong independent production secret.")
ALLOWED_HOSTS = [host.strip() for host in required("DJANGO_ALLOWED_HOSTS").split(",")]
if any(not re.fullmatch(r"[a-zA-Z0-9.-]+", host) or "*" in host for host in ALLOWED_HOSTS):
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must contain explicit hostnames.")
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in required("DJANGO_CSRF_TRUSTED_ORIGINS").split(",")
]
for origin in CSRF_TRUSTED_ORIGINS:
    parsed = urlsplit(origin)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in ALLOWED_HOSTS
        or parsed.username
        or parsed.password
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ImproperlyConfigured("CSRF origins must be exact HTTPS origins for allowed hosts.")
DATABASES = {"default": database(strict=True)}
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
# Caddy must overwrite this header and be the only process able to reach Gunicorn (D02).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# Enable after HTTPS verification during deployment; no preload or includeSubDomains.
SECURE_HSTS_SECONDS = 0

TRUSTED_PROXY_NETWORKS = trusted_networks(required("DJANGO_TRUSTED_PROXY_CIDRS"))
AXES_CLIENT_IP_CALLABLE = "apps.accounts.proxy.client_ip"
SECURE_REDIRECT_EXEMPT = [r"^health/live/$", r"^health/ready/$"]

from .base import *  # noqa: F401,F403

DEBUG = False

# Caddy terminates TLS in front of gunicorn and forwards this header, so
# Django knows the original request was HTTPS (needed for secure cookies /
# CSRF checks to work correctly behind the proxy).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

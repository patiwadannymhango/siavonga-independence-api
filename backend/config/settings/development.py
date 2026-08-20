from .base import *  # noqa: F401,F403

DEBUG = True

# Emails print to the console instead of needing real SMTP credentials to
# run locally. Override EMAIL_BACKEND in backend/.env if you want to test
# real Gmail SMTP delivery from your machine.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

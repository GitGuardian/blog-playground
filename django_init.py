# from https://blog.theodo.com/2020/11/django-jupyter-vscode-setup/

# A script that's needed to setup django if it's not already running on a server.
# Without this, you won't be able to import django modules
import os

import django


os.environ["DJANGO_SETTINGS_MODULE"] = "playground.settings"
#  Allow queryset filtering asynchronously when running in a Jupyter notebook
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# This is for setting up django
django.setup()

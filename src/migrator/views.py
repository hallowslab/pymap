# Create your views here.
# from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.contrib.auth.views import LoginView


def index(request):
    return TemplateResponse(request, "sync.html", {})


def tasks(request):
    return TemplateResponse(request, "tasks.html", {})


class CustomLoginView(LoginView):
    template_name = "login.html"
    success_url = "/"

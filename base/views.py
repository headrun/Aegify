from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required(login_url='/admin/login/')
def home(response):
    try:
        return render(response, "home.html", {})
    except:
        return HttpResponse("<h1>Not Found</h1><p>The requested resource was not found on this server.</p>")

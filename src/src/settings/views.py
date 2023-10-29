from django.shortcuts import render

# Create your views here.
def hello_world(request, *args, **kwargs):
    return render(request, "<h1>Hello world</h1>")
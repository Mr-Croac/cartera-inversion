from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

def registro(request):
    if request.method == "POST":
        formulario = UserCreationForm(request.POST)
        if formulario.is_valid():
            usuario = formulario.save()      # crea el usuario en la BD
            login(request, usuario)          # inicia sesión automáticamente
            return redirect("inicio")
    else:
        formulario = UserCreationForm()

    return render(request, "usuarios/registro.html", {"formulario": formulario})
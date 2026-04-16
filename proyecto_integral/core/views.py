from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'core/home.html')

def registro(request):
    return render(request, 'core/registro.html')

def login_view(request):
    return render(request, 'core/login.html')

def perfil_artista(request, artista_id):
    return render(request, 'core/perfil_artista.html', {'artista_id': artista_id})

def perfil_cliente(request, cliente_id):
    return render(request, 'core/perfil_cliente.html', {'cliente_id': cliente_id})
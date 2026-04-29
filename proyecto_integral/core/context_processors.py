from .models import ComisionGuardada

def comisiones_guardadas(request):
    if request.user.is_authenticated and request.user.es_cliente():
        guardadas = ComisionGuardada.objects.filter(cliente=request.user).values_list('comision_id', flat=True)
        return {'comisiones_guardadas_ids': list(guardadas)}
    return {'comisiones_guardadas_ids': []}
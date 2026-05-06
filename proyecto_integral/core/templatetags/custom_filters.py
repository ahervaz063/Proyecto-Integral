# core/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def batch(iterable, size):
    """
    Agrupa una lista en sublistas de tamaño 'size'.
    Ejemplo: lista|batch:4  → [[item1,item2,item3,item4], [item5,item6,item7,item8], ...]
    """
    if not iterable:
        return []
    size = int(size)
    return [iterable[i:i + size] for i in range(0, len(iterable), size)]
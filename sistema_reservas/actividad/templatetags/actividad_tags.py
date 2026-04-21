from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Obtiene un valor de un diccionario usando una clave variable.
    Uso en template: {{ contadores|get_item:modulo_key }}
    """
    if isinstance(dictionary, dict):
        valor = dictionary.get(key)
        return valor if valor is not None else ''
    return ''


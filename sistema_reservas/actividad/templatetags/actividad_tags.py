from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Obtiene un valor de un diccionario usando una clave variable.
    Uso en template: {{ contadores|get_item:modulo_key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, 0)
    return 0

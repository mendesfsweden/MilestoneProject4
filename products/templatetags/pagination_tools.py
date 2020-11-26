from django import template


register = template.Library()


@register.filter()
def get_full_path(request):
    return request.get_full_path()

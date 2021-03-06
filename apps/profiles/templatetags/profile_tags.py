from django import template
from apps.plus_permissions.api import secure_wrap, TemplateSecureWrapper
from apps.plus_lib.utils import main_hub_name

from apps.plus_permissions.models import GenericReference
from apps.plus_groups.models import TgGroup
register = template.Library()

def show_profile(context, profile):
    if isinstance(profile, GenericReference):
        profile = profile.obj
    try:
        homehub = profile.homeplace.tggroup_set.filter(level='member')[0]
    except:
        homehub = TgGroup.objects.get(id=1)
        
    #profile = TemplateSecureWrapper(secure_wrap(profile, context['request'].user, interface_names=['Viewer'], required_interfaces=['Viewer']))
    user = profile.user
    return {"homehub":homehub, "profile":profile, "user": user, "main_hub_name":main_hub_name()}
register.inclusion_tag("profile_item.html", takes_context=True)(show_profile)


def clear_search_url(request):
    getvars = request.GET.copy()
    if 'search' in getvars:
        del getvars['search']
    if len(getvars.keys()) > 0:
        return "%s?%s" % (request.path, getvars.urlencode())
    else:
        return request.path
register.simple_tag(clear_search_url)



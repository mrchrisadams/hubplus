
from django.conf.urls.defaults import *


urlpatterns = patterns('',
                       url(r'^patch_in_profiles$', 'plus_permissions.views.patch_in_profiles', name='hubspace_profile_patch'),
                       url(r'^patch_in_groups$', 'plus_permissions.views.patch_in_groups', name='hubspace_group_patch'),
                       url(r'^edit/$', 'plus_permissions.views.json_slider_group', name="hubspace permissions editor"),
                       )

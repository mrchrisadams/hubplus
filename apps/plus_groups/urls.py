from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^(?P<group_id>[\w\._-]+)/$', 'plus_groups.views.group', name='group'),
    url(r'^join/(?P<resource_id>[\w\._-]+)/$', 'plus_groups.views.join', name='join_group'),
    url(r'^apply/(?P<resource_id>[\w\._-]+)/$', 'plus_groups.views.apply', name='apply_group'),
    url(r'^leave/(?P<resource_id>[\w\._-]+)/$', 'plus_groups.views.leave', name='leave_group'),

    url(r'^$', 'plus_groups.views.groups', name='groups'),

)


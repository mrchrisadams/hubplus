from apps.hubspace_compatibility.models import TgGroup
from django.contrib.auth.models import User

from apps.hubspace_compatibility.models import Location
from django.db import models

from apps.plus_permissions.site import Site

def get_site(user) :
    ss = Site.objects.all()
    if len(ss) > 0 :
        return ss[0]
    s = Site()
    s.save() 

    admin = get_all_members_group().get_admin_group()
    # permission-wise, the site lives under the all_members_admin group
    s.acquires_from(admin)

    from apps.plus_permissions.interfaces import secure_wrap
    return secure_wrap(s, user)


def get_or_create_root_location():
    root_location, created = Location.objects.get_or_create(name='HubPlus')
    if created:
        root_location.save()
    return root_location


def get_admin_user():
    try:
        admin_user =  User.objects.filter(username='admin')[0]
    except IndexError:
        admin_user = User(username='admin', email_address='tom.salfield@the-hub.net', password='blah')
        admin_user.save()
    return admin_user

def set_anonymous_group():
    admin_user = get_admin_user()
    return TgGroup.objects.get_or_create(group_name='anonymous', display_name='World', place=get_or_create_root_location(), level='public', user=admin_user)


def get_anonymous_group():
    anonymous_group = TgGroup.objects.filter(group_name="anonymous")
    if not anonymous_group:
        anonymous_group, created = set_anonymous_group()
    else :
        anonymous_group = anonymous_group[0] # filter returns a QuerySet
    return anonymous_group


def get_anon_user():
    try:
        anon_user =  User.objects.filter(username='anon')[0]
    except IndexError:
        anon_user = User(username='anon', email_address='anon@null.com')
        anon_user.save()
        get_anonymous_group().add_member(anon_user)
    return anon_user

def set_all_members_group():
    admin_user = get_admin_user()
    return TgGroup.objects.get_or_create(group_name='all_members', display_name='All Members', place=get_or_create_root_location(), level='member', user=admin_user)
           
def get_all_members_group():
    all_members = TgGroup.objects.filter(group_name="all_members")
    if not all_members:
        all_members, created = set_all_members_group()
    else :
        all_members = all_members[0] # filter returns a QuerySet
    return all_members



class CreatorMarker(models.Model) :
    """ This class is only for a fake "agent" which is used to represent "query for the creator of this content_type" """
    pass

def get_creator_agent() :
    if CreatorMarker.objects.count() > 0 :
        return CreatorMarker.objects.all()[0].get_ref()
    c = CreatorMarker()
    c.save()
    return c.get_ref()



    


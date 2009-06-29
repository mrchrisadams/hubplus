from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.db import transaction

from friends.forms import InviteFriendForm
from friends.models import FriendshipInvitation, Friendship

from microblogging.models import Following

from apps.plus_permissions.Profile import *  # Essential to get signals working at the moment.
from profiles.models import Profile, HostInfo
  
from profiles.models import get_or_create_interest, get_or_create_need, get_or_create_skill
from profiles.forms import ProfileForm, HostInfoForm

from avatar.templatetags.avatar_tags import avatar

from apps.plus_lib.models import DisplayStatus, add_edit_key
from apps.plus_permissions.models import PermissionSystem, get_permission_system, SecurityTag, PlusPermissionsNoAccessException

from django.contrib.auth.decorators import login_required

add_edit_key(User)
add_edit_key(Profile)
add_edit_key(HostInfo)

#from gravatar.templatetags.gravatar import gravatar as avatar

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

def profiles(request, template_name="profiles/profiles.html"):
    users = User.objects.all().order_by("-date_joined")
    search_terms = request.GET.get('search', '')
    order = request.GET.get('order')
    if not order:
        order = 'date'
    if search_terms:
        users = users.filter(username__icontains=search_terms)
    if order == 'date':
        users = users.order_by("-date_joined")
    elif order == 'name':
        users = users.order_by("username")
    return render_to_response(template_name, {
        'users':users,
        'order' : order,
        'search_terms' : search_terms
    }, context_instance=RequestContext(request))

def profile(request, username, template_name="profiles/profile.html"):
    other_user = get_object_or_404(User, username=username)
    ps = get_permission_system()

    try:
        p = other_user.get_profile()
    except Exception : 
        other_user.save()
        p = other_user.get_profile()
        p.save()

    if request.user.is_authenticated():

        is_friend = Friendship.objects.are_friends(request.user, other_user)
        is_following = Following.objects.is_following(request.user, other_user)
        other_friends = Friendship.objects.friends_for_user(other_user)
        if request.user == other_user:
            is_me = True
        else:
            is_me = False
    else:
        other_friends = []
        is_friend = False
        is_me = False
        is_following = False
    
    if is_friend:
        invite_form = None
        previous_invitations_to = None
        previous_invitations_from = None
    else:
        if request.user.is_authenticated() and request.method == "POST":
            if request.POST["action"] == "invite":
                invite_form = InviteFriendForm(request.user, request.POST)
                if invite_form.is_valid():
                    invite_form.save()
            else:
                invite_form = InviteFriendForm(request.user, {
                    'to_user': username,
                    'message': ugettext("Let's be friends!"),
                })
                if request.POST["action"] == "accept": # @@@ perhaps the form should just post to friends and be redirected here
                    invitation_id = request.POST["invitation"]
                    try:
                        invitation = FriendshipInvitation.objects.get(id=invitation_id)
                        if invitation.to_user == request.user:
                            invitation.accept()
                            request.user.message_set.create(message=_("You have accepted the friendship request from %(from_user)s") % {'from_user': invitation.from_user})
                            is_friend = True
                            other_friends = Friendship.objects.friends_for_user(other_user)
                    except FriendshipInvitation.DoesNotExist:
                        pass
        else:
            invite_form = InviteFriendForm(request.user, {
                'to_user': username,
                'message': ugettext("Let's be friends!"),
            })
    previous_invitations_to = FriendshipInvitation.objects.filter(to_user=other_user, from_user=request.user)
    previous_invitations_from = FriendshipInvitation.objects.filter(to_user=request.user, from_user=other_user)
    
    if is_me:
        if request.method == "POST":
            if request.POST["action"] == "update":
                profile_form = ProfileForm(request.POST, instance=other_user.get_profile())
                if profile_form.is_valid():
                    profile = profile_form.save(commit=False)
                    profile.user = other_user
                    profile.save()
            else:
                profile_form = ProfileForm(instance=other_user.get_profile())
        else:
            profile_form = ProfileForm(instance=other_user.get_profile())
    else:
        profile_form = None

    if ps.has_access(request.user,other_user.get_profile(),ps.get_interface_factory().get_id(Profile,'Viewer')) :

        dummy_status = DisplayStatus("Dummy Status"," about 3 hours ago")

        return render_to_response(template_name, {
                "profile_form": profile_form,
                "is_me": is_me,
                "is_friend": is_friend,
                "is_following": is_following,
                "other_user": other_user,
                "profile":other_user.get_profile(),
                "other_friends": other_friends,
                "invite_form": invite_form,
                "previous_invitations_to": previous_invitations_to,
                "previous_invitations_from": previous_invitations_from,
                "head_title" : "Profile for %s" % other_user.get_profile().name,
                "head_title_status" : dummy_status,
                "host_info" : other_user.get_profile().get_host_info(),
                
                }, context_instance=RequestContext(request))

    else :
        return HttpResponse("""
<p>You don't have permission to see or do this.</p>

<p>You are %s</p>

<p>This is the profile for %s via interface %s</p>

Current Permissions
<ul>
%s
</ul>
...
""" % (request.user, other_user.get_profile(),'Viewer', 
       ''.join([
          ('<li>%s</li>'%x) for x in ps.get_permissions_for(other_user.get_profile())
          ]),
       ), status=401 )

def our_profile_permission_test(fn) :
    """ Trying to put our permission testing into a decorator """
    def our_fn(request,username,*args,**kwargs) :
        ps = get_permission_system()
        other_user = get_object_or_404(User,username=username)
        profile = other_user.get_profile()
        if not ps.has_access(request.user,profile,ps.get_interface_id(Profile,'Editor')) :
            return HttpResponse("You don't have permission to do that to %s, you are %s" % (username,request.user),status=401)
        else :
            return fn(request,other_user,profile,*args,**kwargs)
    return our_fn

@login_required
@transaction.commit_on_success
def update_profile_form(request,username) :
    """ Get a prefilled basic form for the profile """
    other_user = get_object_or_404(User,username=username)
    p = other_user.get_profile()
    ps= get_permission_system()
    if not ps.has_access(request.user,p,ps.get_interface_id(Profile,'Editor')) :
        raise PluPermissionsNoAccessException(Profile,p.pk,'update_profile_form')
    else :
        profile_form = ProfileForm(request.POST, p)

@login_required
@our_profile_permission_test
def add_profile_interest(request,other_user,profile) :
    """ This is actually a way to add interests """
    interest,created = get_or_create_interest(request.POST['interest'])
    profile.add_interest(interest)
    return HttpResponseRedirect('/profiles/%s/' % request.user.username)

@login_required
@our_profile_permission_test
@transaction.commit_on_success
def add_profile_skill(request,other_user,profile) :
    """ This is actually a way to add skills """
    skill,created = get_or_create_skill(request.POST['skill'])
    profile.add_skill(skill)
    return HttpResponseRedirect('/profiles/%s/' % request.user.username)

@login_required
@our_profile_permission_test
@transaction.commit_on_success
def add_profile_need(request,other_user,profile) :
    """ This is actually a way to add needs """
    need, created = get_or_create_need(request.POST['need'])
    profile.add_need(need)
    return HttpResponseRedirect('/profiles/%s/' % request.user.username)


@login_required
@transaction.commit_on_success
def profile_field(request,username,fieldname,*args,**kwargs) :
    """ Get the value of one field from the user profile, so we can write an ajaxy editor """
    other_user = get_object_or_404(User,username=username)
    ps = get_permission_system()
    p = other_user.get_profile()
    if not ps.has_access(request.user,p,ps.get_interface_id(Profile,'Editor')) :
        return HttpResponse("You aren't authorized to access %s in %s for %s. You are %s" % (fieldname,kwargs['class'],username,request.user),status=401)
    else :
        if kwargs['class'] == 'Profile' :
            return one_model_field(request,p,ProfileForm,fieldname, kwargs.get('default', ''))
        elif kwargs['class'] == 'HostInfo' :
            return one_model_field(request,p.get_host_info(),HostInfoForm,fieldname, kwargs.get('default', ''))


def one_model_field(request, object, formClass, fieldname, default) :
    val = getattr(object, fieldname)
    if not request.POST:
        return HttpResponse("%s" % val, mimetype="text/plain")

    field_validator = formClass.base_fields[fieldname]
    new_val = request.POST['value']
    try:
        field_validator.clean(new_val)
    except ValidationError, e:
        return HttpResponse('%s' % e, status=500)

    try:
        setattr(object, fieldname, new_val)
        object.save()
    except Exception, e :
        return HttpResponse('%s' % e, status=500)
    new_val = new_val and new_val or default
    return HttpResponse("%s" % new_val, mimetype='text/plain')



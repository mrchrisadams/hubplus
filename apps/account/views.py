from django.conf import settings
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404
from django.db.models import Q
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.db import models

from django.contrib.auth.models import AnonymousUser

from apps.plus_permissions.default_agents import get_anonymous_group, get_anon_user

from apps.plus_groups.models import TgGroup

from account.utils import get_default_redirect
from account.models import OtherServiceInfo
from account.forms import SignupForm, AddEmailForm, LoginForm, \
    ChangePasswordForm, SetPasswordForm, ResetPasswordForm, \
    ChangeTimezoneForm, ChangeLanguageForm, TwitterForm, ResetPasswordKeyForm

from forms import HubPlusApplicationForm

from emailconfirmation.models import EmailAddress, EmailConfirmation

from apps.microblogging.forms import TweetForm
from apps.microblogging.views import TweetInstance
from microblogging.utils import twitter_account_for_user, twitter_verify_credentials

from django.utils.translation import ugettext_lazy as _


def home(request, success_url=None):
    """
    Let's base homepage on the microblog personal now.
    """
    if not request.user.is_authenticated():
        return render_to_response('home/home.html', {}, context_instance=RequestContext(request))

    twitter_account = twitter_account_for_user(request.user)
    template_name = "home/home_logged_in.html"
    form_class = TweetForm

    if request.method == "POST":
        form = form_class(request.user, request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            form.save()
            if request.POST.get("pub2twitter", False):
                twitter_account.PostUpdate(text)
            if success_url is None:
                success_url = reverse('home')
            return HttpResponseRedirect(success_url)
        reply = None
    else:
        reply = request.GET.get("reply", None)
        form = form_class()
        if reply:
            form.fields['text'].initial = u"@%s " % reply
    tweets = TweetInstance.objects.tweets_for(request.user).order_by("-sent")
    return render_to_response(template_name, {
        "head_title" : "Home",
        "head_title_status" : '',
        "form": form,
        "reply": reply,
        "tweets": tweets,
        "twitter_authorized": twitter_verify_credentials(twitter_account),
    }, context_instance=RequestContext(request))



def login(request, form_class=LoginForm,
        template_name="account/login.html", success_url=None,
        associate_openid=False, openid_success_url=None, url_required=False):

    if success_url is None:
        success_url = get_default_redirect(request)

    message = ""
    if request.method == "POST" and not url_required:

        form = form_class(request.POST)
        if form.login(request):
            if associate_openid and association_model is not None:
                for openid in request.session.get('openids', []):
                    assoc, created = UserOpenidAssociation.objects.get_or_create(
                        user=form.user, openid=openid.openid
                    )
                success_url = openid_success_url or success_url
            return HttpResponseRedirect(success_url)
        else:
            message = _('The email address or password you provided does not match our records.')
    
    form = form_class()

    return render_to_response(template_name, {

        "form": form,
        "url_required": url_required,
        "message" : message,
    }, context_instance=RequestContext(request))


def signup(request, key, form_class=SignupForm,
        template_name="account/signup.html", success_url=None):


    if success_url is None:
        success_url = get_default_redirect(request)
    if request.method == "POST":
        print "received post"
        form = form_class(request.POST)
        print form
        if form.is_valid():
            username, password = form.save()
            user = authenticate(username=username, password=password)
            auth_login(request, user)
            request.user.message_set.create(
                message=_("Successfully logged in as %(username)s.") % {
                'username': user.username
            })
            return HttpResponseRedirect(success_url)
        else :
            print "invalid form"
    else:
        form = form_class()

    return render_to_response(template_name, {
        "form": form,
    }, context_instance=RequestContext(request))

def email(request, form_class=AddEmailForm,
        template_name="account/email.html"):
    if request.method == "POST" and request.user.is_authenticated():
        if request.POST["action"] == "add":
            add_email_form = form_class(request.user, request.POST)
            if add_email_form.is_valid():
                add_email_form.save()
                add_email_form = form_class() # @@@
        else:
            add_email_form = form_class()
            if request.POST["action"] == "send":
                email = request.POST["email"]
                try:
                    email_address = EmailAddress.objects.get(
                        user=request.user,
                        email=email,
                    )
                    request.user.message_set.create(
                        message="Confirmation email sent to %s" % email)
                    EmailConfirmation.objects.send_confirmation(email_address)
                except EmailAddress.DoesNotExist:
                    pass
            elif request.POST["action"] == "remove":
                email = request.POST["email"]
                try:
                    email_address = EmailAddress.objects.get(
                        user=request.user,
                        email=email
                    )
                    email_address.delete()
                    request.user.message_set.create(
                        message="Removed email address %s" % email)
                except EmailAddress.DoesNotExist:
                    pass
            elif request.POST["action"] == "primary":
                email = request.POST["email"]
                email_address = EmailAddress.objects.get(
                    user=request.user,
                    email=email,
                )
                email_address.set_as_primary()
    else:
        add_email_form = form_class()
    return render_to_response(template_name, {
        "add_email_form": add_email_form,
    }, context_instance=RequestContext(request))
email = login_required(email)

def password_change(request, form_class=ChangePasswordForm,
        template_name="account/password_change.html"):
    if not request.user.password:
        return HttpResponseRedirect(reverse("acct_passwd_set"))
    if request.method == "POST":
        password_change_form = form_class(request.user, request.POST)
        if password_change_form.is_valid():
            password_change_form.save()
            password_change_form = form_class(request.user)
    else:
        password_change_form = form_class(request.user)
    return render_to_response(template_name, {
        "password_change_form": password_change_form,
    }, context_instance=RequestContext(request))
password_change = login_required(password_change)

def password_set(request, form_class=SetPasswordForm,
        template_name="account/password_set.html"):
    if request.user.password:
        return HttpResponseRedirect(reverse("acct_passwd"))
    if request.method == "POST":
        password_set_form = form_class(request.user, request.POST)
        if password_set_form.is_valid():
            password_set_form.save()
            return HttpResponseRedirect(reverse("acct_passwd"))
    else:
        password_set_form = form_class(request.user)
    return render_to_response(template_name, {
        "password_set_form": password_set_form,
    }, context_instance=RequestContext(request))
password_set = login_required(password_set)

def password_delete(request, template_name="account/password_delete.html"):
    # prevent this view when openids is not present or it is empty.
    if not request.user.password or \
        (not hasattr(request, "openids") or \
            not getattr(request, "openids", None)):
        return HttpResponseForbidden()
    if request.method == "POST":
        request.user.password = u""
        request.user.save()
        return HttpResponseRedirect(reverse("acct_passwd_delete_done"))
    return render_to_response(template_name, {
    }, context_instance=RequestContext(request))
password_delete = login_required(password_delete)

def password_reset(request, form_class=ResetPasswordForm,
        template_name="account/password_reset.html",
        template_name_done="account/password_reset_done.html"):
    if request.method == "POST":
        password_reset_form = form_class(request.POST)
        if password_reset_form.is_valid():
            email = password_reset_form.save()
            return render_to_response(template_name_done, {
                "email": email,
            }, context_instance=RequestContext(request))
    else:
        password_reset_form = form_class()
    
    return render_to_response(template_name, {
        "password_reset_form": password_reset_form,
    }, context_instance=RequestContext(request))
    
def password_reset_from_key(request, key, form_class=ResetPasswordKeyForm,
        template_name="account/password_reset_from_key.html"):
    if request.method == "POST":
        password_reset_key_form = form_class(request.POST)
        if password_reset_key_form.is_valid():
            password_reset_key_form.save()
            password_reset_key_form = None
    else:
        password_reset_key_form = form_class(initial={"temp_key": key})
    
    return render_to_response(template_name, {
        "form": password_reset_key_form,
    }, context_instance=RequestContext(request))
    

def timezone_change(request, form_class=ChangeTimezoneForm,
        template_name="account/timezone_change.html"):
    if request.method == "POST":
        form = form_class(request.user, request.POST)
        if form.is_valid():
            form.save()
    else:
        form = form_class(request.user)
    return render_to_response(template_name, {
        "form": form,
    }, context_instance=RequestContext(request))
timezone_change = login_required(timezone_change)

def language_change(request, form_class=ChangeLanguageForm,
        template_name="account/language_change.html"):
    if request.method == "POST":
        form = form_class(request.user, request.POST)
        if form.is_valid():
            form.save()
            next = request.META.get('HTTP_REFERER', None)
            return HttpResponseRedirect(next)
    else:
        form = form_class(request.user)
    return render_to_response(template_name, {
        "form": form,
    }, context_instance=RequestContext(request))
language_change = login_required(language_change)

def other_services(request, template_name="account/other_services.html"):
    from microblogging.utils import twitter_verify_credentials
    twitter_form = TwitterForm(request.user)
    twitter_authorized = False
    if request.method == "POST":
        twitter_form = TwitterForm(request.user, request.POST)

        if request.POST['actionType'] == 'saveTwitter':
            if twitter_form.is_valid():
                from microblogging.utils import twitter_account_raw
                twitter_account = twitter_account_raw(
                    request.POST['username'], request.POST['password'])
                twitter_authorized = twitter_verify_credentials(
                    twitter_account)
                if not twitter_authorized:
                    request.user.message_set.create(
                        message="Twitter authentication failed")
                else:
                    twitter_form.save()
    else:
        from microblogging.utils import twitter_account_for_user
        twitter_account = twitter_account_for_user(request.user)
        twitter_authorized = twitter_verify_credentials(twitter_account)
        twitter_form = TwitterForm(request.user)
    return render_to_response(template_name, {
        "twitter_form": twitter_form,
        "twitter_authorized": twitter_authorized,
    }, context_instance=RequestContext(request))
other_services = login_required(other_services)

def other_services_remove(request):
    # TODO: this is a bit coupled.
    OtherServiceInfo.objects.filter(user=request.user).filter(
        Q(key="twitter_user") | Q(key="twitter_password")
    ).delete()
    request.user.message_set.create(message=ugettext(u"Removed twitter account information successfully."))
    return HttpResponseRedirect(reverse("acct_other_services"))
other_services_remove = login_required(other_services_remove)



def apply(request, form_class=HubPlusApplicationForm,
        template_name="account/apply_form.html"):

    user = request.user
    if user.__class__ == AnonymousUser :
        user = get_anon_user()
        
    # XXX there's a dedicated function for this, replace
    hubs = TgGroup.objects.filter(level='member').exclude(place__name=settings.VIRTUAL_HUB_NAME)

    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            contact, application = form.save(user)
            return render_to_response('plus_contacts/application_thanks.html',{
                    'group' : form.cleaned_data['group'],
                    "head_title" : 'Thanks for your application',
                    "head_title_status" : '',
 
            },context_instance=RequestContext(request))

        else :
            print "invalid form"
    else:
        form = form_class()
    return render_to_response(template_name, {
        "form": form,
        "hubs":hubs,
        "head_title": "Like to join us?",
        "head_title_status" : '',
 
    }, context_instance=RequestContext(request))


    


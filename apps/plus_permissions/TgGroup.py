
from django.db import models

from models import Interface, Slider, SliderOption, SecurityTag, PermissionManager
from models import get_permission_system, default_admin_for, InterfaceReadProperty, InterfaceWriteProperty

from apps.hubspace_compatibility.models import TgGroup

from django.db.models.signals import post_save

import ipdb

# Here's the wrapping we have to put around it. 

def read_interface(name,id) :
    class ReadInterface(Interface) : 
        @classmethod
        def get_id(self):
            return id
    setattr(ReadInterface, name, InterfaceReadProperty(name))
    return ReadInterface
        
class TgGroupViewer(Interface) : 

    pk = InterfaceReadProperty('pk')
    about = InterfaceReadProperty('about')
    location = InterfaceReadProperty('location')
    website = InterfaceReadProperty('website')
    display_name = InterfaceReadProperty('display_name')
    groupextras = InterfaceReadProperty('groupextras')

    @classmethod
    def get_id(self) : 
        return 'TgGroup.Viewer'

#example from Profile
#ProfileEmailAddressViewer = read_interface('email_address','Profile.EmailAddressViewer')


class TgGroupEditor(Interface) : 
    pk = InterfaceReadProperty('pk')
    about = InterfaceWriteProperty('about')
    location = InterfaceWriteProperty('location')
    website = InterfaceWriteProperty('website')

    display_name = InterfaceWriteProperty('display_name')
    
    @classmethod
    def get_id(self) :
        return 'TgGroup.Editor'



class TgGroupApply(Interface):
    pk = InterfaceReadProperty('pk')
    apply = InterfaceCallProperty('apply')

    @classmethod
    def get_id(self) :
        return 'TgGroup.Apply'   

class TgGroupJoin(Interface):
    pk = InterfaceReadProperty('pk')
    join = InterfaceCallProperty('join')

    @classmethod
    def get_id(self) :
        return 'TgGroup.Join'   



class TgGroupInviteMember(Interface):
    pk = InterfaceReadProperty('pk')
    invite_member = InterfaceCallProperty('invite_member')

    @classmethod
    def get_id(self) :
        return 'TgGroup.InviteMember'   

class TgGroupAcceptMember(Interface):
    pk = InterfaceReadProperty('pk')
    accept_member = InterfaceCallProperty('accept_member')

    @classmethod
    def get_id(self) :
        return 'TgGroup.AcceptMember'   



class TgGroupAddMember(Interface):
    pk = InterfaceReadProperty('pk')
    add_member = InterfaceCallProperty('add_member')

    @classmethod
    def get_id(self) :
        return 'TgGroup.AddMember'   

class TgGroupRemoveMember(Interface):
    pk = InterfaceReadProperty('pk')
    remove_member = InterfaceCallProperty('remove_member')

    @classmethod
    def get_id(self) :
        return 'TgGroup.RemoveMember'   




class TgGroupPermissionManager(PermissionManager) :
    def register_with_interface_factory(self,interface_factory) :
        self.interface_factory = interface_factory
        interface_factory.add_type(TgGroup)
        interface_factory.add_interface(TgGroup,'Viewer',TgGroupViewer)
        interface_factory.add_interface(TgGroup,'Editor',TgGroupEditor)

        interface_factory.add_interface(TgGroup,'Apply',TgGroupApply)
        interface_factory.add_interface(TgGroup,'Join',TgGroupJoin)
        interface_factory.add_interface(TgGroup,'InviteMember',TgGroupInviteMember)
        interface_factory.add_interface(TgGroup,'AcceptMember',TgGroupAcceptMember)
        interface_factory.add_interface(TgGroup,'AddMember',TgGroupAddMember)
        interface_factory.add_interface(TgGroup,'RemoveMember',TgGroupRemoveMember)


    def setup_defaults(self,resource, owner, creator) :
        self.save_defaults(resource,owner,creator)

        options = self.make_slider_options(resource,owner,creator)
        interfaces = self.get_interfaces()

        slide = interfaces['Viewer'].make_slider_for(resource,options,owner,0,creator,creator)
        slide = interfaces['Editor'].make_slider_for(resource,options,owner,2,creator,creator)

        slide = interfaces['Apply'].make_slider_for(resource,options,owner,2,creator,creator)
        slide = interfaces['Join'].make_slider_for(resource,options,owner,2,creator,creator)

        slide = interfaces['InviteMember'].make_slider_for(resource,options,owner,2,creator,creator)
        slide = interfaces['AcceptMember'].make_slider_for(resource,options,owner,2,creator,creator)
 
        slide = interfaces['AddMember'].make_slider_for(resource,options,owner,2,creator,creator)
        slide = interfaces['RemoveMember'].make_slider_for(resource,options,owner,2,creator,creator)



    def main_json_slider_group(self,resource) :
        json = self.json_slider_group('Group Permissions', 'Use these sliders to set overall permissions on your group', resource, ['Viewer','Editor'], [0,0], [[0,1]])
        return json


get_permission_system().add_permission_manager(TgGroup, TgGroupPermissionManager(TgGroup))

# ========= Signal handlers


def setup_default_permissions(sender,**kwargs):
    # This signalled by Profile.save()
    # tests if there are already permissions for the profile and if not, creates defaults
    group = kwargs['instance']
    signal = kwargs['signal']
    
    ps = get_permission_system()
    print "DDD setup_default_permission for TgGroup"
    try :
        ps.get_permission_manager(TgGroup)
    except :
        ps.add_permission_manager(TgGroup, TgGroupPermissionManager(TgGroup))
        
    if not get_permission_system().has_permissions(group) :
        ps.get_permission_manager(TgGroup).setup_defaults(group, group, group)

post_save.connect(setup_default_permissions,sender=TgGroup)


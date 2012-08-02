#from django.contrib.auth.backends import RemoteUserBackend
#from Shibboleth_CERN.models import DummyUser
#
#import logging
#logger = logging.getLogger()
#
#class ShibbolethBackend(RemoteUserBackend):
#
#    create_unknown_user = True
#
#    def authenticate(self, **kwargs):
#        print "FIRST Call to shibloeth backend"
#        logging.info("pirmas")
#   #     rez = super(ShibbolethBackend, self).authenticate(**kwargs)
##        print rez
##        print rez.__class__
##        print dir(rez)
#        print "SECOND Call to shibloeth backend"
#
#        if kwargs.get('remote_user', False):
#            rez = DummyUser()
#            rez.username = kwargs['remote_user']
#             #User(username=kwargs['remote_user']).save(commit=False)
#
#            rez.is_authenticated = True
#            rez.is_anonymous = False
#            rez.is_active=True
#
#
#            if 'global-tag-administrators' in kwargs.get('groups', "").split(';'):
#                rez.is_superuser= True
#                rez.is_staff= True
#      #  return  None
#            return rez
#
#
##    def get_user(self, user_id):
##        pass
##        print "userid", user_id
###
#
#    def configure_user(self, user):
#        print "99999999999999999999999999999999"
#        print user
#        user.is_superuser = True
#        return user
##    def get_user(self, user_id):
##        super(ShibbolethBackend, self).get_user(user_id)
##
##
##    def clean_username(self, username):
##        return super(ShibbolethBackend, self).clean_username(username)
##
##
##    def __init__(self):
##        super(ShibbolethBackend, self).__init__()
##
##    def authenticate(self, remote_user):
##        super(ShibbolethBackend, self).authenticate(remote_user)
##
##    def get_all_permissions(self, user_obj):
##        return super(ShibbolethBackend, self).get_all_permissions(user_obj)
##
##    def get_group_permissions(self, user_obj):
##        return super(ShibbolethBackend, self).get_group_permissions(user_obj)
##
##    def has_module_perms(self, user_obj, app_label):
##        return super(ShibbolethBackend, self).has_module_perms(user_obj, app_label)
##
##    def configure_user(self, user):
##        return super(ShibbolethBackend, self).configure_user(user)
##
##    def has_perm(self, user_obj, perm):
##        return super(ShibbolethBackend, self).has_perm(user_obj, perm)

#=======================================================================================================================
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.models import User
from Shibboleth_CERN.primitive_soap import is_user_in_admin_group

class ShibbolethRemoteUserBackend(RemoteUserBackend):

    """
    This backend is to be used in conjunction with the ``RemoteUserMiddleware``
    found in the middleware module of this package, and is used when the server
    is handling authentication outside of Django.

    By default, the ``authenticate`` method creates ``User`` objects for
    usernames that don't already exist in the database.  Subclasses can disable
    this behavior by setting the ``create_unknown_user`` attribute to
    ``False``.
    """

    supports_anonymous_user = False
    create_unknown_user = True


    def authenticate(self, remote_user):
        """
        The username passed as ``remote_user`` is considered trusted.  This
        method simply returns the ``User`` object with the given username,
        creating a new ``User`` object if ``create_unknown_user`` is ``True``.

        Returns None if ``create_unknown_user`` is ``False`` and a ``User``
        object with the given username is not found in the database.
        """
        import logging
        logging.info("Shibboleth authentication")

        if not remote_user:
            return
        user = None
        username = self.clean_username(remote_user)


        # Note that this could be accomplished in one try-except clause, but
        # instead we use get_or_create when creating unknown users since it has
        # built-in safeguards for multiple threads.
        if self.create_unknown_user:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user = self.configure_user(user)
        else:
            try:
                user = User.objects.get(username=username)
                #user = self.configure_user(user) #AFTER EACH LOGIN CONFIIGURE #TODO EXCEPTION HANDLING                                                #SOMEDAY permissioN UPDATE REQUIRES LOGOUT AND LOGIN
            except User.DoesNotExist:
                pass
        return user

    def configure_user(self, user):
        """
        Configures a user after creation and returns the updated user.

        By default, returns the user unmodified.
        """
        import logging
        logging.info("Shibboleth user configuration")
        
        user.is_superuser = is_user_in_admin_group(user.username)
        user.is_staff= user.is_superuser
        user.save()

        return user



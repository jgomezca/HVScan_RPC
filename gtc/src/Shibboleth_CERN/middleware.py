from django.contrib.auth.middleware import RemoteUserMiddleware, LazyUser
from django.core.exceptions import ImproperlyConfigured
from Shibboleth_CERN.primitive_soap import is_user_in_admin_group
from django.contrib import auth

class ShibbloethHeaderMiddleware(RemoteUserMiddleware):
    def process_request(self, request):

        # AuthenticationMiddleware is required so that request.user exists.
        if not hasattr(request, 'user'):
            request.__class__.user = LazyUser()
        if not hasattr(request, 'user'):
       #     raise  Exception(str(request))
            raise ImproperlyConfigured(
                "The Django remote user auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE_CLASSES setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the RemoteUserMiddleware class.")
        print "hi"
        try:
            #print request.META
            username = request.META[self.header]
        except KeyError:
            print "we dont have meta"
            # If specified header doesn't exist then return (leaving
            # request.user set to AnonymousUser by the
            # AuthenticationMiddleware).
            return
        print username
        print "username exists in meta"
        # If the user is already authenticated and that user is the user we are
        # getting passed in the headers, then the correct user is already
        # persisted in the session and we don't need to continue.
        if request.user.is_authenticated():
            print "is authenticated" 
            if request.user.username == self.clean_username(username, request):
                return
        # We are seeing this user for the first time in this session, attempt
        # to authenticate the user.
        print "before auth"
        user = auth.authenticate(remote_user=username)
        print "after auth"
        print user 
        self.configure_user(user) #INSERTED
        if user:
            # User is valid.  Set request.user and persist user in the session
            # by logging the user in.
            request.user = user
            auth.login(request, user)

    def configure_user(self, user):
        #SOMEDAY fix monkeypach. better user configuration

        import logging
        logging.info("Shibboleth user configuration")
        if user is None:
            return

        user.is_superuser = is_user_in_admin_group(user.username)
        user.is_staff= user.is_superuser
        user.save()

        return user
#        backend_str = request.session[auth.BACKEND_SESSION_KEY]
#        backend = auth.load_backend(backend_str)
#        user = backend.configure_user(user)
#        return user
#        try:
#            username = backend.clean_username(username)
#        except AttributeError: # Backend has no clean_username method.
#            pass
#        return username


    header = 'REMOTE_USER'

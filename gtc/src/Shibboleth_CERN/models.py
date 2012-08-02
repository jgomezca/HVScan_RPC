#from django.contrib.auth.models import User

class DummyUser(object):
    id = 999
    is_authenticated = False
    is_anonymous = True
    is_active=False
    is_superuser= False
    is_staff= False
    username = ""
    def save(self, *args, **kwargs):
        pass

    def __str__(self):
        return self.username

    def has_module_perms(self, *args, **kwargs):
        print "has_module_perms"
        print args
        print kwargs
        return self.is_superuser

    def has_perm(self, *args, **kwargs):
        print "has_perm"
        print args
        print kwargs
        return self.is_superuser
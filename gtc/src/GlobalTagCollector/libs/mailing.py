from django.core.mail import EmailMultiAlternatives
import threading
from django.conf import settings
from Shibboleth_CERN.primitive_soap import list_administrator_emails

class EmailThread(threading.Thread):
    def __init__(self, subject, body, from_email, recipient_list, fail_silently, html):
        self.subject = subject
        self.body = body
        self.recipient_list = recipient_list
        self.from_email = from_email
        self.fail_silently = fail_silently
        self.html = html
        threading.Thread.__init__(self)

    def run (self):
        msg = EmailMultiAlternatives(self.subject, self.body, self.from_email, self.recipient_list)
        if self.html:
            msg.attach_alternative(self.html, "text/html")
            print msg.fail_silently
        msg.send(self.fail_silently)

#removed from email
def send_mail(subject, body, recipient_list, fail_silently=False, html=None, *args, **kwargs):
    from_email = settings.DEFAULT_FROM_EMAIL
    email_thread = EmailThread(subject, body, from_email, recipient_list, fail_silently, html)
    email_thread.start()
    return email_thread

def mail_admins(subject, body, fail_silently=False, html=None, *args, **kwargs):
    admin_list = list_administrator_emails()
    return send_mail(subject, body, admin_list, fail_silently, html, *args, **kwargs)

def send_mail_user(subject, body, user, fail_silently=False, html=None, *args, **kwargs):
    from_email = settings.DEFAULT_FROM_EMAIL
    user_email = user.username #TODO get email for username (Nice/email)
    return EmailThread(subject, body, from_email, [user_email], fail_silently, html).start()


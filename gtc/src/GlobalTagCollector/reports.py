from django.template import Context, Template
from GlobalTagCollector.libs.mailing import send_mail
from GlobalTagCollector.models import GlobalTag
from Shibboleth_CERN.primitive_soap import list_administrator_emails
import socket
try:
    HOSTNAME = socket.gethostname()
except:
    HOSTNAME = 'unknown'

#NOTE NO report if no data
#-----------------------------------------------------------------------------------------------------------------------
def report_yesterday_global_tags():

    mail_template = Template(
        '''
Automatic report from Global Tag Collector

Yesterday imported global tags:
{% for gt in yesterday_gts %}
  {{ gt.name }} - {{ gt.external_finding_timestamp }}
{% endfor %}
'''
    )
    yesterday_gts = GlobalTag.imported.today()
    if len(yesterday_gts) == 0:
        return
    c = Context({'yesterday_gts':yesterday_gts})
    message_text = mail_template.render(c)
    recipients = list_administrator_emails()
    return send_mail("GT import report", message_text, recipients, fail_silently=True)
#-----------------------------------------------------------------------------------------------------------------------

def report_last_7_days_global_tags():
    mail_template = Template(
        '''
Automatic report from Global Tag Collector

Global tags imported during last 7 days:
{% for gt in week_gts %}
  {{ gt.name }} - {{ gt.external_finding_timestamp }}
{% endfor %}
'''
    )
    week_gts = GlobalTag.imported.last_7_days()
    print week_gts
    if len(week_gts) == 0:
        return
    c = Context({'week_gts':week_gts})
    message_text = mail_template.render(c)
    recipients = list_administrator_emails()
    return send_mail("GT import report", message_text, recipients, fail_silently=True)
#-----------------------------------------------------------------------------------------------------------------------

def report_record_queued(queue_entry):
    mail_template = Template(
        '''
        Automatic report from Global Tag Collector
        Sender: {{ hostname }}

        New record added to the queue. Details:
        Queue: {{ queue_entry.queue.name }}
        Account type: {{ queue_entry.tag.account.account_type.title}}
        Account: {{ queue_entry.tag.account.name }}
        Tag: {{ queue_entry.tag.name }}
        Record: {{ queue_entry.record.name }}
        Label: {{ queue_entry.label }}
        Comment: {{ queue_entry.comment }}
        Status: {{ queue_entry.get_status_display }}
        Submitter: {{ queue_entry.submitter}}
        Submitting time: {{ queue_entry.submitting_time }}


        '''
    )

    admin_mail_template = Template(
        '''
        Automatic report from Global Tag Collector
        Sender: {{ hostname }}

        New record added to the queue. Details:
        Queue: {{ queue_entry.queue.name }}
        Account type: {{ queue_entry.tag.account.account_type.title}}
        Account: {{ queue_entry.tag.account.name }}
        Tag: {{ queue_entry.tag.name }}
        Record: {{ queue_entry.record.name }}
        Label: {{ queue_entry.label }}
        Comment: {{ queue_entry.comment }}
        Status: {{ queue_entry.get_status_display }}
        Submitter: {{ queue_entry.submitter}}
        Submitting time: {{ queue_entry.submitting_time }}

        https://{{hostname}}.cern.ch/admin/GlobalTagCollector/gtqueueentry/{{queue_entry.id}}/

        '''
    )

    c = Context({'queue_entry':queue_entry, 'hostname':HOSTNAME})
    message_text = mail_template.render(c)
    admin_message_text = admin_mail_template.render(c)
    administrators = set(list_administrator_emails())
    title = "GT record queued"
    send_mail(title, admin_message_text, administrators, fail_silently=True)

    if queue_entry.submitter.email in administrators:
        pass
    else:
        send_mail(title, message_text, [queue_entry.submitter.email], fail_silently=True)



#-----------------------------------------------------------------------------------------------------------------------

def report_record_status_changed(queue_entry, old_status):
    mail_template = Template(
        '''
        Automatic report from Global Tag Collector
        Sender: {{ hostname }}

        Record status changed. Details:
        Queue: {{ queue_entry.queue.name }}
        Account type: {{ queue_entry.tag.account.account_type.title}}
        Account: {{ queue_entry.tag.account.name }}
        Tag: {{ queue_entry.tag.name }}
        Record: {{ queue_entry.record.name }}
        Label: {{ queue_entry.label }}
        Comment: {{ queue_entry.comment }}
        From Status {{ old_status }}
        To Status: {{ queue_entry.get_status_display }}
        Submitter: {{ queue_entry.submitter}}
        Submitting time: {{ queue_entry.submitting_time }}
        Administrator: {{ queue_entry.administrator }}
        Administration Time: {{ queue_entry.administration_time }}
        '''
    )
    admin_mail_template = Template(
        '''
        Automatic report from Global Tag Collector
        Sender: {{ hostname }}

        Record status changed. Details:
        Queue: {{ queue_entry.queue.name }}
        Account type: {{ queue_entry.tag.account.account_type.title}}
        Account: {{ queue_entry.tag.account.name }}
        Tag: {{ queue_entry.tag.name }}
        Record: {{ queue_entry.record.name }}
        Label: {{ queue_entry.label }}
        Comment: {{ queue_entry.comment }}
        From Status {{ old_status }}
        To Status: {{ queue_entry.get_status_display }}
        Submitter: {{ queue_entry.submitter}}
        Submitting time: {{ queue_entry.submitting_time }}
        Administrator: {{ queue_entry.administrator }}
        Administration Time: {{ queue_entry.administration_time }}

        https://{{hostname}}.cern.ch/admin/GlobalTagCollector/gtqueueentry/{{queue_entry.id}}/
        '''
    )
    c = Context({'queue_entry':queue_entry, 'old_status': old_status, 'hostname':HOSTNAME})
    message_text = mail_template.render(c)
    admin_message_text = admin_mail_template.render(c)
    administrators = set(list_administrator_emails())
    title = "GT status changes"
    send_mail(title, admin_message_text, administrators, fail_silently=True)

    if queue_entry.submitter.email in administrators:
        pass
    else:
        send_mail(title, message_text, [queue_entry.submitter.email], fail_silently=True)


#def records_modificated_yesterday():
#    pass



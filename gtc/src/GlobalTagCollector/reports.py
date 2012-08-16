from django.core.mail.message import EmailMultiAlternatives
from django.template import Context, Template
from django.conf import settings
from django.template import Context, Template
from GlobalTagCollector.models import GlobalTag
from django.core.urlresolvers import reverse
import logging
logger = logging.getLogger(__file__)

import socket

def send_mail(subject, body, recipient_list, html=None):
    from_email = settings.EMAIL_HOST_USER
    msg = EmailMultiAlternatives(subject, body, from_email, recipient_list)
    if html:
        msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=False)


def report_queue_created(queue_obj):
    mail_template = Template("""

Automatic report from Global Tag Collector
--
Hostname:{{hostname}}
Production Level: {{production_level}}
--
Global Tag Queue created.
Queue Name: {{queue_obj.name}}
Description: {{queue_obj.description}}
Is open?: {{queue_obj.is_open}}
Last gt: {{queue_obj.last_gt}}
Expected gt name: {{queue_obj.expected_gt_name}}
GT account: {{queue_obj.gt_account}}
GT type category: {{queue_obj.gt_type_category}}
Releases (from-to): {{queue_obj.release_from}} - {{queue_obj.to}}

{{url}}
"""
    )
    recipients = ["global-tag-administrators@cern.ch"]
    c = Context({
        'hostname':settings.HOSTNAME,
        'queue_obj':queue_obj,
        'production_level': settings.PRODUCTION_LEVEL,
        'url': 'https://' + settings.HOSTNAME + reverse("gt_queue_entries",kwargs={'queue_id':queue_obj.pk})
    })
    message_text = mail_template.render(c)

    try:
        send_mail(subject="Created queue:" + queue_obj.name, body=message_text,recipient_list=recipients)
    except Exception as e:
        logger.error("Message could not be sent")
        logger.error(e)


def report_queue_entry_submitted(queue_entries):
    mail_template = Template("""

Automatic report from Global Tag Collector
--
Hostname:{{hostname}}
Production Level: {{production_level}}
{% for queue_entry in queue_entries %}
--
Global Tag Queue entry submitted.
Queue:{{queue_entry.queue}}
Tag:{{queue_entry.tag}}
Record:{{queue_entry.record}}
Label:{{queue_entry.label}}
Comment:{{queue_entry.comment}}
Status:{{queue_entry.status}}
Submitter:{{queue_entry.submitter}}
Submitting time:{{queue_entry.submitting_time}}
https://{{hostname}}/{% url gt_queue_entries queue_id=queue_entry.queue.pk %}
{% endfor %}
"""
    )
    recipients = ["global-tag-administrators@cern.ch", queue_entries[0].submitter.email]
    c = Context({
        'hostname':settings.HOSTNAME,
        'queue_entries':queue_entries,
        'production_level': settings.PRODUCTION_LEVEL,
    })
    message_text = mail_template.render(c)
    recipients =["global-tag-administrators@cern.ch", queue_entries[0].submitter.email]
    try:
        print message_text
        send_mail(
            subject="Queue entry submitted",body=message_text,recipient_list=recipients)
    except Exception as e:
        logger.error("Message could not be sent")
        logger.error(e)




def report_queue_entry_status_changed(queue_entry_obj, affected_records, old_status, old_status_display):
    mail_template = Template("""

Automatic report from Global Tag Collector
--
Hostname:{{hostname}}
Production Level: {{production_level}}
--
Global Tag Queue entry changed by administrator.
Queue:{{queue_entry.queue}}
Tag:{{queue_entry.tag}}
Record:{{queue_entry.record}}
Label:{{queue_entry.label}}
Comment:{{queue_entry.comment}}
Status:{{queue_entry.get_status_display}}
Old status:{{old_status_display}}
Submitter:{{queue_entry.submitter}}
Submitting time:{{queue_entry.submitting_time}}
Administrator:{{queue_entry.administrator}}

{{url}}

Other affected records (if any):
{% for affected_record in affected_records %}

Tag:{{affected_record.tag}}
Record:{{affected_record.record}}
Label:{{affected_record.label}}
{% endfor %}
"""
    )
    recipients = ["global-tag-administrators@cern.ch", queue_entry_obj.submitter.email]
    c = Context({
        'hostname':settings.HOSTNAME,
        'queue_entry':queue_entry_obj,
        'production_level': settings.PRODUCTION_LEVEL,
        'old_status_display':old_status_display,
        'affected_records':affected_records,
        'url': 'https://' + settings.HOSTNAME + reverse("gt_queue_entries",kwargs={'queue_id':queue_entry_obj.queue.pk})
    })
    message_text = mail_template.render(c)

    try:
        send_mail(
            subject="Queue entry submitted to the queue:" + queue_entry_obj.queue.name, body=message_text,recipient_list=recipients)
    except Exception as e:
        logger.error("Message could not be sent")
        logger.error(e)

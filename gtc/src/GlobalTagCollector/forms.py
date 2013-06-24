from django.forms.formsets import BaseFormSet, formset_factory
from django import forms
from django.forms import ModelForm
from GlobalTagCollector import models
from GlobalTagCollector.models import Account, AccountType, Record, HardwareArchitecture

class AccountModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(AccountModelForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = "Account Name:"
        self.fields['name'].help_text = ""
        self.fields['entry_comment'].label = "Comment:"
        self.fields['entry_comment'].help_text = ""

    class Meta:
        model = Account
        fields = ['id', 'name', 'entry_comment', 'account_type']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        return name


class HardwareArchitectureModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(HardwareArchitectureModelForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = "HWA Name:"
        self.fields['name'].help_text = ""
        self.fields['entry_comment'].label = "Comment:"
        self.fields['entry_comment'].help_text = ""
        self.fields['name'].required = True

    class Meta:
        model = HardwareArchitecture
        fields = ['id', 'name', 'entry_comment']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        return name


class QueueTagEntryForm(ModelForm):
    #todo prohibid ID fields
    class Meta:
        model = models.GTQueueEntry
        exclude = ('queue', 'status', 'administrator', 'submitter')

    class Media:
        js =  ('js/jquery-1.6.2.min.js',)
        pass
       



    def __init__(self, *args, **kwargs):
        super(QueueTagEntryForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['account_type', 'account',  'tag', 'record', 'label', 'comment',  'queue_choices']
  #      self.fields["tag"].queryset = models.Tag.objects.none()
  #      self.fields["record"].queryset = models.Record.objects.none()

    #def __init__(self):
    #    super(ModelForm, self).__init__(*args, **kw)
   #     self.fields.keyOrder = ['auto_id','tag', 'record', 'label', 'comment', 'account_type', 'account', 'queue_choices']

    account_type = forms.ModelChoiceField(queryset=AccountType.objects.filter(visible_for_users=True))
    account = forms.ModelChoiceField(queryset=Account.objects.all())
    queue_choices = forms.ModelMultipleChoiceField(queryset=models.GTQueue.objects.filter(is_open=True).order_by('name'))#,widget=forms.CheckboxSelectMultiple)

    def clean(self):
        super(QueueTagEntryForm, self).clean()
        cleaned_data = self.cleaned_data

        account_type = cleaned_data.get('account_type', None)
        account = cleaned_data.get('account', None)
        tag = cleaned_data.get('tag', None)
        record = cleaned_data.get('record', None)

        if (account_type is not None) and (account is not None) and (account.account_type != account_type):
            self._errors['account'] = self.error_class(["Account must belong to account selected type"])
            del cleaned_data['account']

        if (account is not None) and (tag is not None) and (tag.account != account):
            self._errors['tag'] = self.error_class(["Tag must belong to account"])
            del cleaned_data['tag']

        if (tag is not None) and (record is not None) and (tag.object_r != record.object_r):
            self._errors['record'] = self.error_class(["Record mus belong to the tag"])
            del cleaned_data['record']

        return cleaned_data

class BaseQueueTagEntryFormSet(BaseFormSet): #ASK it is enought to check tags? how about labels? # label + record = unique

    def clean(self):
        """Checks that no two same tags(in same account)"""
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return
        tags = []
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            if form.cleaned_data == {}:
                continue
            tag = form.cleaned_data['tag']
            if tag.pk in tags:
                #WRONG: raise forms.ValidationError("Your submits are conflicting. Please check form #%d."% (i+1))
                #BETTER:
                self._non_form_errors = self.error_class(["Your submits are conflicting. Please check form #%d."% (i+1)])
            tags.append(tag.pk)

    def save(self, submitter): #Note this is not ovveriding
                                #todo return results
        if self.is_valid():
            instances = []
            for form in self:
                if len(form.cleaned_data.keys())>0 :
                    print form.cleaned_data['queue_choices']
                    for queue_choice in form.cleaned_data['queue_choices']:
                        submit = None
                        del submit
                        submit = form.save(commit=False, )
                        submit.pk = None # because force insert don't want to work
                        submit.queue = queue_choice
                        submit.submitter = submitter
                        if submitter.is_superuser:
                            submit.administrator = submitter #ask maby is staff also would work
                        else:
                            submit.administrator = None
                        submit.administration_time = None
                        r = submit.save(force_insert=True)
                        #FIX sor some reason sumit becomes same object, when appending. in next line workaround to get list of submits
                        instances.append(models.GTQueueEntry.objects.get(pk=submit.pk)) #actual object, not id
            return instances




#TODO update default extra
QueueTagEntryFormSet = formset_factory(QueueTagEntryForm,
                                       formset=BaseQueueTagEntryFormSet)

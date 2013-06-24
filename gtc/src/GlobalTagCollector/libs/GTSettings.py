from GlobalTagCollector.models import Account, GlobalTag, HardwareArchitecture
from GlobalTagCollector.forms import AccountModelForm, HardwareArchitectureModelForm

class HardwareArchitectureSettings(object):
    def __init__(self):
        self.hwa_objects_all = HardwareArchitecture.objects.all()
        self.form = HardwareArchitectureModelForm()
        self.form_submitted = False

    def init_form(self):
        return {'hwa_form': self.form, 'hwa_objects_all': self.hwa_objects_all}

    def insert_hwa(self, post_data):
        self.form = HardwareArchitectureModelForm(post_data)
        if self.form.is_valid():
            self.form.instance.entry_manual_added = True
            self.form.save()
            return True
        return False

    def delete_hwa(self, get_data):
        self.obj = HardwareArchitecture.objects.filter(pk=get_data)
        self.obj.delete()


class GlobalTagSettings(object):
    def __init__(self):
        self.gtc_objects_all = GlobalTag.objects.all()
        self.form_submitted = False

    def init_form(self):
        return {'gtc_objects_all': self.gtc_objects_all}

    def update_gtc(self, gt_id, choice):
        gt_obj = GlobalTag.objects.get(pk=gt_id)
        gt_obj.entry_ignored = True if choice == 1 else False
        gt_obj.save()
        return True


class AccountSettings(object):
    def __init__(self):
        self.acc_objects_all = Account.objects.filter(entry_manual_added=True)
        self.form = AccountModelForm()
        self.form_submitted = False

    def init_form(self):
        return {'acc_form': self.form, 'acc_objects_all': self.acc_objects_all}

    def insert_acc(self, post_data):
        self.form = AccountModelForm(post_data)
        if self.form.is_valid():
            self.form.instance.entry_manual_added = True
            self.form.save()
            return True
        return False

    def delete_acc(self, get_data):
        self.obj = Account.objects.filter(pk=get_data)
        self.obj.delete()
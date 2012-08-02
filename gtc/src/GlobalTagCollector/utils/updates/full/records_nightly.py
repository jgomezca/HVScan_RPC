import os
import subprocess
import re
from GlobalTagCollector.models import Record, ObjectForRecords, HardwareArchitecture, SoftwareRelease
import datetime
from django.db.transaction import commit_on_success

class NigtlyReleasesInfromation(object):
    """

    """

    def __init__(self, name, hardware_architecture, path):
        self.nightly_release_name = name
        self.path = path
        self.hardware_architecture_name = hardware_architecture
        m = re.search("CMSSW_(?P<major_release>\d+)_(?P<minor_release>\d+)_X_(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})-(?P<hour>\d{2})(?P<minute>\d{2})", self.nightly_release_name)
        self.__dict__.update( m.groupdict())
        self.datetime = datetime.datetime(int(self.year), int(self.month), int(self.day), int(self.hour), int(self.minute))
        self.release_cycle = int(self.major_release)*100 + int(self.minor_release)

    def __str__(self):
        return str(self.nightly_release_name) + " "+ str(self.hardware_architecture_name) +" "+ str(self.path)


class NewestSoftwareReleasesByCycle(object):
    releases = {}

    def add_nightly_release_information(self, new_nri):
        """

        """
        if self.releases.has_key((new_nri.hardware_architecture_name,new_nri.release_cycle)):
            if self.releases[(new_nri.hardware_architecture_name,new_nri.release_cycle)].datetime < new_nri.datetime:
                self.releases[(new_nri.hardware_architecture_name,new_nri.release_cycle)] = new_nri
        else:
            self.releases[(new_nri.hardware_architecture_name,new_nri.release_cycle)] = new_nri
    

class RecordsNightlyMigration(object):
    """

    """

    def get_nightly_software_releases_list(self):
      #  return
        """

        """
        newest_cycles = NewestSoftwareReleasesByCycle()
        dirname = os.path.dirname(__file__)
        for hardware_architecture in HardwareArchitecture.objects.all():
            cmd_args = [dirname + "/nightly_software_releases_list.sh", hardware_architecture.name]
            (stdout, stderr) = subprocess.Popen(cmd_args, stdout=subprocess.PIPE).communicate()
            for line in stdout.splitlines():
                try:
                    #print line
                    release_name, hardware_arch, path = line.split(" ")
                    
                except Exception as e:
                    print line
                    print cmd_args
                    raise e
                try:
                    nri = NigtlyReleasesInfromation(release_name,hardware_arch, path)
                    newest_cycles.add_nightly_release_information(nri)
                except Exception as e:
                    pass
        return list(newest_cycles.releases.values())



    def __init__(self):
        nri_list = self.get_nightly_software_releases_list()
        dirname = os.path.dirname(__file__)
        for nri in nri_list:
            CMSSW_name = "CMSSW_" + str(nri.major_release) + "_" + str(nri.minor_release) + "_X"
            RELESE_NUMBER =int(nri.major_release) * 100000000  + int(nri.minor_release) * 1000000 + 0 * 1000 + 998 #998 - special number
            sr, created = SoftwareRelease.objects.get_or_create(name=CMSSW_name, internal_version=RELESE_NUMBER)

            sr_arch_names = [arch.name for arch in sr.hardware_architecture.all()]
            if created or (nri.hardware_architecture_name not in sr_arch_names):
                ha = HardwareArchitecture.objects.get(name=nri.hardware_architecture_name)
                sr.hardware_architecture.add(ha)
                sr.save()


    #hardware_architecture = models.ManyToManyField(HardwareArchitecture)


            cmd_args = [dirname + "/get_records_nightly.sh", nri.hardware_architecture_name, nri.path]
            (stdout, stderr) = subprocess.Popen(cmd_args, stdout=subprocess.PIPE).communicate()
            stdout = str(stdout)
            for line in stdout.splitlines():
             #   print line
                record_name, object_name = line.split(", ",1)
                try:
                    with commit_on_success():
                        o4r, obj_created = ObjectForRecords.objects.get_or_create(name=object_name)
                        r, r_created = Record.objects.get_or_create(object_r=o4r, name=record_name)
                        if r_created:
                            r.software_release.add(sr)
                            r.save()
                except Exception as e:
                    print e

#nri = NigtlyReleasesInfromation("CMSSW_4_2_X_2011-07-09-0100", "sat/4.2-sat-01/CMSSW_4_2_X_2011-07-09-0100/lib/slc5_amd64_gcc434")

#
#print HardwareArchitecture.objects.all()
#print "pre"
#RecordsNightlyMigration()

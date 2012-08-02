from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from GlobalTagCollector import models
import json
from GlobalTagCollector.libs.GTQueueManagement import GTQueueManager
from GlobalTagCollector.libs.data_update_managers import GlobalTagsUpdate
from GlobalTagCollector.models import GlobalTag, GTQueue, GTTypeCategory, GTAccount, SoftwareRelease, Tag, Record

import pprint

class Command(BaseCommand):

    def data_to_information(self, data):
        data_lines = data.split("\n")
        #pprint.pprint(data_lines)

        data_entries = []
        for data_line in data_lines:
            data_line = data_line.strip()
            if not len(data_line): continue
            data_line = data_line.rsplit(" |",1)[0]
#            print data_line
            splitted_line =  data_line.split("| ")
#            print splitted_line
#            print len(splitted_line)
            entry_dict = {
                "tag_name" : splitted_line[1].strip().lstrip("!"),
                "record_name" : splitted_line[2].strip().lstrip("!"),
                "label" : splitted_line[3].strip().lstrip("!"),
                "db_acc": splitted_line[4].strip().lstrip("!"),
                "description": splitted_line[5].strip().lstrip("!"),
            }
            try:
                entry_dict["gt_name"]= splitted_line[7].strip().lstrip("!")
            except Exception:
                entry_dict["gt_name"] = None
            data_entries.append(entry_dict)
        #pprint.pprint(data_entries)
        return data_entries


    def handle(self, *args, **options):
        #---++ START52
        #---++++!! Approved
        # #%TABLE{ tableborder="0" cellpadding="4" cellspacing="3" cellborder="1" headerbg="#D5CCB1"  headercolor="#666666" databg="#FAF0D4, #F3DFA8" headerrows="1" dataalign="left"}%
#%EDITTABLE{ format="| text, -1 | text, -1 | text, -1 | text, -1 | text, -1 | label, 0, %SERVERTIME{"$day/$mon/$year"}% | text, -1 | "changerows="on"}%
#| *Tag name* | *Record name* | *Label* | *Database account* | *Brief description* | *posted* | *GT* |
        start_52_data_text ="""
| !AlCaRecoHLTpaths5e32_v16_mc | !AlCaRecoTriggerBitsRcd | | CMS_COND_31X_HLT | It contains latest changes in 5E33 2012 HLT Menu /dev/CMSSW_5_2_0/HLT/V30: AlCa_EcalEta_v* -> AlCa_EcalEta*, AlCa_EcalPi0_v* -> AlCa_EcalPi0*. Removed non existing CSC bits | 15/Mar/2012 | |
| !DTt0_STARTUP_V02_mc | !DTT0Rcd | | CMS_COND_DT_000 | Migration to new account | 19/Mar/2012 | |
| !DTTtrig_V01_cosmics_mc | !DTTtrigRcd | cosmics | CMS_COND_31X_DT | New cosmics DTTtrig MC tag | 23/Mar/2012 | |
| !CSCBadChambers_March2012_v1_mc | !CSCBadChambersRcd | | CMS_COND_31X_CSC | new tag for CSC Bad Chambers for inclusion in the GT for the 5_2_X ReDigi/ReReco of MC: -- Chamber status changes --  ME-1/1/02 [Now Bad]  ME-1/1/22 [Now Bad]  ME-1/1/32 [Now Bad]  ME+1/1/06 [Now Bad]  ME+1/1/03 [Now Good]  ME+1/1/24 [Now Good] | 27/Mar/2012 | |
| !HcalChannelQuality_v1.40_mc | !HcalChannelQualityRcd | | !CMS_COND_31X_HCAL | Updated channel status, HO ring2 is now on | 29/Mar/2012 | START52_V7 |
| !L1EmEtScale_EEG_EHSUMS_TAU4_FGHOE_CALIBV4_15MAR12_mc | !L1EmEtScaleRcd | | CMS_COND_31X_L1T | New !RCT configuration for 2012 running. | 27/Mar/2012 | START52_V8 |
| !L1RCTParameters_EEG_EHSUMS_TAU4_FGHOE_CALIBV4_15MAR12_mc | !L1RCTParametersRcd | | CMS_COND_31X_L1T | New !RCT configuration for 2012 running. | 27/Mar/2012 | START52_V8 |
| !L1CaloHcalScale_EEG_EHSUMS_TAU4_FGHOE_CALIBV4_15MAR12_mc | !L1CaloHcalScaleRcd | | CMS_COND_31X_L1T | New !RCT configuration for 2012 running. | 27/Mar/2012 | START52_V8 |
| !L1CaloEcalScale_EEG_EHSUMS_TAU4_FGHOE_CALIBV4_15MAR12_mc | !L1CaloEcalScaleRcd | | CMS_COND_31X_L1T | New !RCT configuration for 2012 running. | 27/Mar/2012 | START52_V8 |
| !L1MuCSCTFConfiguration_10412_mc | !L1MuCSCTFConfigurationRcd | | CMS_COND_31X_L1T | New !CSCTF configuration for 2012 running | 01/Apr/2012 | START52_V8 |
| !L1MuCSCPtLut_key-10_mc | !L1MuCSCPtLutRcd | | CMS_COND_31X_L1T | New !CSCTF configuration for 2012 running | 02/Apr/2012 | START52_V8 |
| !L1MuGMTParameters_gmt2012_0_EarlyRPC_mc | !L1MuGMTParametersRcd | | CMS_COND_31X_L1T | New !GMT configuration for 2012 running | 02/Apr/2012 | START52_V8 |
| !SiStripBadComponents_realisticMC_for2012_v1_mc | !SiStripBadChannelRcd | | CMS_COND_31X_STRIP | Added 12 new masked modules in TIB and TOB | 02/Apr/2012 | START52_V9 |
| !L1CaloEcalScale_EEG_EHSUMS_TAU4_FGHOE_CALIBV1_02APR12_mc | !L1CaloEcalScaleRcd | | CMS_COND_31X_L1T | Corrected !RCT for ECAL transparency calibration in MC, not data | 02/Apr/2012 | START52_V9 |
| !L1CaloHcalScale_EEG_EHSUMS_TAU4_FGHOE_CALIBV1_02APR12_mc | !L1CaloHcalScaleRcd | | CMS_COND_31X_L1T | Corrected !RCT for ECAL transparency calibration in MC, not data | 02/Apr/2012 | START52_V9 |
| !L1EmEtScale_EEG_EHSUMS_TAU4_FGHOE_CALIBV1_02APR12_mc | !L1EmEtScaleRcd | | CMS_COND_31X_L1T | Corrected !RCT for ECAL transparency calibration in MC, not data | 02/Apr/2012 | START52_V9 |
| !L1RCTParameters_EEG_EHSUMS_TAU4_FGHOE_CALIBV1_02APR12_mc | !L1RCTParametersRcd | | CMS_COND_31X_L1T | Corrected !RCT for ECAL transparency calibration in MC, not data | 02/Apr/2012 | START52_V9 |
| Realistic8TeV2012Collisions_START52_V9_v1_mc | BeamSpotObjectsRcd | | CMS_COND_31X_BEAMSPOT | Updated 8TeV with the observed value of sigmaZ - for special MC productions only | 20/May/2012 | START52_V9A |
"""
        entries_52 = self.data_to_information(start_52_data_text)


        GTQueue.objects.filter(expected_gt_name='START52_V9A').delete()
        GlobalTag.objects.filter(name="START52_V9A").delete()

        gt_queue_obj = GTQueue(
            name="START52_V9A",
            description="Test description",
            is_open = True,
            last_gt = GlobalTag.objects.get(name="START52_V7"),

            gt_type_category = GTTypeCategory.objects.get(name="mc"),
            gt_account = GTAccount.objects.get(name="base global tag account"),
            release_from = SoftwareRelease.objects.all().order_by('internal_version')[0],
            release_to = None,
            expected_gt_name = 'START52_V9A'
        )
        print "queue created"
        gt_queue_obj.save()
        user, created = User.objects.get_or_create(username="DUMMY_TEST_USER2")
        print "dummy user created"
        queue_manager = GTQueueManager(gt_queue_obj)
        queue_manager.create_children(user)

        #--------

        print entries_52
        for data_entry in entries_52:
            #offline production
            tag = Tag.objects.get(name=data_entry["tag_name"], account__name=data_entry["db_acc"], account__account_type__title="Offline Production")
            record = Record.objects.get(name=data_entry["record_name"])
            queue_manager.add_queue_entry(tag_obj=tag, record_obj=record,label=data_entry["label"], comment=data_entry["description"], submitter=user, status="A")

        #--------

        GlobalTagsUpdate()._process_global_tag('START52_V9A')
        f = open("GT_TEST_GTC.conf","wb")
        f.write(queue_manager.queue_configuration())
        f.close()

    #except Exception as e:
        #print e



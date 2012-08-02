# coding=utf-8

class PatchTagContainers(object):

    def patch(self, account, tags_containers):
        if account.name == "CMS_COND_31X_FROM21X":
            for tag_container in tags_containers:
                 if "Rcd" in tag_container["container_name"]:
                     tag_container["container_name"] = tag_container["container_name"].strip("Rcd")
        return tags_containers


# -*- coding: utf-8 -*-
"""
Test
====
"""
import cherrypy
import datetime
import record_lib
import Settings
import ServerCache
from cherrypy import expose

import service
import api

#if @service - then doc and args
#/domain/recordsprovider/api/..


@api.generateServiceApi
class App(object):

    @cherrypy.expose
    def index(self):
        return self.apih()


    @cherrypy.expose
    def hardwarearchitecture_list(self, *args, **kwargs):
        """
        Returs list of currently active hardware architectures (Mac OS architectures are excluded).
        No arguments required.
        Response example:
        {
          "body": {
            "hardware_architectures": [
              "slc5_amd64_gcc434",
              "slc5_amd64_gcc451",
              "slc5_ia32_gcc434",
              "slc5_amd64_gcc462"
            ]
          },
          "header": {
            "date_updated": "2012-05-14T00:00:00"
          }
        }
        """
        ha = record_lib.hardware_architecture_provider()
        ha_updated = Settings.HARDWARE_ARCHITECTURES_UPDATED
        rez = {
            'header':{
                'date_updated': ha_updated.strftime('%Y-%m-%dT%H:%M:%S'),
            },
            'body':{
                'hardware_architectures': ha,
            }
        }
        return service.setResponseJSON(rez)


    def _flat_software_releases_list(self, software_releases_list):
        flat_software_releases_list = []
        for software_release in software_releases_list:
            software_release_dict = {
                'name': software_release.name,
                'hardware_architectures':list(software_release.hardware_releases()),
                'version':{
                    'tuple': software_release.version_tuple(),
                    'dict': software_release.version_dict(),
                    'is_prerelease':software_release.is_prerelease,
                    }
            }
            flat_software_releases_list.append(software_release_dict)
        return flat_software_releases_list


    @cherrypy.expose
    def softwarerelease_list(self, include_prereleases=True, from_major=None, till_major=None, *args, **kwargs):
        include_prereleases = bool(include_prereleases)
        if from_major is not None:
            from_major = int(from_major)
        if till_major is not None:
            till_major = int(till_major)
        srm = record_lib.SoftwareReleaseManager()
        software_releases_list = srm.list_software_releases(include_prereleases, from_major, till_major)
        flat_software_releases_list = self._flat_software_releases_list(software_releases_list)

        rez = {
            'header':{
                'filter_aruments':{
                    'include_prereleases':include_prereleases,
                    'from_major':from_major,
                    'till_major':till_major,
                },
            },
            'body':{
                'software_releases':flat_software_releases_list
            }

        }
        return service.setResponseJSON(rez)


    @cherrypy.expose
    def softwarerelease_dict(self,include_prereleases=True, from_major=None, till_major=None):
        include_prereleases = bool(include_prereleases)
        if from_major is not None:
            from_major = int(from_major)
        if till_major is not None:
            till_major = int(till_major)
        srm = record_lib.SoftwareReleaseManager()
        software_releases_by_architecture = srm.list_software_releases(include_prereleases, from_major, till_major,
            group_by_hardware_architecture=True)
        flat_software_releases_by_architecture = []
        for hardware_architecture_name, software_releases_list in software_releases_by_architecture.items():
            flat_software_releases_list = self._flat_software_releases_list(software_releases_list)
            flat_software_releases_by_architecture.append(
                {'hardware_architecture_name':hardware_architecture_name, 'software_releases':flat_software_releases_list}
            )


        rez = {
            'header':{
                'filter_aruments':{
                    'include_prereleases':include_prereleases,
                    'from_major':from_major,
                    'till_major':till_major,
                    },
                },
            'body':{
                'hardware_architectures':flat_software_releases_by_architecture,
            }

        }
        return service.setResponseJSON(rez)


    @cherrypy.expose
    def softwarerelease_majorversion_list(self):
        rez = {
            'header': {},
            'body':{
                'software_release_major_versions':record_lib.SoftwareReleaseManager().major_version_list()
            }
        }
        return service.setResponseJSON(rez)

    @cherrypy.expose()
    def record_container_map(self, hardware_architecture_name, software_release_name, *args, **kwargs):
        cache_key = hardware_architecture_name+"#record#container#map#"+software_release_name
        cache_rez = ServerCache.cache_get(cache_key, max_age=31536000)#max age ~1year
        if cache_rez is None:
            record_container_map = record_lib.ContainerRecordProvider().provide(hardware_architecture_name, software_release_name)
            record_container_list = [ {'record_name':record, 'container':container} for record, container in record_container_map.items() ]
            cached_at = datetime.datetime.now()
            for_cache = {'record_container_list':record_container_list,'cached_at':cached_at,
                         'hardware_architecture_name':hardware_architecture_name,
                         'software_release_name':software_release_name}
            ServerCache.cache_put(cache_key, for_cache)
        else:
            record_container_list = cache_rez['record_container_list']
            cached_at = cache_rez['cached_at']
            if cache_rez.get('hardware_architecture_name') != hardware_architecture_name or \
               cache_rez.get('software_release_name') != software_release_name:
                #we got hash collision. solving
                record_container_map = record_lib.ContainerRecordProvider().provide(hardware_architecture_name, software_release_name)
                record_container_list = [ {'record_name':record, 'container':container} for record, container in record_container_map.items() ]
                cached_at = datetime.datetime.now()
                for_cache = {'record_container_list':record_container_list,'cached_at':cached_at,
                         'hardware_architecture_name':hardware_architecture_name,
                         'software_release_name':software_release_name}
                ServerCache.cache_put(cache_key, for_cache)



        rez = {
            'header':{
                'cached_at': cached_at.strftime('%Y-%m-%dT%H:%M:%S'),
                'hardware_architecture_name':hardware_architecture_name,
                'software_release_name':software_release_name,
            },
            'body':{
                'record_container_map':record_container_list
            }
        }

        return service.setResponseJSON(rez)


def main():
	service.start(App())


if __name__ == '__main__':
	main()


import os
from GTServer import UploadGTServer

import GTServerSettings as Settings

import service


Settings.GLOBAL_TAG_SCHEMA = Settings.update_frontier_connection(Settings.GLOBAL_TAG_SCHEMA)
Settings.LOG_SCHEMA = Settings.update_frontier_connection(Settings.LOG_SCHEMA)
Settings.RUN_INFO_SCHEMA=Settings.update_frontier_connection(Settings.RUN_INFO_SCHEMA)


def main():
	service.start(UploadGTServer())


if __name__ == '__main__':
	main()


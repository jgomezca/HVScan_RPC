import service
import os
class InfoContainer:
    def __init__(self):
        pass

baseDBUrl = 'oracle://cms_orcon_adg'
ecalCondDB = service.getFrontierConnectionString({
	'account': 'CMS_COND_31X_ECAL',
	'frontier_name': 'PromptProd',
})
stripCondDB = baseDBUrl + '/CMS_COND_31X_STRIP'
rpcCondDB = baseDBUrl + '/CMS_COND_31X_RPC'

folders = InfoContainer()
#Directory, where temporary files are stored
folders.tmp_dir = os.environ['PI_file_dir_tmp']
folders.plots_dir = os.environ['PI_file_dir_plot'] 
folders.histo_dir = '/home/ryzzyj/backend/static_files/histo'
folders.xml_dir = os.environ['PI_file_dir_xml']
folders.table_dir = os.environ['PI_file_dir_html']
folders.iov_table_dir = os.environ['PI_file_dir_html']
folders.iov_table_name = 'iovtable.html'
folders.tag_table_name = 'tagtable.html'
folders.trend_plots_dir = os.environ['PI_file_dir_plot_trend']
folders.json_dir = os.environ['PI_file_dir_json']

db_data = InfoContainer()
db_data.users_db_conn_str = 'sqlite:///Users.db'
db_data.auth_path = ''

general = InfoContainer()
general.date_format = '%d/%m/%y %H:%M:%S'

skippedTags = set([
	'EcalLaserAPDPNRatios_data_20120814_2011-2012_v0',
])


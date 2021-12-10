from pyfiles.data_client import DataClient, MySqlServer
from pyfiles.com_lib import *


data_client = DataClient()
mysql = MySqlServer()
basic_info = BasicInfo(mysql)
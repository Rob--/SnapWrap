from snap import Snap
from snapchat import Snapchat
import requests.packages, logging

requests.packages.urllib3.disable_warnings()
logging.getLogger("requests").setLevel(logging.WARNING)
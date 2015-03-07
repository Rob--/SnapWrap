from snapchat import Snapchat
from requests.exceptions import HTTPError, ConnectionError
import logging
import time
import utils

class CustomBot(Snapchat):
    def on_snap(self, sender, snap):
        self.save_snap(snap, "A:\Python\Projects\SnapWrap\SnapWrap")
        
    def on_friend_add(self, friend):
        self.add_friend(friend)

    def on_friend_delete(self, friend):
        self.delete_friend(friend)

logging.getLogger("requests").setLevel(logging.WARNING)

while True:
    try:
        try:
            bot = CustomBot(*["user", "pass"])
            bot.begin()
        except (HTTPError, ConnectionError) as e:
            time.sleep(180)
    except Exception:
        print(Exception.message)
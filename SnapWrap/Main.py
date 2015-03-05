from bot import SnapchatBot
import time
from requests.exceptions import HTTPError, ConnectionError
import logging

class CustomBot(SnapchatBot):
    
    def on_snap(self, sender, snap):
        self.post_story(snap)
        
    def on_friend_add(self, friend):
        self.add_friend(friend)

    def on_friend_delete(self, friend):
        self.delete_friend(friend)

logging.getLogger("requests").setLevel(logging.WARNING)
import pdb
pdb.set_trace()
while True:
    try:
        bot = CustomBot(*["ghcollege", "garthhillcollege1"])
        bot.listen()
    except (HTTPError, ConnectionError) as e:
        time.sleep(180)
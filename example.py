from SnapWrap import Snapchat
import logging

class CustomBot(Snapchat):
    def on_snap(self, sender, snap):
	self.send_snap(snap, sender)
        self.save_snap(snap, "C:\Snapchat\Snaps")
        
    def on_friend_add(self, friend):
        self.add_friend(friend)
        self.send_snap(self.from_file("C:\Snapchat\welcome.jpg", friend))

    def on_friend_delete(self, friend):
        self.delete_friend(friend)

logging.getLogger("requests").setLevel(logging.WARNING)

bot = CustomBot(*["user", "pass"])
bot.begin()

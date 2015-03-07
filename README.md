# SnapWrap
### Wrapper for the unofficial and undocumented Snapchat API.
---

SnapWrap is essentially an API wrapper for Snapchat's API but includes many functions that increase functionality and easability when conversing with Snapchat's API.
This library would not be possible without [agermanidis](https://github.com/agermanidis/SnapchatBot) or [martinp](https://github.com/martinp/pysnap).

SnapWrap's is based directly off agermanidis' library which includes martinp's library (to deal with low level access to the API) - this library includes the newest endpoints of Snapchat's API (`loq`) and are used when possible.

While finding, inspecting and implementing the newest endpoints I've documented everything I thought necessary. Documentation on the API will expand.

This library does slightly differ to agermanidis' apart from the endpoints. I've added more functions - such as an easier way to save snaps and the ability to mark a snap as replayed.

---
# Installation
---

`python setup.py install`

---

# Usage
---

The following code will simply initiate a class with three "listener" functions that are called after you call the `begin()` method. The library is being imported, logging in with the given credentials and then running a constant loop that will check for new updates (snap, friends, etc).

	from snapchat import Snapchat

    class CustomBot(Snapchat):
		def on_snap(self, sender, snap):
			self.send_snap(snap, sender)
        
		def on_friend_add(self, friend):
    		self.add_friend(friend)

		def on_friend_delete(self, friend):
    		self.delete_friend(friend)
	
	bot = CustomBot(*["user", "pass"])
	bot.begin()
	
# Functions
---

`begin(timeout, mark_viewed, mark_screenshotted, mark_replayed)` - starts a permanent cycle (with a delay on each iteration) of looking for new snaps and checking for newly added/deleted users. Parameters are optional.

`get_snaps(self, mark_viewed, mark_screenshotted, mark_replayed)` - retrieves all new snaps. Parameters are optional.

**timeout**: the delay per each iteration.

**mark_viewed**: (bool) mark snaps as viewed when opening them.

**mark_screenshotted**: (bool) mark snaps as have being screenshotted when opening them.

**mark_replayed**: (bool) mark snaps as have being replayed when opening them.

`get_friends()` - returns a list/array of people that you've added.

`get_best_friends()` - returns a list/array of your best friends.

`get_added_me()` - returns a list/array of people that have added you.

`get_blocked()` - returns a list/array of people you've blocked.

`send_snap(snap, recipients)` - sends a snap.

**snap**: the snap object.

**recipients**: either a string of the recipient or a list/array of recipients.

`get_friend_stories()` - returns a dict of your friends' usernames and their stories (`{'user1' : [storyObj1, storyObj2], "user2": [storyObj1]}`).

`update_privacy(friends_only=True)` - updates your privacy settings.

**friends_only**: a boolean as to whether only your friends can see your story and send you snaps or whether anyone can.

`post_story(snap)` - posts a snap to your story.

**snap**: the snap object.

`delete_story(snap)` - deletes a snap from your story.

**snap**: the snap object.

`add_friend(usrname)` - adds a user to your friends list.

`delete_friend(username)` - deletes a user from your friends list.

`block(username)` - blocks a user.

`unblock(username)` - unblocks a user.

**username**: username of the user you want to apply the action to.

`logout()` - logs the account out.

`clear_feed()` - clears the snap feed.

`clear_conversation(username)` - clears a conversation with the given user.

**username**: username of the user you want to clear the conversation with.

`save_snap(snap, dir)` - saves a snap to a directory.

**snap**: the snap object.

**dir**: the directory where the snap will be saved.
---

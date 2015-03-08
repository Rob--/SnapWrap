from time import sleep, strftime
import Client
from snap import Snap
from utils import save_snap
from constants import DEFAULT_TIMEOUT

class Snapchat(object):
    def __init__(self, username, password, **kwargs):        
        self.username = username
        self.password = password

        self.client = Client.Snapchat()
        info = self.client.login(username, password)
        if self.client.username is None and self.client.auth_token is None:
            self.log('Login failed, %s - %s' % (info['status'], info['message']))
            raise SystemExit(1)

        self.current_friends = self.get_friends()
        self.added_me = self.get_added_me()

        if hasattr(self, "initialize"):
            self.initialize(**kwargs)

    def log(self, message):
        print("[%s %s] %s" % (strftime("%x"), strftime("%X"), message))

    @staticmethod
    def process_snap(snap_obj, data):
        return Snap(
            data=data,
            snap_id=snap_obj['id'],
            media_type=snap_obj["media_type"],
            duration=snap_obj['time'],
            sender=snap_obj["sender"]
        )

    def begin(self, timeout=DEFAULT_TIMEOUT, mark_viewed=True, mark_screenshotted=False, mark_replayed=False):
        while True:
            self.log("Querying for new snaps...")
            snaps = self.get_snaps(mark_viewed, mark_screenshotted, mark_replayed)
            
            if hasattr(self, "on_snap"):
                for snap in snaps:
                    self.on_snap(snap.sender, snap)
                    
            added_me = self.get_added_me()

            newly_added = set(added_me).difference(self.added_me)
            newly_deleted = set(self.added_me).difference(added_me)

            self.added_me = added_me
            
            for friend in newly_added:
                self.log("%s has added me." % friend)
                if hasattr(self, "on_friend_add"):
                    self.on_friend_add(friend)
                    
            for friend in newly_deleted:
                self.log("%s has deleted me." % friend)
                if hasattr(self, "on_friend_delete"):
                    self.on_friend_delete(friend)

            sleep(timeout)

    def get_friends(self):
        return map(lambda fr: fr['name'], self.client.get_friends()['friends'])
    
    def get_best_friends(self):
        return map(lambda fr: fr['name'], self.client.get_friends()['bests'])

    def get_added_me(self):
        return map(lambda fr: fr['name'], self.client.get_friends()['added_friends'])
    
    def get_blocked(self):
        return self.client.get_blocked()

    def send_snap(self, snap, recipients):
        if not snap.uploaded:
            self.log("Status: uploading, id: %s." % snap.snap_id)
            snap.upload(self)

        if type(recipients) is not list:
            recipients = [recipients]
            
        recipients_str = ','.join(recipients)
        self.log("Status: sending snap to %s, id: %s." % (snap.snap_id, recipients_str ))
        self.client.send(snap.media_id, recipients_str, snap.duration)

    def get_friend_stories(self, update_timestamp=0):
        self.client.get_friend_stories(update_timestamp)
        
    def update_privacy(self, friends_only=False):
        return self.client.update_privacy(friends_only)
        
    def post_story(self, snap):
        if not snap.uploaded:
            self.log("Status: uploading, id: %s." % snap.snap_id)
            snap.upload(self)

        self.log("Status: sending snap to story, id: %s." % snap.snap_id)
        try:
            snap.story_id = self.client.send_to_story(snap)['json']['story']['id']
        except:
            pass

    def delete_story(self, snap):
        self.client.delete_story(snap.story_id)

    def add_friend(self, username):
        return self.client.add_friend(username)

    def delete_friend(self, username):
        return self.client.delete_friend(username)

    def block(self, username):
        return self.client.block(username)
        
    def unblock(self, username):
        return self.client.unblock(username)
        
    def logout(self):
        return self.client.logout()
    
    def clear_feed(self):
        return self.client.clear_feed()
    
    def clear_conversation(self, username):
        return self.client.clear_conversation(username)
    
    def save_snap(self, snap, dir):
        self.log("Saving %s to %s..." % (snap.snap_id, dir))
        save_snap(snap, dir)
        
    def get_snaps(self, mark_viewed=True, mark_screenshotted=False, mark_replayed=False):
        new_snaps = self.client.get_snaps()
        snaps = []

        for snap in new_snaps:
            if snap['status'] == 2:
                continue
            
            data = self.client.get_blob(snap["id"])
            
            if data is None:
                continue
            
            snap = self.process_snap(snap, data)
            
            if mark_viewed:
                self.client.mark_viewed(snap_id=snap.snap_id, sender=snap.sender, replayed=mark_replayed)
            if mark_screenshotted:
                self.client.mark_screenshot(snap_id=snap.snap_id, sender=snap.sender, replayed=mark_replayed)
                
            snaps.append(snap)

        return snaps

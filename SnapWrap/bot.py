import time, uuid
from PySnap.__init__ import Snapchat
from snap import Snap
from constants import DEFAULT_TIMEOUT

class SnapchatBot(object):
    def __init__(self, username, password, **kwargs):
        self.bot_id = uuid.uuid4().hex[0:4]

        self.username = username
        self.password = password

        self.client = Snapchat()
        result = self.client.login(username, password)
        if self.client.username is None and self.client.auth_token is None:
            self.log('Login failed:\nStatus: %s\nMessage: %s' % (result['status'], result['message']))
            raise SystemExit(1)

        self.current_friends = self.get_friends()
        print(self.current_friends)
        self.added_me = self.get_added_me()

        if hasattr(self, "initialize"):
            self.initialize(**kwargs)

    def log(self, message):
        print("[%s %s] %s" % (time.strftime("%x"), time.strftime("%X"), message))

    @staticmethod
    def process_snap(snap_obj, data):
        return Snap(
            data=data,
            snap_id=snap_obj['id'],
            media_type=snap_obj["media_type"],
            duration=snap_obj['time'],
            sender=snap_obj["sender"]
        )

    def mark_viewed(self, snap):
        self.client.mark_viewed(snap.snap_id)

    def listen(self, timeout=DEFAULT_TIMEOUT):
        while True:
            self.log("Querying for new snaps...")
            snaps = self.get_snaps()

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

            time.sleep(timeout)

    def get_friends(self):
        return map(lambda fr: fr['name'], self.client.get_friends(False))

    def get_added_me(self):
        return map(lambda fr: fr['name'], self.client.get_friends(True))

    def send_snap(self, recipients, snap):
        self.log("Preparing to send snap %s" % snap.snap_id)

        if not snap.uploaded:
            self.log("Uploading snap %s" % snap.snap_id)
            snap.upload(self)

        if type(recipients) is not list:
            recipients = [recipients]

        recipients_str = ','.join(recipients)

        self.log("Sending snap %s to %s" % (snap.snap_id, recipients_str))

        self.client.send(snap.media_id, recipients_str, snap.duration)

    def post_story(self, snap):
        if not snap.uploaded:
            self.log("Uploading snap")
            snap.upload(self)

        self.log("Posting snap as story")
        response = self.client.send_to_story(snap.media_id, snap.duration, snap.media_type)

        try:
            snap.story_id = response['json']['story']['id']
        except:
            pass

    def delete_story(self, snap):
        if snap.story_id is None:
            return

        self.client._request('delete_story', {
            'username': self.username,
            'story_id': snap.story_id
        })

    def add_friend(self, username):
        self.client.add_friend(username)

    def delete_friend(self, username):
        self.client.delete_friend(username)

    def block(self, username):
        self.client.block(username)

    def get_snaps(self, mark_viewed=True):
        snaps = self.client.get_snaps()
        ret = []

        for snap_obj in snaps:
            if snap_obj['status'] == 2:
                continue

            data = self.client.get_blob(snap_obj["id"])

            if data is None:
                continue

            snap = self.process_snap(snap_obj, data)

            if mark_viewed:
                self.mark_viewed(snap)

            ret.append(snap)

        return ret

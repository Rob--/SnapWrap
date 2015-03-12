#!/usr/bin/env python

import json
import os.path
from time import time
from datetime import date
from SnapWrap.Client.utils import (encrypt, decrypt, decrypt_story, make_media_id, request, timestamp, requests)
from SnapWrap.constants import (DEFAULT_DURATION, MEDIA_TYPE_VIDEO, MEDIA_TYPE_VIDEO_NO_AUDIO, MEDIA_TYPE_IMAGE,
                                PRIVACY_FRIENDS, PRIVACY_EVERYONE, FRIEND_BLOCKED)

def is_video(data):
    return len(data) > 1 and data[0:2] == b'\x00\x00'


def is_image(data):
    return len(data) > 1 and data[0:2] == b'\xFF\xD8'


def is_zip(data):
    return len(data) > 1 and data[0:2] == b'PK'


def get_file_extension(media_type):
    if media_type in (MEDIA_TYPE_VIDEO, MEDIA_TYPE_VIDEO_NO_AUDIO):
        return 'mp4'
    if media_type == MEDIA_TYPE_IMAGE:
        return 'jpg'
    return ''

def get_media_type(data):
    if is_video(data):
        return MEDIA_TYPE_VIDEO
    if is_image(data):
        return MEDIA_TYPE_IMAGE
    return None

def _map_keys(snap):
    return {
        u'id':                  (snap['id']     if 'id'     in snap else None),
        u'media_id':            (snap['c_id']   if 'c_id'   in snap else None),
        u'media_type':          (snap['m']      if 'm'      in snap else None),
        u'time':                (snap['t']      if 't'      in snap else None),
        u'sender':              (snap['sn']     if 'sn'     in snap else None),
        u'recipient':           (snap['rp']     if ''       in snap else None),
        u'status':              (snap['st']     if 'st'     in snap else None),
        u'screenshot_count':    (snap['c']      if 'c'      in snap else None),
        u'sent':                (snap['sts']    if 'sts'    in snap else None),
        u'opened':              (snap['ts']     if 'ts'     in snap else None)
    }
    
class Snapchat(object):
    def __init__(self):
        self._reset()

    def _request(self, endpoint, data=None, files=None, raise_for_status=True, req_type='post'):
        return request(endpoint, self.auth_token, data, files,  raise_for_status, req_type)

    def _reset(self):
        self.username = None
        self.auth_token = None
        
    def register(self, username, password, birthday, email):
        """
        Registers a Snapchat account.
        Returns: response identical to the one recieved when logging in if successful,
                 response from the request (includes a message/status) if unsuccessful.
        
        :param username: the username you wish to register.
        :param password: the password.
        :param birthday: the birthday. Needs to be in the format (string) 'YYYY-MM-DD', e.g. 1995-01-01. 
        :param email: the email address tied to the account.
        """
        result = self._request('loq/register', { 
            'age': date.today().year - int(birthday.split("-")[0]),
            'birthday': birthday,
            'dsig': 'd56e1a29cdcd6b0924cf',
            'dtoken1i': self._request('loq/device_id', {}).json()["dtoken1i"],
            'email': email,
            'password': password      
        }).json()
        
        if result['logged'] is False:
            if 'status' in result:
                print("Register failed, %s - %s" % (result['status'], result['message']))
            else:
                print("Register failed, %s" % (result['message']))
            return result
        
        if 'auth_token' in result:
            self.auth_token = result['auth_token']
        
        result = self._request('loq/register_username', { 
            'username': email,
            'selected_username' : username        
        }).json()
        
        if 'logged' in result:
            if result['logged'] is False:
                if 'status' in result:
                    print("Register failed, %s - %s" % (result['status'], result['message']))
                else:
                    print("Register failed, %s" % (result['message']))
                return result
        
        if 'auth_token' in result['updates_response']:
            self.auth_token = result['updates_response']['auth_token']
        if 'username' in result['updates_response']:
            self.username = result['updates_response']['username']
        return result
        
    def login(self, username, password):
        self._reset()
        result = self._request('loq/login', {                    
            'username': username,
            'password': password,
            'ptoken': str(requests.post(
                "https://android.clients.google.com/c2dm/register3",
                data={
                    'X-GOOG.USER_AID':'4002600885140111980',
                    'app':'com.snapchat.android',
                    'sender':'191410808405',
                    'cert':'49f6badb81d89a9e38d65de76f09355071bd67e7',  
                    'device':'4002600885140111980',
                    'app_ver':'508',
                    'info':'',
                },
                headers={
                    'app': 'com.snapchat.android',
                    'User-Agent': 'Android-GCM/1.4 (mako JDQ39)',
                    'Authorization' : 'AidLogin 4002600885140111980:7856388705669173275'
                }).content
            ).replace("token=", ""),
            'retry': '0',
            'dtoken1i': self._request('loq/device_id', {}).json()["dtoken1i"],
            'dsig': 'd56e1a29cdcd6b0924cf',
        }).json()

        if "status" in result:
                return result
        if 'auth_token' in result['updates_response']:
            self.auth_token = result['updates_response']['auth_token']
        if 'username' in result['updates_response']:
            self.username = result['updates_response']['username']
        return result
    
    def logout(self):
        """
        Logout of the Snapchat account.
        Returns: True if successful. False is unsuccessful.
        """
        return len(self._request('logout', {
            'username': self.username
        }).content) == 0

    def get_updates(self, update_timestamp=0):
        """
        Gets updates - user, friend, snap and conversation information.
        Returns: dict containing the response (in JSON format).
        
        :param update_timestamp: optional timestamp (epoch in seconds) to limit updates.
        """
        result = self._request('loq/all_updates', {
            'username': self.username,
            'features_map': '{"conversations_delta_response":true,"stories_delta_response":true}'
        }).json()
        if 'auth_token' in result['updates_response']:
            self.auth_token = result['updates_response']['auth_token']
        return result

    def get_snaps(self, update_timestamp=0):
        """
        Gets snaps - finds all new (unopened) snaps.
        Returns: list of snap object containing meta data.
        
        :param update_timestamp: optional timestamp (epoch in seconds) to limit updates.
        """
        return[_map_keys(snap) for snap in self.get_updates(update_timestamp)['conversations_response'][0]['pending_received_snaps']
                if 'c_id' not in snap]
        
    def get_friend_stories(self, update_timestamp=0):
        """
        Get your friends' stories.
        Returns: Dict containing users and their stories.
        
        Structure:
        {'user1' : [storyObj1, storyObj2], "user2": [storyObj1]}

        :param update_timestamp: optional timestamp (epoch in seconds) to limit updates.
        """
        all = {}
        for friend in self.get_updates(update_timestamp)['stories_response']['friend_stories']:
            stories = []
            for story in friend['stories']:
                obj = story['story']
                obj['sender'] = friend['username']
                stories.append(obj)
            all[friend['username']] = stories
        return all

    def get_story_blob(self, story_id, story_key, story_iv):
        """
        Gets the image/video of a given story snap.
        Returns: the decrypted data of given story snap, None if the data is invalid.
        
        :param story_id: media id of the story snap.
        :param story_key: encryption key of the story.
        :param story_iv: encryption IV of the story.
        """
        r = self._request('story_blob', {
            'story_id': story_id
        }, raise_for_status=False, req_type='get')
        
        data = decrypt_story(r.content, story_key, story_iv)
        if any((is_image(data), is_video(data), is_zip(data))):
            return data
        return None

    def get_blob(self, snap_id):
        """
        Gets the image/video of a given snap.
        Returns: the decrypted data of given snap, None if the data is invalid.
        
        param: snap_id: id of the given snap.
        """
        data = decrypt(self._request('ph/blob', {
            'username': self.username, 'id': snap_id
        }, raise_for_status=False).content)
        
        if any((is_image(data), is_video(data), is_zip(data))):
            return data
        return None

    def send_events(self, events, data=None):
        """
        Send event data. This is used update information about snaps, users and conversations.
        Returns: True if successful, False if unsuccessful.
        
        :param events: list of events to send (list of dicts).
        :param data: dict of additional data to send.
        """
        if data is None:
            data = {}
        return len(self._request('bq/update_snaps', {
            'username': self.username,
            'events': json.dumps(events),
            'json': json.dumps(data)
        }).content) == 0

    def mark_viewed(self, snap_id, sender, view_duration=1, replayed=False):
        """
        Marks a given snap as viewed.
        Returns: True if successful, False if unsuccessful.

        :param snap_id: the id of the snap.
        :param sender: the sender of the snap.
        :param view_duration: number of seconds the snap was viewed.
        :param replayed: mark the snap as having been replayed.
        """
        now = time()
        data = {snap_id: {u"c": 0, "replayed": 1 if replayed else 0, u"sv": view_duration, u"t": now}}
        events = [
            {
                u"eventName": u"SNAP_VIEW",
                u"params": {
                    "time": view_duration,
                    "id": snap_id,
                    "type":"IMAGE",
                    "sender": sender
                },
                u'ts': int(round(now)) - view_duration
            }
        ]
        return self.send_events(events, data)

    def mark_screenshot(self, snap_id, sender, view_duration=1, replayed=False):
        """Mark a snap as screenshotted
        Returns true on success.

        :param snap_id: Snap id to mark as viewed
        :param sender: the sender of the snap.
        :param view_duration: Number of seconds snap was viewed
        :param replayed: mark the snap as having been replayed.
        """
        now = time()
        data = {snap_id: {u"c": 0, "replayed": 1 if replayed else 0, u"sv": view_duration, u"t": now}}
        events = [
            {
                u"eventName": u"SNAP_SCREENSHOT",
                u"params": {
                    "time": view_duration,
                    "id": snap_id,
                    "type":"IMAGE",
                    "sender": sender
                },
                u'ts': int(round(now)) - view_duration
            }
        ]
        return self.send_events(events, data)

    def update_privacy(self, friends_only):
        """
        Change privacy settings (from whom can you receive snaps from).
        Returns: True if successful, False if unsuccessful.

        :param friends_only: True is friends only, False if everyone.
        """
        return self._request('ph/settings', {
            'username': self.username,
            'action': 'updatePrivacy',
            'privacySetting': PRIVACY_FRIENDS if friends_only else PRIVACY_EVERYONE
        }).json()['param'] == str(PRIVACY_FRIENDS if friends_only else PRIVACY_EVERYONE)
        
    def update_story_privacy(self, friends_only):
        """
        Change story privacy settings (from whom can you receive snaps from).
        Returns: True if successful, False if unsuccessful.

        :param friends_only: True is friends only, False if everyone.
        """
        return self._request('ph/settings', {
            'username': self.username,
            'action': 'updateStoryPrivacy',
            'privacySetting': "FRIENDS" if friends_only else "EVERYONE"
        }).json()['param'] == str("FRIENDS" if friends_only else "EVERYONE")
        
    def update_birthday(self, birthday):
        """
        Change your birthday.
        Returns: True if successful, False if unsuccessful.

        :param birthday: the birthday, needs to be in the format "MM-DD".
        """
        return self._request('ph/settings', {
            'username': self.username,
            'action': 'updateBirthday',
            'birthday': birthday
        }).json()["logged"]
        
    def update_email(self, email):
        """
        Change your email.
        Returns: True if successful, False if unsuccessful.

        :param email: the email address.
        """
        return self._request('ph/settings', {
            'username': self.username,
            'action': 'updateEmail',
            'email': email
        }).json()["logged"]
        
    def update_number_of_best_friends(self, number):
        """
        Change the number of best friends to be displayed.
        Returns: True if successful, False if unsuccessful.

        :param number: the number of best friends to be displayed.
        """
        return self._request('bq/set_num_best_friends', {
            'username': self.username,
            'num_best_friends': number
        }).json()["logged"]

    def get_friends(self):
        """
        Retrieves the section of the response from getting updates about friends.
        Returns: JSON that consists of 'bests', 'friends', and 'added_friends'.
        """
        return self.get_updates()['friends_response']

    def add_friend(self, username):
        """
        Add a user to your friends list.
        Returns: True if successful, False if unsuccessful.
        
        :param username: Username to add as a friend
        """
        return self._request('bq/friend', {   
            'friend_source': 'ADDED_BY_USERNAME', 
            'username': self.username,
            'action': 'add',
            'friend': username,
        }).json()['logged']

    def delete_friend(self, username):
        """
        Delete a user from your friends list.
        Returns: True if successful, False if unsuccessful.

        :param username: username of the user to remove.
        """
        return self._request('bq/friend', {   
            'friend_source': 'ADDED_BY_USERNAME', 
            'username': self.username,
            'action': 'delete',
            'friend': username,
        }).json()['logged']
        
    def delete_story(self, story_id):
        if story_id is None:
            return
        self.client._request('bq/delete_story', {
            'username': self.username,
            'story_id': story_id
        })

    def block(self, username):
        """
        Block a user.
        Returns: True if successful, False if unsuccessful.

        :param username: username of the user to block.
        """
        return self._request('bq/friend', {
            'action': 'block',
            'friend': username,
            'username': self.username
        }).json()['logged']

    def unblock(self, username):
        """
        Unblock a user.
        Returns: True if successful, False if unsuccessful.

        :param username: username of the user to unblock.
        """
        return self._request('bq/friend', {
            'action': 'unblock',
            'friend': username,
            'username': self.username
        }).json()['logged']

    def get_blocked(self):
        """
        Finds blocked users.
        Returns: list of currently blocked users.
        """
        return [f for f in self.get_friends()['friends'] if f['type'] == FRIEND_BLOCKED]

    def upload(self, path):
        """
        Uploads media from a given path.
        Returns: media id if successful, None if unsuccessful.
        """
        if not os.path.exists(path):
            raise ValueError('No such file: {0}'.format(path))

        with open(path, 'rb') as f:
            data = f.read()

        media_type = get_media_type(data)
        if media_type is None:
            raise ValueError('Could not determine media type for given data.')

        media_id = make_media_id(self.username)
        r = self._request('ph/upload', {  
            'media_id': media_id,
            'username': self.username,
            'type': media_type
        }, files={'data': encrypt(data)})
        return media_id if len(r.content) == 0 else None

    def send(self, media_id, recipients, duration=DEFAULT_DURATION):
        """
        Sends a snap.
        The snap needs to be uploaded first as this returns a media_id that is used in this method.
        Returns: True if successful, False if unsuccessful.
        """
        return len(self._request('loq/send', {                
            'media_id': media_id,
            'time': int(duration),
            'username': self.username,
            'zipped': 0,
            'recipients': json.dumps(recipients),
        }).content) == 0

    def send_to_story(self, snap):
        """
        Sends a snap to your story.
        The snap needs to be uploaded first as this returns a media_id that is used in this method.
        Returns: The story id of the snap.
        """
        return self._request('bq/post_story', {
            'caption_text_display': snap.sender, 
            'story_timestamp': timestamp(),
            'media_id': snap.media_id,
            'client_id': snap.media_id,
            'time': snap.duration,
            'username': self.username,
            'my_story': 'true',
            'zipped': '0',
            'type': snap.media_type
        })['json']['story']['id']
                
    def clear_feed(self):
        """
        Clears the user's feed
        Returns: True if successful, False if unsuccessful.
        """
        return len(self._request('ph/clear', {
            'username': self.username
        }).content) == 0
    
    def clear_conversation(self, user):
        """
        Clears conversations for the given users.
        Returns: True if successful, False if unsuccessful.
        """
        return len(self._request('loq/clear_conversation', {
            'conversation_id': '{u}~{username}'.format(u=user, username=self.username),
            'username': self.username
        }).content) == 0 
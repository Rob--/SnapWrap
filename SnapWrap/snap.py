import subprocess, uuid
from PIL import Image
from StringIO import StringIO

from SnapWrap.utils import guess_type, create_temporary_file, get_video_duration, resize_image, file_extension_for_type
from constants import MEDIA_TYPE_IMAGE, MEDIA_TYPE_VIDEO, MEDIA_TYPE_VIDEO_WITHOUT_AUDIO, DEFAULT_DURATION

class UnknownMediaType(Exception):
    pass

class Snap(object):
    @staticmethod
    def from_file(path, duration=DEFAULT_DURATION, username=None):
        media_type = guess_type(path)

        if media_type is MEDIA_TYPE_VIDEO or media_type is MEDIA_TYPE_VIDEO_WITHOUT_AUDIO:
            if duration is None: duration = get_video_duration(path)
            tmp = create_temporary_file(".snap.mp4")
            output_path = tmp.name
            subprocess.Popen(["ffmpeg", "-y", "-i", path, output_path]).wait()

        elif media_type is MEDIA_TYPE_IMAGE:
            image = Image.open(path)
            tmp = create_temporary_file(".jpg")
            output_path = tmp.name
            resize_image(image, output_path)
            if duration is None: duration = DEFAULT_DURATION
        else:
            raise UnknownMediaType("Could not determine media type of the file.")

        return Snap(path=output_path, media_type=media_type, duration=duration, self_post=True, username=username)

    @staticmethod
    def from_image(img, duration=DEFAULT_DURATION):
        f = create_temporary_file(".jpg")
        resize_image(img, f.name)
        return Snap(path=f.name, media_type=MEDIA_TYPE_IMAGE, duration=duration)

    def upload(self, bot):
        self.media_id = bot.client.upload(self.file.name)
        self.uploaded = True

    def __init__(self, **opts):
        self.uploaded = False
        self.duration = opts['duration']
        self.media_type = opts['media_type']
        self.story_id = None
        
        if 'self_post' in opts:
            self.sender = opts['username']
            self.from_me = True
        
        if 'sender' in opts:
            self.sender = opts['sender']
            self.snap_id = opts['snap_id']
            self.from_me = False
        else:
            self.snap_id = uuid.uuid4().hex
            self.from_me = True

        if 'data' in opts:
            self.media_type = opts['media_type']
            self.file = create_temporary_file("." + file_extension_for_type(opts['media_type']))
            
            if self.media_type is MEDIA_TYPE_VIDEO or self.media_type is MEDIA_TYPE_VIDEO_WITHOUT_AUDIO:
                self.file.write(opts['data'])
                self.file.flush()
            else:
                resize_image(Image.open(StringIO(opts['data'])), self.file.name)
        else:
            path = opts['path']
            self.file = open(path)

"""
Where uploaded files live.

Locally they go to media/. On hosts with a throwaway disk (Render's free plan wipes it on every deploy),
set CLOUDINARY_URL and images go to Cloudinary through STORAGES["default"]; video fields use this callable
so MP4s are uploaded as Cloudinary *video* resources rather than images.
"""
from django.conf import settings
from django.core.files.storage import default_storage


def video_storage():
    if getattr(settings, "CLOUDINARY_ENABLED", False):
        from cloudinary_storage.storage import VideoMediaCloudinaryStorage

        return VideoMediaCloudinaryStorage()
    return default_storage

import math
import re

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from tinymce.models import HTMLField

from apps.core.models import OrderedModel, TimeStampedModel
from apps.core.storage import video_storage
from apps.core.utils import OptimizedImagesMixin


class Category(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status="published", published_at__lte=timezone.now()).order_by("-published_at")


class Post(OptimizedImagesMixin, TimeStampedModel):
    STATUS_CHOICES = [("draft", "Draft"), ("published", "Published")]
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=220)
    category = models.ForeignKey(Category, related_name="posts", null=True, blank=True, on_delete=models.SET_NULL)
    focus_area = models.ForeignKey("programs.FocusArea", related_name="posts", null=True, blank=True, on_delete=models.SET_NULL)
    excerpt = models.CharField(max_length=300, blank=True)
    body = HTMLField()
    cover = models.ImageField(upload_to="blog/", blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft", db_index=True)
    published_at = models.DateTimeField(default=timezone.now, db_index=True)
    is_featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0, editable=False)

    objects = PostQuerySet.as_manager()
    optimized_image_fields = ("cover",)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("news:detail", args=[self.slug])

    @property
    def summary(self):
        if self.excerpt:
            return self.excerpt
        text = re.sub(r"\s+", " ", strip_tags(self.body)).strip()
        return text[:220] + ("…" if len(text) > 220 else "")

    @property
    def cover_url(self):
        if self.cover:
            return self.cover.url
        if self.focus_area_id and self.focus_area.image:
            return self.focus_area.image.url
        return ""

    @property
    def reading_minutes(self):
        return max(1, math.ceil(len(strip_tags(self.body).split()) / 200))


class Album(OptimizedImagesMixin, TimeStampedModel):
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    cover = models.ImageField(upload_to="gallery/covers/", blank=True)
    date = models.DateField(default=timezone.localdate)
    focus_area = models.ForeignKey("programs.FocusArea", null=True, blank=True, on_delete=models.SET_NULL)
    is_published = models.BooleanField(default=True)

    optimized_image_fields = ("cover",)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("news:album", args=[self.slug])

    @property
    def cover_url(self):
        if self.cover:
            return self.cover.url
        first = self.photos.first()
        return first.image.url if first else ""


class Photo(OptimizedImagesMixin, OrderedModel):
    album = models.ForeignKey(Album, related_name="photos", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="gallery/%Y/%m/")
    caption = models.CharField(max_length=200, blank=True)
    consent_confirmed = models.BooleanField(
        default=False, help_text="Tick when people (especially children) in the photo have consented to publication.")

    optimized_image_fields = ("image",)

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return self.caption or f"Photo {self.pk}"


class Video(OptimizedImagesMixin, OrderedModel):
    """A YouTube video, or an MP4 uploaded straight to the site (e.g. from WhatsApp)."""

    title = models.CharField(max_length=150)
    caption = models.CharField(max_length=255, blank=True)
    youtube_id = models.CharField(max_length=20, blank=True, help_text="The part after v= in a YouTube link")
    file = models.FileField(upload_to="gallery/videos/", storage=video_storage, blank=True,
                            help_text="MP4 (H.264). Keep it under ~25 MB for mobile data.")
    poster = models.ImageField(upload_to="gallery/videos/posters/", blank=True, help_text="Still image shown before the video plays.")
    album = models.ForeignKey(Album, related_name="videos", null=True, blank=True, on_delete=models.SET_NULL)
    is_featured = models.BooleanField(default=False, help_text="Show on the home page.")

    optimized_image_fields = ("poster",)

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return self.title

    @property
    def is_local(self):
        return bool(self.file)

    @property
    def url(self):
        if self.file:
            return self.file.url
        return f"https://www.youtube.com/watch?v={self.youtube_id}" if self.youtube_id else ""

    @property
    def poster_url(self):
        if self.poster:
            return self.poster.url
        return f"https://i.ytimg.com/vi/{self.youtube_id}/hqdefault.jpg" if self.youtube_id else ""

    def clean(self):
        from django.core.exceptions import ValidationError

        if not self.youtube_id and not self.file:
            raise ValidationError("Add a YouTube ID or upload a video file.")

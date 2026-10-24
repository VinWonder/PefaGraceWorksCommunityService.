from django.contrib import admin
from django.utils.html import format_html

from .models import Album, Category, Photo, Post, Video


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "status", "published_at", "is_featured", "views"]
    list_filter = ["status", "category", "focus_area", "is_featured"]
    list_editable = ["status", "is_featured"]
    search_fields = ["title", "excerpt", "body"]
    prepopulated_fields = {"slug": ["title"]}
    date_hierarchy = "published_at"
    readonly_fields = ["views"]

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)


class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 3
    fields = ["thumb", "image", "caption", "consent_confirmed", "order"]
    readonly_fields = ["thumb"]

    @admin.display(description="")
    def thumb(self, obj):
        return format_html('<img src="{}" style="height:56px;border-radius:4px">', obj.image.url) if obj.image else ""


class VideoInline(admin.TabularInline):
    model = Video
    extra = 0
    fields = ["title", "file", "poster", "youtube_id", "is_featured", "order"]


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ["title", "date", "focus_area", "photo_count", "is_published"]
    list_filter = ["is_published", "focus_area"]
    prepopulated_fields = {"slug": ["title"]}
    inlines = [PhotoInline, VideoInline]

    @admin.display(description="Photos")
    def photo_count(self, obj):
        return obj.photos.count()


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ["thumb", "title", "source", "album", "is_featured", "order"]
    list_display_links = ["thumb", "title"]
    list_editable = ["is_featured", "order"]
    list_filter = ["is_featured", "album"]

    @admin.display(description="")
    def thumb(self, obj):
        return format_html('<img src="{}" style="height:48px;border-radius:4px">', obj.poster_url) if obj.poster_url else "—"

    @admin.display(description="Source")
    def source(self, obj):
        return "Uploaded file" if obj.is_local else f"YouTube: {obj.youtube_id}"

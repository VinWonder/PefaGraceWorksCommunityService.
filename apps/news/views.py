from django.core.paginator import Paginator
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, render

from .models import Album, Category, Photo, Post, Video


def post_list(request, slug=None):
    posts = Post.objects.published().select_related("category", "focus_area")
    category = None
    if slug:
        category = get_object_or_404(Category, slug=slug)
        posts = posts.filter(category=category)
    page = Paginator(posts, 9).get_page(request.GET.get("page"))
    return render(request, "news/list.html", {
        "page_obj": page, "category": category, "categories": Category.objects.all(),
    })


def post_detail(request, slug):
    post = get_object_or_404(Post.objects.published().select_related("category", "author"), slug=slug)
    Post.objects.filter(pk=post.pk).update(views=F("views") + 1)
    related = Post.objects.published().exclude(pk=post.pk)
    if post.category_id:
        related = related.filter(category=post.category)
    return render(request, "news/detail.html", {"post": post, "related": related[:3]})


def gallery(request):
    albums = Album.objects.filter(is_published=True).prefetch_related("photos").order_by("-date", "id")
    photos = Photo.objects.filter(album__is_published=True).select_related("album").order_by("album__id", "order", "id")
    videos = Video.objects.filter(Q(album__isnull=True) | Q(album__is_published=True)).select_related("album")
    return render(request, "news/gallery.html", {"albums": albums, "photos": photos, "videos": videos})


def album_detail(request, slug):
    album = get_object_or_404(Album, slug=slug, is_published=True)
    return render(request, "news/album.html", {
        "album": album, "photos": album.photos.all(), "videos": album.videos.all(),
    })

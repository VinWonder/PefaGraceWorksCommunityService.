"""
Load the WhatsApp photos and videos in static/img into the gallery and place the best ones around the site.

    python manage.py import_whatsapp_media                      # safe to run again: skips what is already there
    python manage.py import_whatsapp_media --replace            # re-import every file
    python manage.py import_whatsapp_media --ffmpeg C:/path/ffmpeg.exe

With ffmpeg available, videos are recompressed for mobile data, get a poster image, and the
home page hero gets a short silent "reel" loop. Without it, the original MP4s are used as they are.
"""
import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models import HeroSlide, SiteSettings
from apps.news.models import Album, Photo, Video
from apps.programs.models import FocusArea, Project

IMAGE = "WhatsApp Image 2026-10-24 at {}.jpeg"
VIDEO = "WhatsApp Video 2026-10-24 at {}.mp4"

# Albums, best photo first. The first photo becomes the album cover.
ALBUMS = [
    ("prison-ministry", "Prison ministry: Kibos and Kisumu Women's Prison", "faith-and-outreach",
     "Worship, Bibles, prayer and donated supplies for inmates at Kibos Maximum Security Prison, "
     "GK Prison Kibos Medium and Kisumu Women's Prison.", [
         ("11.29.1", "Worship with inmates: hands raised in praise"),
         ("11.29.10", "Praying with an inmate during the prison outreach"),
         ("11.29.99", "Worship and praise inside the prison hall"),
         ("11.29.292", "Hundreds gathered for an open-air prison service"),
         ("11.29.19", "Presenting a Bible to an inmate"),
         ("11.29.297", "A conversation with an inmate"),
         ("11.38.09", "Preaching inside the prison hall"),
         ("11.29.267", "Preaching at an open-air prison service"),
         ("11.29.11", "Handing out Bibles at the prison fellowship"),
         ("11.29.9", "Presenting a Bible at the prison fellowship"),
         ("11.38.103", "Greeting inmates after the service"),
         ("11.29.18", "Sharing the Word during a prison service"),
         ("11.29.24", "Sharing gifts and supplies with inmates"),
         ("11.29.25", "Greeting an inmate during the outreach"),
         ("11.29.26", "An open-air prison fellowship"),
         ("11.29.269", "Ministering in the prison yard"),
         ("11.29.276", "The team leading an open-air prison service"),
         ("11.29.290", "A gift for an inmate"),
         ("11.29.291", "Inmates gathering for the prison fellowship"),
         ("11.29.293", "Handing out Bibles in the prison yard"),
         ("11.38.0", "Bibles shared in the prison yard"),
         ("11.38.05", "An open-air service at the prison"),
         ("11.38.052", "Handing out Bibles to inmates"),
         ("11.29.190", "The outreach team at GK Prison Kibos Medium"),
         ("11.11.23", "Donated supplies delivered to Kibos Maximum Security Prison"),
         ("10.56.45", "Our team and visiting partners at Kisumu Women's Prison"),
         ("10.56.20", "Donated supplies delivered at the prison gate"),
         ("11.29.17", "Food and supplies for Kisumu Women's Prison"),
         ("11.29.303", "Supplies donated to the prison"),
         ("11.38.12", "Supplies delivered to Kisumu Women's Prison"),
     ]),
    ("baptisms", "Baptisms: new life in Christ", "faith-and-outreach",
     "Children, young people and adults taking the step of baptism.", [
         ("11.29.23", "Celebrating a child's baptism"),
         ("11.29.28", "Prayer at a baptism"),
         ("11.29.22", "Baptised into new life"),
         ("11.29.27", "A joyful baptism"),
         ("11.29.20", "A young believer being baptised"),
         ("11.29.21", "Baptism service"),
     ]),
    ("medical-camp", "Community medical camp", "health",
     "Free consultations, check-ups and health advice for families in Kolwa Central.", [
         ("11.29.286", "A free consultation at the medical camp"),
         ("11.29.287", "A child is checked at the medical camp"),
         ("11.29.280", "Families waiting to be seen at the medical camp"),
         ("11.29.277", "Registration at the community medical camp"),
     ]),
    ("children-and-youth", "Children and youth ministry", "education",
     "Worship, songs, dance, graduation days and fellowship with the children of our community.", [
         ("11.29.2", "Children celebrating together at the church"),
         ("11.29.30", "Children's graduation celebration"),
         ("11.29.29", "Children and leaders at the church compound"),
     ]),
    ("mission-and-community", "Mission team and community", "",
     "Visiting partners, tree planting and street outreach across Kisumu East.", [
         ("11.05.16", "The mission team with church members and visiting partners"),
         ("11.05.41", "Planting trees during the mission visit"),
         ("11.29.295", "Street outreach in the neighbourhood"),
     ]),
]

# (file stem, title, caption, second to take the poster from)
VIDEOS = [
    ("11.55.25", "Kids on the move: praise and dance", "Our children's ministry fills the church hall with joy.", 36),
    ("11.55.56", "Children's praise and worship", "Songs of worship led by the children of PEFA.", 12),
    ("11.55.19", "Children's worship in the church hall", "Sunday worship with our children's ministry.", 12),
    ("11.55.39", "Singing together", "The children's choir sings in the church hall.", 26),
]
VIDEO_ALBUM = "children-and-youth"
REEL = ("11.55.25", 30, 8)  # (video, start second, length) for the silent hero loop

# Where the strongest photos go around the site
SLIDES = [
    # (title, subtitle, button text, button url, photo, order, use reel)
    ("Empowered by faith, serving with grace", None, None, None, "11.29.2", 0, True),
    ("Hope behind prison walls", "Worship, Bibles and supplies for inmates at Kibos and Kisumu Women's Prison.",
     "See the prison ministry", "/gallery/prison-ministry/", "11.29.1", 1, False),
    ("Keeping every child in school", None, None, None, "11.29.30", 2, False),
    ("A clinic for 5,000 neighbours", None, None, None, "11.29.286", 3, False),
]
FOCUS_IMAGES = {"faith-and-outreach": "11.29.1", "health": "11.29.286", "education": "11.29.30"}
PROJECT_IMAGES = {"community-health-clinic": "11.29.280", "education-300-learners": "11.29.29"}
CHURCH_IMAGE = "11.05.16"

# Openly licensed photos (static/img/illustrative) for work we have no photos of yet: planned water and
# livelihood projects. The licences require this credit to be shown with the photo.
ILLUSTRATIVE_DIR = Path(settings.BASE_DIR) / "static" / "img" / "illustrative"
CREDITS = {
    "water-hand-pump": "Illustrative photo: Emerymakini / Wikimedia Commons, CC BY 4.0",
    "water-borehole-kilifi": "Illustrative photo: Nzili / Wikimedia Commons, CC BY-SA 4.0",
    "tailoring-training": "Illustrative photo: Minette Lontsie / Wikimedia Commons, CC BY-SA 4.0",
    "tailor-workshop": "Illustrative photo: Maina Pat Mbae / Wikimedia Commons, CC BY-SA 4.0",
    "computer-class": "Illustrative photo: Peterkariukimutuura / Wikimedia Commons, CC BY-SA 4.0",
}
ILLUSTRATIVE_SLIDES = {"Clean water for schools and homes": "water-hand-pump"}
ILLUSTRATIVE_FOCUS = {"water-and-sanitation": "water-hand-pump", "economic-empowerment": "tailoring-training"}
ILLUSTRATIVE_PROJECTS = {
    "wash-boreholes": "water-borehole-kilifi",
    "vocational-skills": "tailor-workshop",
    "community-resource-centre": "computer-class",
}


class Command(BaseCommand):
    help = "Import the WhatsApp photos and videos from static/img into the gallery, slides, focus areas and projects."

    def add_arguments(self, parser):
        parser.add_argument("--source", default=str(Path(settings.BASE_DIR) / "static" / "img"))
        parser.add_argument("--replace", action="store_true", help="Re-import files that are already in the gallery.")
        parser.add_argument("--ffmpeg", default="", help="Path to ffmpeg (found automatically if on PATH).")

    def handle(self, *args, **opts):
        self.src = Path(opts["source"])
        self.replace = opts["replace"]
        if not self.src.is_dir():
            raise CommandError(f"Source folder not found: {self.src}")
        self.ffmpeg = self._find_ffmpeg(opts["ffmpeg"])
        if not self.ffmpeg:
            self.stdout.write(self.style.WARNING("ffmpeg not found: videos will be copied uncompressed and without posters."))
        self.tmp = Path(tempfile.mkdtemp(prefix="pgcs-media-"))
        try:
            with transaction.atomic():
                albums = self._albums()
                self._videos(albums[VIDEO_ALBUM])
                self._placements()
        finally:
            shutil.rmtree(self.tmp, ignore_errors=True)
        self.stdout.write(self.style.SUCCESS(
            f"Gallery ready: {Photo.objects.count()} photos in {Album.objects.count()} albums, {Video.objects.count()} videos."))

    # ------------------------------------------------------------------
    def _find_ffmpeg(self, given):
        if given:
            if not Path(given).is_file():
                raise CommandError(f"ffmpeg not found at {given}")
            return given
        found = shutil.which("ffmpeg")
        if found:
            return found
        try:
            import imageio_ffmpeg

            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            return ""

    def _image(self, stem):
        path = self.src / IMAGE.format(stem)
        if not path.is_file():
            raise CommandError(f"Missing photo: {path.name}")
        return path

    def _assign(self, field, path, name):
        if path.suffix.lower() in (".jpg", ".jpeg"):
            field.save(name, self._web_jpeg(path), save=False)
            return
        with path.open("rb") as fh:
            field.save(name, File(fh), save=False)

    def _web_jpeg(self, path, max_size=(1920, 1920)):
        """Phone photos are 4032px and ~2 MB; shrink them the same way admin uploads are shrunk."""
        from PIL import Image, ImageOps

        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")
            img.thumbnail(max_size, Image.LANCZOS)
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=82, optimize=True, progressive=True)
        return ContentFile(buffer.getvalue())

    # ------------------------------------------------------------------
    def _albums(self):
        areas = {a.slug: a for a in FocusArea.objects.all()}
        albums = {}
        for order, (slug, title, focus, description, photos) in enumerate(ALBUMS):
            album, _ = Album.objects.update_or_create(slug=slug, defaults={
                "title": title, "description": description, "focus_area": areas.get(focus), "is_published": True})
            albums[slug] = album
            for i, (stem, caption) in enumerate(photos):
                photo = Photo.objects.filter(album=album, order=i).first() or Photo(album=album, order=i)
                photo.caption = caption
                if self.replace or not photo.image:
                    self._assign(photo.image, self._image(stem), f"{slug}-{i + 1:02d}.jpg")
                photo.save()
            if self.replace or not album.cover:
                self._assign(album.cover, self._image(photos[0][0]), f"{slug}-cover.jpg")
                album.save()
            self.stdout.write(f"  {title}: {len(photos)} photos")
        return albums

    def _run(self, *args):
        subprocess.run([self.ffmpeg, "-v", "error", "-y", *args], check=True)

    def _videos(self, album):
        for order, (stem, title, caption, poster_at) in enumerate(VIDEOS):
            source = self.src / VIDEO.format(stem)
            if not source.is_file():
                raise CommandError(f"Missing video: {source.name}")
            video = Video.objects.filter(title=title).first() or Video(title=title)
            video.caption, video.album, video.order, video.is_featured = caption, album, order, True
            name = f"children-ministry-{order + 1}"
            if self.replace or not video.file:
                mp4 = source
                if self.ffmpeg:
                    mp4 = self.tmp / f"{name}.mp4"
                    self._run("-i", str(source), "-c:v", "libx264", "-preset", "slow", "-crf", "28",
                              "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(mp4))
                self._assign(video.file, mp4, f"{name}.mp4")
            if self.ffmpeg and (self.replace or not video.poster):
                jpg = self.tmp / f"{name}.jpg"
                self._run("-ss", str(poster_at), "-i", str(source), "-frames:v", "1", "-q:v", "3", str(jpg))
                self._assign(video.poster, jpg, f"{name}.jpg")
            video.youtube_id = ""
            video.save()
            self.stdout.write(f"  Video: {title}")

    def _placements(self):
        reel = None
        if self.ffmpeg:
            stem, start, length = REEL
            reel = self.tmp / "hero-reel.mp4"
            self._run("-ss", str(start), "-t", str(length), "-i", str(self.src / VIDEO.format(stem)), "-an",
                      "-vf", "scale=360:-2", "-c:v", "libx264", "-preset", "slow", "-crf", "30",
                      "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(reel))

        for title, subtitle, button, url, stem, order, use_reel in SLIDES:
            slide = HeroSlide.objects.filter(title=title).first() or HeroSlide(title=title)
            if subtitle:
                slide.subtitle, slide.button_text, slide.button_url = subtitle, button, url
            slide.order, slide.is_active = order, True
            if self.replace or not slide.image:
                self._assign(slide.image, self._image(stem), f"slide-{order + 1}.jpg")
            if use_reel and reel and (self.replace or not slide.video):
                self._assign(slide.video, reel, "hero-reel.mp4")
            slide.save()
        # Slides without a real photo of their own go last so the opening run is all photography.
        HeroSlide.objects.filter(image="").update(order=10)

        for slug, stem in FOCUS_IMAGES.items():
            area = FocusArea.objects.filter(slug=slug).first()
            if area and (self.replace or not area.image):
                self._assign(area.image, self._image(stem), f"{slug}.jpg")
                area.save()
        for slug, stem in PROJECT_IMAGES.items():
            project = Project.objects.filter(slug=slug).first()
            if project and (self.replace or not project.image):
                self._assign(project.image, self._image(stem), f"{slug}.jpg")
                project.save()
        site = SiteSettings.load()
        if self.replace or not site.church_block_image:
            self._assign(site.church_block_image, self._image(CHURCH_IMAGE), "church-block.jpg")
            site.save()
        self.stdout.write("  Placed photos on hero slides, focus areas, projects and the church block.")
        self._illustrative()

    def _illustrative(self):
        def place(obj, name, filename):
            if obj and (self.replace or not obj.image):
                self._assign(obj.image, ILLUSTRATIVE_DIR / f"{name}.jpg", filename)
                obj.image_credit = CREDITS[name]
                obj.save()

        for title, name in ILLUSTRATIVE_SLIDES.items():
            slide = HeroSlide.objects.filter(title=title).first()
            place(slide, name, f"slide-{name}.jpg")
            if slide and slide.image:
                HeroSlide.objects.filter(pk=slide.pk).update(order=4)
        for slug, name in ILLUSTRATIVE_FOCUS.items():
            place(FocusArea.objects.filter(slug=slug).first(), name, f"{slug}.jpg")
        for slug, name in ILLUSTRATIVE_PROJECTS.items():
            place(Project.objects.filter(slug=slug).first(), name, f"{slug}.jpg")
        self.stdout.write("  Added credited illustrative photos for water and livelihood work.")

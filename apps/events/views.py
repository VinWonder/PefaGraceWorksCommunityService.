from datetime import datetime, time
from datetime import timezone as dt_timezone

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.core.utils import notify_person, rate_limit

from .forms import RegistrationForm
from .models import Event


def event_list(request):
    return render(request, "events/list.html", {
        "upcoming": Event.objects.upcoming().select_related("focus_area"),
        "past": Event.objects.past().select_related("focus_area")[:9],
    })


def calendar(request):
    return render(request, "events/calendar.html")


def calendar_feed(request):
    """JSON feed consumed by FullCalendar."""
    events = Event.objects.filter(is_published=True)
    start = parse_date((request.GET.get("start") or "")[:10])
    end = parse_date((request.GET.get("end") or "")[:10])
    if start and end:
        tz = timezone.get_current_timezone()
        events = events.filter(end__gte=datetime.combine(start, time.min, tzinfo=tz),
                               start__lte=datetime.combine(end, time.max, tzinfo=tz))
    data = [{
        "title": e.title,
        "start": e.start.isoformat(),
        "end": e.end.isoformat(),
        "url": e.get_absolute_url(),
        "classNames": [f"ev-{e.kind}"],
    } for e in events[:500]]
    return JsonResponse(data, safe=False)


@rate_limit("event-register", limit=5)
def event_detail(request, slug):
    event = get_object_or_404(Event.objects.select_related("focus_area"), slug=slug, is_published=True)
    form = RegistrationForm(request.POST or None, event=event)
    if request.method == "POST" and event.can_register and form.is_valid():
        reg = form.save(commit=False)
        reg.event = event
        reg.save()
        notify_person(reg.email, f"You're registered: {event.title}",
                      f"Hello {reg.full_name},\n\nYou are registered for {event.title} on "
                      f"{timezone.localtime(event.start):%A %d %B %Y at %H:%M} at {event.venue}.\n\nGod bless,\nPEFA GraceWorks")
        messages.success(request, "You're registered. We'll see you there.")
        return redirect(event.get_absolute_url())
    return render(request, "events/detail.html", {"event": event, "form": form})


def event_ics(request, slug):
    event = get_object_or_404(Event, slug=slug, is_published=True)
    fmt = "%Y%m%dT%H%M%SZ"

    def esc(text):
        return (text or "").replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")

    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//PEFA GraceWorks//Events//EN", "BEGIN:VEVENT",
        f"UID:event-{event.pk}@pefagraceworks",
        f"DTSTAMP:{timezone.now().astimezone(dt_timezone.utc).strftime(fmt)}",
        f"DTSTART:{event.start.astimezone(dt_timezone.utc).strftime(fmt)}",
        f"DTEND:{event.end.astimezone(dt_timezone.utc).strftime(fmt)}",
        f"SUMMARY:{esc(event.title)}",
        f"LOCATION:{esc(event.venue + (', ' + event.address if event.address else ''))}",
        f"DESCRIPTION:{esc(event.summary)}",
        f"URL:{request.build_absolute_uri(event.get_absolute_url())}",
        "END:VEVENT", "END:VCALENDAR",
    ]
    response = HttpResponse("\r\n".join(lines), content_type="text/calendar")
    response["Content-Disposition"] = f'attachment; filename="{event.slug}.ics"'
    return response

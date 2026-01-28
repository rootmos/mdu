import logging
import os

logger = logging.getLogger(__name__)

from .. import app

ICS_URL = os.environ["S3_BASE_URL"] + "/GLM01-VT26.ics"
REDIRECT_URL = os.environ["S3_BASE_URL"] + "/GLM01-VT26.html"

def on_event(event):
    ks = app.select_courses()

    url = app.prepare_url(ks, start=app.START)
    events = app.do_fetch(url)
    ical = app.make_ical(events)
    app.do_put_s3(ICS_URL, ical)

    url = app.prepare_url(ks, fmt="")
    html = app.prepare_redirect(url)
    app.do_put_s3(REDIRECT_URL, html.encode("UTF-8"))

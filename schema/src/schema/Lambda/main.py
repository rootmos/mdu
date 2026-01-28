import logging
import os
import urllib.parse

import boto3

logger = logging.getLogger(__name__)

from .. import app

ICS_URL = os.environ["S3_BASE_URL"] + "/GLM01-VT26.ics"
REDIRECT_URL = os.environ["S3_BASE_URL"] + "/GLM01-VT26.html"

def parse_s3_url(url):
    p = urllib.parse.urlparse(url, scheme="s3")
    assert p.scheme == "s3"
    return p.netloc, p.path.lstrip("/")

def do_put_s3(s3_url, bs: bytes):
    logger.info("uploading to: %s", s3_url)
    s3 = boto3.client("s3")
    bucket, key = parse_s3_url(s3_url)

    if s3_url.endswith(".ics"):
        ct = "text/calendar"
    elif s3_url.endswith(".html"):
        ct = "text/html"
    else:
        ct = None

    s3.put_object(
        Bucket = bucket,
        Key = key,
        Body = bs,
        ACL = "public-read",
        ContentType = ct,
    )

def on_event(event):
    ks = app.select_courses()

    url = app.prepare_url(ks, start=app.START)
    events = app.do_fetch(url)
    ical = app.make_ical(events)
    do_put_s3(ICS_URL, ical)

    url = app.prepare_url(ks, fmt="")
    html = app.prepare_redirect(url)
    do_put_s3(REDIRECT_URL, html.encode("UTF-8"))

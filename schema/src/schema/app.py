import logging
import sys
import urllib.parse
import zoneinfo
from dataclasses import dataclass
from datetime import datetime, date
from io import BytesIO
from typing import Generator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from xml.dom import minidom

import boto3
import dateutil.parser
import icalendar

from . import util

logger = logging.getLogger(__name__)

KURSER = [
    "OAU258-AU258V26-",
    "OAU376-AU37AV26-",
    "OAU278-AU278V26-",
]

START = date.fromisoformat("2026-01-19")

TZ = zoneinfo.ZoneInfo("Europe/Stockholm")

KRONOX_URL_EXAMPLE = "https://webbschema.mdu.se/setup/jsp/SchemaXML.jsp?startDatum=idag&intervallTyp=a&intervallAntal=2&forklaringar=true&sokMedAND=false&sprak=SV&resurser="

def CDATA(e) -> str | None:
    for n in e.childNodes:
        if n.nodeType == n.CDATA_SECTION_NODE:
            # TODO assumption: only one CDATA section
            return n.data

def TEXT(e) -> str | None:
    for n in e.childNodes:
        if n.nodeType == n.TEXT_NODE:
            # TODO assumption: only one text node
            return n.data

def getSingularChild(tag, root):
    [e] = root.getElementsByTagName(tag)
    return e

def extract_posts(dom):
    schema = getSingularChild("schema", dom)
    for n in schema.childNodes:
        if n.tagName == "schemaPost":
            yield n

    more = getSingularChild("detFinnsFlerPoster", schema).getAttribute("varde")
    if more != "false":
        raise NotImplementedError("pagination required", more)

def extract_fields(post):
    fs = {}
    for f in post.getElementsByTagName("falt"):
        k = TEXT(getSingularChild("namn", f))
        v = CDATA(getSingularChild("varde", f))
        fs[k] = v
    return fs

def extract_resurser(post):
    rs = {}
    for rn in getSingularChild("resursTrad", post).getElementsByTagName("resursNod"):
        k = rn.getAttribute("resursTypId")
        v = CDATA(getSingularChild("resursId", rn))
        rs[k] = v
    return rs

def extract_kurs(post):
    for rn in getSingularChild("resursTrad", post).getElementsByTagName("resursNod"):
        if rn.getAttribute("resursTypId") == "UTB_KURSINSTANS_GRUPPER":
            return CDATA(getSingularChild("resursId", rn))
    raise RuntimeError("unable to extract kurs")

@dataclass
class Event:
    start: datetime
    end: datetime
    title: str
    course: str
    comment: str | None = None
    location: str | None = None

    def ical(self) -> icalendar.Event:
        e = icalendar.Event()
        e.add("dtstart", self.start)
        e.add("dtend", self.end)
        e.add("summary", f"{self.course} {self.title}")
        if self.comment is not None:
            e.add("description", self.comment)
        if self.location is not None:
            e.add("location", self.location)
        return e

def parse_post(post) -> Event:
    [e] = post.getElementsByTagName("bokatDatum")
    datum = dateutil.parser.parse(e.getAttribute("datum"), yearfirst=True).date()
    start = datetime.combine(datum, dateutil.parser.parse(e.getAttribute("startTid")).time(), tzinfo=TZ)
    slut = datetime.combine(datum, dateutil.parser.parse(e.getAttribute("slutTid")).time(), tzinfo=TZ)

    moment = CDATA(getSingularChild("moment", post))
    assert moment is not None
    kommentar = CDATA(getSingularChild("kommentar", post))

    fs = extract_fields(post)
    rs = extract_resurser(post)

    kurs_tillfälle = rs["UTB_KURSINSTANS_GRUPPER"]
    kurs = kurs_tillfälle[:kurs_tillfälle.find("-")]
    lokal = rs.get("RESURSER_LOKALER")

    return Event(
        start = start,
        end = slut,
        title = moment,
        course = kurs,
        comment = kommentar,
        location = lokal,
    )

def select_courses(*selections):
    if not selections:
        return set(KURSER)

    ks = set()
    for k0 in selections:
        for k1 in KURSER:
            if k1.startswith(k0):
                ks.add(k1)
    return ks

URL = str
def prepare_url(ks, fmt: str | None = None, start: date | None = None) -> URL:
    template = urlparse(KRONOX_URL_EXAMPLE)

    if fmt is not None:
        template = template._replace(path = template.path.replace("SchemaXML.jsp", f"Schema{fmt}.jsp"))

    qs = parse_qs(template.query)

    resurser = []
    for k in ks:
        resurser.append("k." + k[:k.find("-")] + "-")
        resurser.append("k." + k)
    qs["resurser"] = [ ",".join(resurser) ]

    if start is not None:
        qs["startDatum"] = [ start.isoformat() ]

    url = template._replace(query = urlencode(qs, doseq=True))
    return urlunparse(url)

def do_fetch(url: URL, sandbox=False) -> Generator[Event]:
    def fetch():
        with util.urlopen(url) as f:
            return f.read()
    if not sandbox:
        raw = fetch()
    else:
        raw = util.pickle_cache("schema.xml", fetch)

    dom = minidom.parse(BytesIO(raw))

    for post in extract_posts(dom):
        yield parse_post(post)

def make_ical(events) -> bytes:
    cal = icalendar.Calendar().new()
    for event in events:
        cal.add_component(event.ical())
    return cal.to_ical()

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

def prepare_redirect(url):
    html = "<html>"
    html += "<body>"
    html += "<script>"
    html += f'window.location.assign("{url}")'
    html += "</script>"
    html += "</body>"
    html += "</html>"
    return html

def run(args):
    ks = select_courses(*args.kurs)
    if args.url:
        print(prepare_url(ks, start=START, fmt=""))
        return

    if args.redirect:
        print(prepare_redirect(prepare_url(ks, start=START, fmt="")))
        return

    url = prepare_url(ks, start=START)
    events = do_fetch(url, sandbox=args.sandbox)
    ical = make_ical(events)

    if args.stdout:
        logger.debug("writing ICAL to stdout")
        sys.stdout.buffer.write(ical)

    if args.file is not None:
        logger.info("writing ICAL to: %s", args.file)
        with open(args.file, "bw") as f:
            f.write(ical)

    if args.s3:
        do_put_s3(args.s3_url, ical)

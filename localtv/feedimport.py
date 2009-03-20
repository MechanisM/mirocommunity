import datetime

import feedparser
from lxml.html.clean import clean_html
import vidscraper

from localtv import util, miro_util
from localtv.models import Video, Feed, FEED_STATUS_ACTIVE

def update_feeds(verbose=False):
    for feed in Feed.objects.filter(status=FEED_STATUS_ACTIVE):
        parsed_feed = feedparser.parse(feed.feed_url, etag=feed.etag)
        for entry in parsed_feed['entries']:
            if (Video.objects.filter(feed=feed,
                                     guid=entry['guid']).count()
                or Video.objects.filter(feed=feed,
                                        website_url=entry['link']).count()):
                if verbose:
                    print "Skipping %s" % entry['title']
                continue

            file_url = None
            embed_code = None

            video_enclosure = miro_util.getFirstVideoEnclosure(entry)
            if video_enclosure:
                file_url = video_enclosure['href']

            try:
                scraped_data = vidscraper.auto_scrape(
                    entry['link'], fields=['file_url', 'embed'])
                file_url = file_url or scraped_data.get('file_url')
                embed_code = scraped_data.get('embed')
            except vidscraper.errors.Error, e:
                if verbose:
                    print "Vidscraper error: %s" % e

            if not (file_url or embed_code):
                if verbose:
                    print (
                        "Skipping %s because it lacks file_url "
                        "or embed_code") % entry['title']
                continue

            video = Video(
                name=entry['title'],
                site=feed.site,
                description=clean_html(entry['summary']),
                file_url=file_url or '',
                embed_code=embed_code or '',
                when_submitted=datetime.datetime.now(),
                status=FEED_STATUS_ACTIVE,
                feed=feed,
                website_url=entry['link'])
            video.save()

            if entry.get('tags'):
                tags = util.get_or_create_tags(
                    [tag['term'] for tag in entry['tags']])

                for tag in tags:
                    video.tags.add(tag)

        feed.etag = parsed_feed.etag or ''
        feed.last_updated = datetime.datetime.now()
        feed.save()
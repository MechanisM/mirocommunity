# Miro Community - Easiest way to make a video website
#
# Copyright (C) 2009, 2010, 2011, 2012 Participatory Culture Foundation
#
# Miro Community is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Miro Community is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Miro Community. If not, see <http://www.gnu.org/licenses/>.

import os
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.template.defaultfilters import slugify
from django.test import TestCase
from haystack import connections
from tagging.models import Tag

from localtv.models import Video, Watch, Category, Feed, SavedSearch


class BaseTestCase(TestCase):
    def _clear_index(self):
        """Clears the search index."""
        backend = connections['default'].get_backend()
        backend.clear()

    def _update_index(self):
        """Updates the search index."""
        backend = connections['default'].get_backend()
        index = connections['default'].get_unified_index().get_index(Video)
        backend.update(index, index.index_queryset())

    def _rebuild_index(self):
        """Clears and then updates the search index."""
        self._clear_index()
        self._update_index()

    def create_video(self, name='Test.', status=Video.ACTIVE, site_id=1,
                     watches=0, categories=None, authors=None, tags=None,
                     update_index=True, **kwargs):
        """
        Factory method for creating videos. Supplies the following defaults:

        * name: 'Test'
        * status: :attr:`Video.ACTIVE`
        * site_id: 1

        In addition to kwargs for the video's fields, which are passed directly
        to :meth:`Video.objects.create`, takes a ``watches`` kwarg (defaults to
        0). If ``watches`` is greater than 0, that many :class:`.Watch`
        instances will be created, each successively one day further in the
        past.

        List of category and author instances may also be passed in as
        ``categories`` and ``authors``, respectively.

        """
        video = Video(name=name, status=status, site_id=site_id, **kwargs)
        video.save(update_index=update_index)

        for i in xrange(watches):
            self.create_watch(video, days=i)

        if categories is not None:
            video.categories.add(*categories)

        if authors is not None:
            video.authors.add(*authors)

        if tags is not None:
            video.tags = tags

        # Update the index here to be sure that the categories and authors get
        # indexed correctly.
        if status == Video.ACTIVE and site_id == 1:
            index = connections['default'].get_unified_index().get_index(Video)
            index._enqueue_update(video)
        return video

    def create_category(self, site_id=1, **kwargs):
        """
        Factory method for creating categories. Supplies the following
        default:

        * site_id: 1

        Additionally, ``slug`` will be auto-generated from ``name`` if not
        provided. All arguments given are passed directly to
        :meth:`Category.objects.create`.

        """
        if 'slug' not in kwargs:
            kwargs['slug'] = slugify(kwargs.get('name', ''))
        return Category.objects.create(site_id=site_id, **kwargs)

    def create_user(self, **kwargs):
        """
        Factory method for creating users. All arguments are passed directly
        to :meth:`User.objects.create`.

        """
        return User.objects.create(**kwargs)

    def create_tag(self, **kwargs):
        """
        Factory method for creating tags. All arguments are passed directly
        to :meth:`Tag.objects.create`.

        """
        return Tag.objects.create(**kwargs)

    def create_watch(self, video, ip_address='0.0.0.0', days=0):
        """
        Factory method for creating :class:`Watch` instances.

        :param video: The video for the :class:`Watch`.
        :param ip_address: An IP address for the watcher.
        :param days: Number of days to place the :class:`Watch` in the past.

        """
        watch = Watch.objects.create(video=video, ip_address=ip_address)
        watch.timestamp = datetime.now() - timedelta(days)
        watch.save()
        return watch

    def create_feed(self, feed_url, name=None, description='Lorem ipsum',
                    last_updated=None, status=Feed.ACTIVE, site_id=1,
                    **kwargs):
        if name is None:
            name = feed_url
        if last_updated is None:
            last_updated = datetime.now()
        return Feed.objects.create(feed_url=feed_url,
                                   name=name,
                                   description=description,
                                   last_updated=last_updated,
                                   status=status,
                                   site_id=site_id,
                                   **kwargs)

    def create_search(self, query_string, site_id=1, **kwargs):
        return SavedSearch.objects.create(query_string=query_string,
                                          site_id=site_id,
                                          **kwargs)

    def create_site(self, domain='example.com', name=None):
        if name is None:
            name = domain

        return Site.objects.create(domain=domain, name=name)

    def _data_file(self, filename):
        """
        Returns the absolute path to a file in our testdata directory.
        """
        return os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                'testdata',
                filename))

    def assertStatusCodeEquals(self, response, status_code):
        """
        Assert that the response has the given status code.  If not, give a
        useful error mesage.
        """
        self.assertEqual(response.status_code, status_code,
                          'Status Code: %i != %i\nData: %s' % (
                response.status_code, status_code,
                response.content or response.get('Location', '')))

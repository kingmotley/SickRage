# Author: duramato <matigonkas@outlook.com>
# URL: https://github.com/SiCKRAGETV/sickrage
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import generic
import json

from sickbeard import logger
from sickbeard import tvcache
from sickbeard import show_name_helpers
from sickbeard import db
from sickbeard.common import WANTED
from sickbeard.config import naming_ep_type
from sickbeard.helpers import sanitizeSceneName

class TORRENTPROJECTProvider(generic.TorrentProvider):

    def __init__(self):
        generic.TorrentProvider.__init__(self, "TorrentProject")

        self.supportsBacklog = True
        self.public = True
    
        self.urls = {'api': u'https://torrentproject.se/',}
        self.url = self.urls['api']
        self.minseed = None
        self.minleech = None
        self.cache = TORRENTPROJECTCache(self)

    def isEnabled(self):
        return self.enabled

    def _get_airbydate_season_range(self, season):
        if season == None:
            return ()
        year, month = map(int, season.split('-'))
        min_date = datetime.date(year, month, 1)
        if month == 12:
            max_date = datetime.date(year, month, 31)
        else:
            max_date = datetime.date(year, month+1, 1) -  datetime.timedelta(days=1)
        return (min_date, max_date)

    def _get_title_and_url(self, item):
        title, download_url, size, id, seeders, leechers = item
        if title:
            title = self._clean_title_from_provider(title)

        if url:
            url = url.replace('&amp;', '&')

        return (title, url)


    def _get_size(self, item):
        title, download_url, size, id, seeders, leechers = item
        if not size:
            size = 0
        return size


    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys(): #Mode = RSS, Season, Episode
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                searchURL = self.urls['api'] + "?s=" + search_string + "&out=json"
                logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG)
                torrents = self.getURL(searchURL, json=True)
                if int(torrents["total_found"]) == 0:
                    logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                    continue
                del torrents["total_found"]

                if not torrents:
                    logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                    continue

                results = []
                for i in torrents:
                    title = torrents[i]["title"]
                    seeders = torrents[i]["seeds"]
                    leechers = torrents[i]["leechs"]
                    if seeders < self.minseed or leechers < self.minleech:
                        logger.log("Torrent doesn't meet minimum seeds & leechers not selecting :   " + title, logger.DEBUG)
                        continue
                    hash = torrents[i]["torrent_hash"]
                    size = torrents[i]["torrent_size"]
                    trackerUrl = self.urls['api'] + "" + hash + "/trackers_json"
                    jdata = self.getURL(trackerUrl, json=True)
                    download_url = "magnet:?xt=urn:btih:" + hash + "&dn=" + title + "".join(["&tr=" + s for s in jdata])

                    if not all([title, download_url]):
                        continue
                        
                    item = title, download_url, size, id, seeders, leechers

                    if mode != 'RSS':
                        logger.log(u"Found result: %s " % title, logger.DEBUG)
                    items[mode].append(item)
                    
            # For each search mode sort all the items by seeders
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

class TORRENTPROJECTCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # set this 0 to suppress log line, since we aren't updating it anyways
        self.minTime = 0

    def _getRSSData(self):
        # no rss for torrentproject afaik,& can't search with empty string
        # newest results are always > 1 day since added anyways
        search_strings = {'RSS': ['']}
        return {'entries': {}}

provider = TORRENTPROJECTProvider()

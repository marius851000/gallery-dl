# -*- coding: utf-8 -*-

# Copyright 2015 Mike Fährmann
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extract manga-chapters and entire manga from http://mangapark.me/"""

from .common import Extractor, Message
from .. import text

class MangaparkMangaExtractor(Extractor):
    """Extract all chapters of a manga from mangapark"""
    category = "mangapark"
    subcategory = "manga"
    pattern = [r"(?:https?://)?(?:www\.)?mangapark\.me/manga/([^/]+)"]
    url_base = "http://mangapark.me"

    def __init__(self, match):
        Extractor.__init__(self)
        self.url_title = match.group(1)

    def items(self):
        yield Message.Version, 1
        for chapter in self.get_chapters():
            print(self.url_base + chapter)
            yield Message.Queue, self.url_base + chapter

    def get_chapters(self):
        """Return a list of all chapter urls"""
        page = self.request(self.url_base + "/manga/" + self.url_title).text
        needle = '<a class="ch sts sts_1" target="_blank" href="'
        pos = page.index('<div id="list" class="book-list">')
        return reversed(list(
            text.extract_iter(page, needle, '"', pos)
        ))


class MangaparkChapterExtractor(Extractor):
    """Extract a single manga-chapter from mangapark"""
    category = "mangapark"
    subcategory = "chapter"
    directory_fmt = ["{category}", "{manga}", "c{chapter:>03}{chapter-minor}"]
    filename_fmt = "{manga}_c{chapter:>03}{chapter-minor}_{page:>03}.{extension}"
    pattern = [(r"(?:https?://)?(?:www\.)?mangapark\.me/manga/"
                r"([^/]+/s(\d+)(?:/v(\d+))?/c(\d+)(\.\d+)?)")]

    def __init__(self, match):
        Extractor.__init__(self)
        self.part, self.version, self.volume, self.chapter, self.chminor = match.groups()

    def items(self):
        page = self.request("http://mangapark.me/manga/" + self.part + "?zoom=2").text
        data = self.get_job_metadata(page)
        yield Message.Version, 1
        yield Message.Directory, data
        for num, image in enumerate(self.get_images(page), 1):
            data.update(image)
            data["page"] = num
            yield Message.Url, data["url"], text.nameext_from_url(data["url"], data)

    def get_job_metadata(self, page):
        """Collect metadata for extractor-job"""
        data = {
            "category": self.category,
            "version": self.version,
            "volume": self.volume or "",
            "chapter": self.chapter,
            "chapter-minor": self.chminor or "",
            "lang": "en",
            "language": "English",
        }
        data = text.extract_all(page, (
            ("manga-id"  , "var _manga_id = '", "'"),
            ("chapter-id", "var _book_id = '", "'"),
            ("manga"     , "<h2>", "</h2>"),
            (None        , 'target="_blank" href="', ''),
            ("count"     , 'page 1">1 / ', '<'),
        ), values=data)[0]
        pos = data["manga"].rfind(" ")
        data["manga"] = data["manga"][:pos]
        return data

    @staticmethod
    def get_images(page):
        """Collect image-urls, -widths and -heights"""
        pos = 0
        while True:
            url   , pos = text.extract(page, ' target="_blank" href="', '"', pos)
            if not url:
                return
            width , pos = text.extract(page, ' width="', '"', pos)
            height, pos = text.extract(page, ' _heighth="', '"', pos)
            yield {
                "url": url,
                "width": width,
                "height": height,
            }

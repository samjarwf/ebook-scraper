#!/usr/bin/python3

import re
import sys
import time

from lxml import html
from lxml.etree import strip_tags
import requests

from scraper import Scraper

HEADERS = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36" }

class TWI_Scraper(Scraper):
    author = "pirateaba"

    # def get_toc(self):
    #     url = "https://wanderinginn.com/table-of-contents/"
    #     page = requests.get(url, headers=HEADERS)
    #     tree = html.fromstring(page.content)

    #     volumes = tree.xpath("//div[contains(@class, 'volume-wrapper')]")
    #     volume_data = []

    #     for volume in volumes:
    #         volume_name = volume.xpath(".//h2/text()")[0].strip()

    #         chapters = []
    #         chapter_entries = volume.xpath(".//div[contains(@class, 'chapter-entry')]")

    #         for ch in chapter_entries:
    #             try:
    #                 name = ch.xpath(".//a/text()")[0].strip()
    #                 link = ch.xpath(".//a/@href")[0].strip()
    #                 chapters.append({"name": name, "link": link})
    #             except IndexError:
    #                 continue

    #         volume_data.append({
    #             "name": volume_name,
    #             "chapters": chapters
    #         })

    #     self.volumes = volume_data

    #     # Debug print
    #     for v in self.volumes:
    #         print(f"{v['name']}: {len(v['chapters'])} chapters")



    def get_toc(self):
        url = "https://wanderinginn.com/table-of-contents/"
        toc = html.fromstring(requests.get(url=url, headers=HEADERS).content)

        # Find all volumes
        volume_wrappers = toc.xpath("//div[contains(@class, 'volume-wrapper')]")
        books = []

        for volume in volume_wrappers:
            # Extract volume name
            volume_name = volume.xpath(".//h2/text()")[0]
            book_wrappers = volume.xpath(".//div[contains(@class, 'book-wrapper')]")

            for book in book_wrappers:
                # Extract book details
                book_name_elements = book.xpath(".//a[contains(@class, 'book-title-num')]/text()")
                if not book_name_elements:
                    print(f"Skipping book due to missing title")
                    continue
                book_name = book_name_elements[0]

                book_title_text = book.xpath(".//span[contains(@class, 'book-title-text')]/text()")
                book_title = f"{book_name}{book_title_text[0]}" if book_title_text else book_name
                
                book_data = {
                    "name": book_name,
                    "title": book_title,
                    "subtitle": "The Wandering Inn",
                    "file": book_name.lower().replace(" ", "_") + ".epub",
                    "chapters": []
                }

                # Extract chapters
                chapters = book.xpath(".//div[contains(@class, 'chapter-entry')]")
                for chapter in chapters:
                    chapter_name = chapter.xpath(".//a/text()")[0]
                    chapter_link = chapter.xpath(".//a/@href")[0]
                    book_data["chapters"].append({"name": chapter_name, "link": chapter_link})

                books.append(book_data)
            

        self.books = books

        # for book in self.books:
        #      print(book)


    @staticmethod
    def get_chapter_data(chapter):
        # Be polite to the server
        time.sleep(1)

        # Fetch the chapter's HTML page
        r = requests.get(chapter["link"], headers=HEADERS)
        if r.status_code != 200:
            print(f"Error! Non-200 status code: {r.status_code}")
            raise Exception(f"Failed to fetch chapter: {chapter['link']}")

        page = html.fromstring(r.content)

        # Extract the publication date
        match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', chapter["link"])
        if match:
            year, month, day = match.groups()
            chapter["date"] = f"{year}-{month}-{day}"
        else:
            chapter["date"] = "Unknown"

        # Extract the content
        content_elements = page.xpath("//div[contains(@class, 'entry-content')]")
        if not content_elements:
            print(f"Warning: No content found for chapter: {chapter['link']}")
            chapter["content"] = html.Element("div")  # Empty content placeholder
            return chapter

        # Keep the content as an lxml element
        chapter["content"] = content_elements[0]

        # Clean up the content by removing ads or unwanted children
        children = chapter["content"].getchildren()
        if len(children) >= 2:  # Ensure there are at least two children to remove
            chapter["content"].remove(children[-2])
            chapter["content"].remove(children[-1])

        # Strip all `<a>` tags
        strip_tags(chapter["content"], "a")

        return chapter

if __name__ == "__main__":
	TWI_Scraper().scrape(6)
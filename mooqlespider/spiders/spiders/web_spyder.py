import scrapy
import re
import lxml
import unidecode
from lxml.html.clean import Cleaner
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule, CrawlSpider, Spider
from spiders.items import SpidersItem
from scrapy.selector import Selector
from Cryptodome.Cipher import AES
from scrapy.exceptions import CloseSpider
from scrapy.utils.request import request_fingerprint
from scrapy.http import Request



class Spiders(CrawlSpider):
    # The name of the spider
    name = "mooqledb"

    # The URLs to start with
    start_urls = ["http://quotes.toscrape.com/", "https://www.data-blogger.com/"]

    # This spider has one rule: extract all (unique and canonicalized) links, follow them and parse them using the parse_items
    rules = [
        Rule(LinkExtractor(canonicalize=True,unique=True, deny=('forum',), deny_domains=("reddit.com", "youtube.com", "facebook.com", "instagram.com", "twitter.com", "en.wikipedia.org", "4chan.org", "linkedin.com", "dailymotion.com", "tiktok.com", "9gag.com")), follow=True,callback="parse_items")
    ]

    # Method which starts the quests by visiting all URLs specified in start_urls
    def start_requests(self):
        print("Scraping starting...")
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)

    # Method for parsing items
    def parse_items(self, response):


        key = 'abcdefghijklmnop' #keylength must be 16char

        # Only extract canonicalized and unique links (with respect to the current page)
        links = LinkExtractor(canonicalize=False, unique=True).extract_links(response)
        items = []

        # Now go through all the found links
        for link in links:
            sel = Selector(response)
            # Get page title
            page_title = sel.xpath('//title/text()').extract()[0]
            # Get page content
            cleaner = Cleaner()
            cleaner.javascript = True
            cleaner.style = True
            page_html = sel.xpath('//body').extract()[0]
            # Get everything in script tag
            page_js = sel.xpath('//div/script').extract()
            # Remove Javascript and CSS
            page_html = cleaner.clean_html(page_html)
            # Extract text
            html_doc = lxml.html.document_fromstring(page_html)
            page_content = ' '.join(lxml.etree.XPath("//text()")(html_doc))
            page_content += ' ' + page_title
            page_content += ' '.join(page_js)
            page_content = page_content.lower()
            # Remove line breaks, tabs, extra spaces and symbols
            page_content = re.sub(r'[^\w]', ' ', page_content)
            page_content = re.sub('\n', ' ', page_content)
            page_content = re.sub('\r', ' ', page_content)
            page_content = re.sub('\t', ' ', page_content)
            page_content = re.sub(' +', ' ', page_content)
            page_content = re.sub('_', ' ', page_content )
            page_content = page_content.lstrip()
            page_content = unidecode.unidecode(page_content)
            page_content = str(encryptAES(key, page_content))
            tempstr = response.url
            tempstr = str(encryptAES(key,tempstr))
            item = SpidersItem()
            item['text'] = page_content
            item['url_from'] = tempstr
            
            yield item

        # Return all the found items
        return items


    def closed(self, spider):
        print("Scraping done")
    
# Encryption function
def encryptAES(key, plaintext): 
    # Initialise encryption using pycryptodome library
    # using AES, ECB
    cipher = AES.new(key.encode("utf8"), AES.MODE_ECB)
    
    # Split the string into individual words
    plaintext= plaintext.split()
    
    # For each word in the string, pad each word to a length % 16 = 0
    # by adding white spaces
    for i in range(len(plaintext)):
        while(True):
            if(len(plaintext[i]) % 16 > 0):
                plaintext[i] += ' '
            else:
                # Once the length is % 16 = 0, move onto the next word
                break
    
    # Revert from list of words into one string
    plaintext = "".join(plaintext)
    
    # Encode it using utf8
    msg =cipher.encrypt(plaintext.encode("utf8"))
    
    # Return the encoded ciphertext
    return (msg)
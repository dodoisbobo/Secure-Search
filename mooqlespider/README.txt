Libraries needed:
------------------------------
pip install unidecode: remove accented characters
pip install scrapy - core: web crawler
pip install pycryptodomex - evans: for encryption
pip install mysql.connector : shaoqi

Previous patch:
-----------------------
Included unidecode to convert characters to proper type to encryption
Edited code in pipelines.py that will remove duplicate URLs crawled and scraped


Latest patch:
-----------------------
Added deltafetch to skip sites that was already crawled
Added Splash to scrape <script> tag 
Added SQL statement in pipelines to delete duplicate that got passed deltafetch
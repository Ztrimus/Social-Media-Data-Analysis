"""
File: data_crawling.py
Project: social-media-data-analysis
File Created: 15th Sep 2023 3:26 am MST, Friday
Author: Saurabh Zinjad (GitHub: Ztrimus)
Email: zinjadsaurabh1997@gmail.com

Copyright (c) 2023 Saurabh Zinjad
"""
from mastodon import Mastodon
import local_config
import utils
import json

mastodon = Mastodon(
    client_id=local_config.CLIENT_ID,
    client_secret=local_config.CLIENT_SECRET,
    access_token=local_config.ACCESS_TOKEN,
    api_base_url=local_config.API_BASE_URL,
)

search_query = [
    "AIethics",
    "AIRegulation",
    "Artificial intelligence",
    "AI",
]  # "SocialSciences", "ml", "DataScience", "statistics"

unique_users = utils.get_unique_users(mastodon, search_query)

# Serialize and save the dictionary to a text file
with open("../data/data.json", "w", encoding="utf-8") as file:
    json.dump(
        list(unique_users.values()), file, ensure_ascii=False, indent=4, default=str
    )

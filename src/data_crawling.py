"""
File: data_crawling.py
Project: social-media-data-analysis
File Created: 15th Sep 2023 3:26 am MST, Friday
Author: Saurabh Zinjad (GitHub: Ztrimus)
Email: zinjadsaurabh1997@gmail.com

Copyright (c) 2023 Saurabh Zinjad
"""
from mastodon import Mastodon
import credentials
import config
import utils
import json

try:
    mastodon_server = Mastodon(
        client_id=credentials.CLIENT_ID,
        client_secret=credentials.CLIENT_SECRET,
        access_token=credentials.ACCESS_TOKEN,
        api_base_url=credentials.API_BASE_URL,
    )
    print("\n\nmastodon server connected.")

    search_query = config.QUERY

    unique_users = utils.unique_users_data_crawling(mastodon_server, search_query)

    # Serialize and save the dictionary to a text file
    with open(config.JSON_DATA_PATH, "w", encoding="utf-8") as file:
        json.dump(unique_users, file, ensure_ascii=False, indent=4)  # , default=str
except Exception as e:
    # Handle the exception
    print(f"An exception occurred: {e}")
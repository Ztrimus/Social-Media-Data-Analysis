'''
File: utils.py
Project: social-media-data-analysis
File Created: 19th Sep 2023 11:35 pm, Tuesday
Author: Saurabh Zinjad (GitHub: Ztrimus)
Email: zinjadsaurabh1997@gmail.com

Copyright (c) 2023 Saurabh Zinjad
'''

import collections
from typing import List
from mastodon import Mastodon

def get_unique_users(server: Mastodon, hashtags: List[str], api_method_list: List[str] = ["timeline_hashtag", "account_search", "search_v2"]):
    """ Get distinct users who post or talks about provided hashtags/topics.

    Args:
        server (Mastodon): Mastodon class object for specific server/instance's session.
        hashtags (List[str]): List of topics
        api_method_list (List[str], optional): list of masotdon APIs used during fetching distinct users. Defaults to ["account_search", "timeline_hashtag", "search_v2"].

    Returns:
        collections.defaultdict(): Set of distinct users
    """
    
    accounts = collections.defaultdict()

    for hashtag in hashtags:
        for api_method in api_method_list:
            match api_method:
                case "account_search":
                    temp_accounts = server.account_search(q=hashtag, limit=300)

                    for account in temp_accounts:
                        if account.id not in accounts:
                            accounts[account.id] = account

                case "timeline_hashtag":
                    last_id = 0
                    visited_pages = 0
                    # loop for getting paginated data
                    while True:
                        if last_id:
                            hashtag_data = server.timeline_hashtag(hashtag=hashtag, max_id=last_id)
                        else:
                            hashtag_data = server.timeline_hashtag(hashtag=hashtag)
                        
                        # check for end of pagination
                        hashtag_data_len = len(hashtag_data)                        
                        if hashtag_data_len <= 0 or visited_pages > 15:
                            break
                        last_id = hashtag_data[-1].id
                        visited_pages += 1

                        # add user of post into accounts data
                        for post in hashtag_data:
                            if post.account.id not in accounts:
                                accounts[post.account.id] = post.account
    
                case "search_v2":
                    offset = 0

                    while True:
                        fetched_accounts = server.search_v2(q=hashtag, result_type="accounts", offset=offset)

                        # check for end of pagination
                        fetched_accounts_len = len(fetched_accounts.accounts)
                        if  fetched_accounts_len <= 0:
                            break
                        offset += fetched_accounts_len

                        # add user of post into accounts data
                        for account in fetched_accounts.accounts:
                            if account.id not in accounts:
                                accounts[account.id] = account
    
    return accounts        


def post_content(server: Mastodon, id: int):
    return server.status(id).content
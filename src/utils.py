'''
File: utils.py
Project: social-media-data-analysis
File Created: 19th Sep 2023 11:35 pm, Tuesday
Author: Saurabh Zinjad (GitHub: Ztrimus)
Email: zinjadsaurabh1997@gmail.com

Copyright (c) 2023 Saurabh Zinjad
'''

import collections
import config
from typing import List
from mastodon import Mastodon

def unique_users_data_crawling(server: Mastodon, hashtags: List[str], api_method_list: List[str] = ["timeline_hashtag", "search_v2", "account_search"]):
    """ Get distinct users who post or talks about provided hashtags/topics.

    Args:
        server (Mastodon): Mastodon class object for specific server/instance's session.
        hashtags (List[str]): List of topics
        api_method_list (List[str], optional): list of masotdon APIs used during fetching distinct users. Defaults to ["account_search", "timeline_hashtag", "search_v2"].

    Returns:
        collections.defaultdict(): Set of distinct users
    """
    try:
        accounts = collections.defaultdict()

        # find users related to given hashtags
        print("User nodes collecting...")
        accounts = hashtag_based_user_data_by_diff_apis(server, accounts, hashtags, api_method_list)
        # find relations between users
        print("User relations filling...")
        accounts = fill_follower_following_list(server, accounts)
        # formatting steps for jsonification
        print("Users data formatting...")
        accounts = list(accounts.values())
        accounts = sorted(accounts, key=lambda x: x["followers_count"], reverse=True)

        print(f"\nCollected unique user nodes: {len(accounts)}\n")
        return accounts        
    except Exception as e:
        print(f"An exception occurred: {e}")

def hashtag_based_user_data_by_diff_apis(server: Mastodon, accounts: collections.defaultdict, hashtags: List[str], api_method_list: List[str] = ["timeline_hashtag", "search_v2", "account_search"]):
    try:
        for hashtag in hashtags:
            print(f"\tfor tag \"{hashtag}\"")
            for api_method in api_method_list:
                print(f"\t\tusing \"{api_method}\" API...")
                match api_method:
                    case "account_search":
                        temp_accounts = server.account_search(q=hashtag, limit=config.ACCOUNT_LIMIT)

                        for account in temp_accounts:
                            if account.id not in accounts and not account.bot:
                                accounts[account.id] = get_required_properties(account)

                    case "timeline_hashtag":
                        previous_page = server.timeline_hashtag(hashtag=hashtag.replace(" ",""))
                        hashtag_data = get_remaining_paginated_data(server, previous_page, limit=config.POST_LIMIT)
                        if len(hashtag_data):
                            # add user of posts into accounts data
                            for post in hashtag_data:
                                if post.account.id not in accounts and not post.account.bot:
                                    accounts[post.account.id] = get_required_properties(post.account)
        
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
                                if account.id not in accounts and not account.bot:
                                    accounts[account.id] = get_required_properties(account)
                                    
        return accounts
                        
    except Exception as e:
        print(f"An exception occurred: {e}")


def get_required_properties(account: dict):

    # TODO: more parameter to consider
    # featured Hashtags
    # AI related posts only
    # reboosted post
    try:
        formatted_account = {}

        formatted_account['id'] = account.id
        formatted_account['username'] = account.username
        formatted_account['display_name'] = account.display_name
        formatted_account['note'] = account.note
        formatted_account['followers_count'] = account.followers_count
        formatted_account['following_count'] = account.following_count
        formatted_account['followers'] = set()
        formatted_account['followings'] = set()
        formatted_account['statuses_count'] = account.statuses_count
        formatted_account['created_at'] = account.created_at.strftime('%Y-%m-%d %H:%M:%S') if account.created_at else account.created_at
        formatted_account['last_status_at'] = account.last_status_at.strftime('%Y-%m-%d %H:%M:%S') if account.last_status_at else account.last_status_at
        formatted_account['acct'] = account.acct
        formatted_account['bot'] = account.bot
        formatted_account['group'] = account.group
        formatted_account['url'] = account.url

        return formatted_account
    
    except Exception as e:
        print(f"An exception occurred: {e}")

def fill_follower_following_list(server: Mastodon, accounts: collections.defaultdict):
    try:
        account_id_list = set(accounts.keys())
        
        for index, id in enumerate(accounts):
            if index%50 == 0 or index == len(accounts)-1:
                print(f"\tfinding {index}th user - {accounts[id]['username']}'s relations...")
            previous_page = server.account_followers(id = id)
            followers = get_remaining_paginated_data(server, previous_page, limit=config.DATA_LIMIT)

            if len(followers):
                page_data_id_list = set(follower.id for follower in followers)

                existing_followers_in_accounts = account_id_list.intersection(page_data_id_list)

                for follower in existing_followers_in_accounts:
                        accounts[id]['followers'].add(follower)
                        accounts[follower]['followings'].add(id)
                
        for id in accounts:
            accounts[id]['followers'] = list(accounts[id]['followers'])
            accounts[id]['followings'] = list(accounts[id]['followings'])

        return accounts
    
    except Exception as e:
        print(f"An exception occurred: {e}")

def post_content(server: Mastodon, id: int):
    return server.status(id).content

def get_remaining_paginated_data(server: Mastodon, previous_page: any, limit: int = config.DATA_LIMIT):
    try:
        data = []

        if len(previous_page):
            data.extend(previous_page)
            current_page = None

            while True:
                current_page = server.fetch_next(previous_page)
                
                if current_page == previous_page or not current_page:
                    break

                data.extend(current_page)
                previous_page = current_page
                
                if len(data) >= limit:
                    break
        
        return data
    
    except Exception as e:
        print(f"An exception occurred: {e}")
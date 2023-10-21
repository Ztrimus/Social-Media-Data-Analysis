'''
File: utils.py
Project: social-media-data-analysis
File Created: 19th Sep 2023 11:35 pm, Tuesday
Author: Saurabh Zinjad (GitHub: Ztrimus)
Email: zinjadsaurabh1997@gmail.com

Copyright (c) 2023 Saurabh Zinjad
'''

import re
import config
import collections
import traceback
from typing import List
from mastodon import Mastodon
from bs4 import BeautifulSoup
from langdetect import detect
from googletrans import Translator

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
        # account_statuses
        # formatting steps for jsonification
        print("Users data formatting...")
        accounts = list(accounts.values())
        accounts = sorted(accounts, key=lambda x: x["followers_count"], reverse=True)

        print("\nUser nodes Info\n----------------")
        relational_data = []
        for user in accounts:
            if len(user['followers']) or len(user['followings']):
                relational_data.append(user)

        print(f"Collected unique user nodes: {len(accounts)}\n")
        print(f"connected nodes: {len(relational_data)}")
        
        return accounts        
    except Exception as e:
        print(f"An exception occurred: {e}")
        print(traceback.format_exc())

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
                                accounts[account.id] = format_account_data(account)

                    case "timeline_hashtag":
                        previous_page = server.timeline_hashtag(hashtag=hashtag.replace(" ",""))
                        hashtag_data = get_remaining_paginated_data(server, previous_page, limit=config.POST_LIMIT)
                        accounts = process_statuses(server, hashtag_data, accounts)
                        pass
        
                    case "search_v2":
                        offset = 0
                        
                        while True:
                            searched_data = server.search_v2(q=hashtag, offset=offset)
                            # TODO: remove result_type and handle for statuses

                            # add user of post into accounts data
                            for account in searched_data.accounts:
                                if account.id not in accounts and not account.bot:
                                    accounts[account.id] = format_account_data(account)
                            
                            accounts = process_statuses(server, searched_data.statuses, accounts)
                            
                            # check if accounts list ended or statuses list hit limit
                            if  len(searched_data.accounts) <= 0 or offset > config.POST_LIMIT:
                                break

                            offset += 20
                                    
        return accounts
                        
    except Exception as e:
        print(f"An exception occurred: {e}")
        print(traceback.format_exc())

def process_statuses(server:Mastodon, posts: List[any], accounts_data: collections.defaultdict):
    try:
        if len(posts):
            # add user of posts into accounts data
            for post in posts:
                if not post.account.bot:
                    formatted_post = format_post_data(post)

                    if post.account['id'] not in accounts_data:
                        accounts_data[post.account['id']] = format_account_data(post.account)
                    
                    existing_post_id_list = [post['id'] for post in accounts_data[post.account['id']]['posts']]
                    if formatted_post['id'] not in existing_post_id_list:
                        accounts_data[post.account['id']]['posts'].append(formatted_post)

                    for account in post['mentions']:
                        account = server.account(account['id'])
                        if account['id'] not in accounts_data and not account.bot:
                            accounts_data[account['id']] = format_account_data(account)
        
        return accounts_data
    except Exception as e:
        print(f"An exception occurred: {e}")
        print(traceback.format_exc())

def fill_follower_following_list(server: Mastodon, accounts: collections.defaultdict):
    try:
        account_id_list = set(accounts.keys())
        
        for index, id in enumerate(accounts):
            previous_page = server.account_followers(id = id)
            followers = get_remaining_paginated_data(server, previous_page, limit=config.DATA_LIMIT)

            if len(followers):
                page_data_id_list = set(follower.id for follower in followers)

                existing_followers_in_accounts = account_id_list.intersection(page_data_id_list)

                for follower in existing_followers_in_accounts:
                        accounts[id]['followers'].add(follower)
                        accounts[follower]['followings'].add(id)

            if index%50 == 0 or index == len(accounts)-1:
                print(f"\tDone finding {index}th user - {accounts[id]['username']}'s relations...")
                
        for id in accounts:
            accounts[id]['followers'] = list(accounts[id]['followers'])
            accounts[id]['followings'] = list(accounts[id]['followings'])

        return accounts
    
    except Exception as e:
        print(f"An exception occurred: {e}")
        print(traceback.format_exc())

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
        print(traceback.format_exc())

def format_account_data(account: dict):
    # TODO: Include 10 most hashtag relevant posts in accounts details
    # TODO: reboosted post
    # TODO: add fields parameter in account
    # TODO: featured Hashtags

    try:
        formatted_account = {}

        formatted_account['id'] = account.id
        formatted_account['username'] = account.username
        formatted_account['url'] = account.url
        formatted_account['note'] = parse_text(account.note)
        formatted_account['posts'] = []
        formatted_account['followers'] = set()
        formatted_account['followings'] = set()
        formatted_account['display_name'] = account.display_name
        formatted_account['followers_count'] = account.followers_count
        formatted_account['following_count'] = account.following_count
        formatted_account['statuses_count'] = account.statuses_count
        formatted_account['created_at'] = account.created_at.strftime('%Y-%m-%d %H:%M:%S') if account.created_at else account.created_at
        formatted_account['last_status_at'] = account.last_status_at.strftime('%Y-%m-%d %H:%M:%S') if account.last_status_at else account.last_status_at
        formatted_account['acct'] = account.acct
        formatted_account['bot'] = account.bot
        formatted_account['group'] = account.group
        formatted_account['ai_sentiment'] = [0,1,0]

        return formatted_account
    
    except Exception as e:
        print(f"An exception occurred: {e}")
        print(traceback.format_exc())

def format_post_data(post):
    try:
        formatted_post = {}
        
        formatted_post['id'] = post.id
        formatted_post['url'] = post.url
        formatted_post['content'] = parse_text(post.content)
        formatted_post['attach_media_text'] = get_card_text(post.card)
        formatted_post['tags'] = [tag['name'] for tag in post.tags] if len(post.tags) else []
        formatted_post['mentions'] = [account.id for account in post.mentions]
        formatted_post['language'] = post.language
        formatted_post['in_reply_to_id'] = post.in_reply_to_id
        formatted_post['in_reply_to_account_id'] = post.in_reply_to_account_id
        formatted_post['replies_count'] = post.replies_count
        formatted_post['reblogs_count'] = post.reblogs_count
        formatted_post['favourites_count'] = post.favourites_count

        return formatted_post
    except Exception as e:
        print(f"An exception occurred: {e}")
        print(traceback.format_exc())

def get_card_text(card):
    try:
        if card:
            title = card['title'].strip()
            description = card['description'].strip()
            return f"{title + '.' if title else title } {description}"
        return ''
    except Exception as e:
        print(f"An exception occurred: {e}")
        print(traceback.format_exc())

def parse_text(text: str):
    # Parse the HTML content
    text = text.strip()
    translator = Translator()
    target_language = "en"
    formatted_text = ''

    if text:
        try:
            soup = BeautifulSoup(text, 'html.parser')
            
            # Remove HTML tags but keep text
            formatted_text = soup.get_text()

            # Detect the language and convert text to English if not in English
            #TODO: Find good translator and handle corner cases for error handling
            try:
                detected_lang = detect(formatted_text)
                if detected_lang != target_language:
                    try:
                        formatted_text = translator.translate(formatted_text, dest=target_language).text
                    except Exception as e:
                        pass
            except Exception as e:
                pass

            # Use regular expression to remove hashtags (words starting with '#')
            formatted_text = re.sub(r'#\w+', '', formatted_text)
            # Use regular expression to remove URLs starting with 'https://' or 'http://'
            formatted_text = re.sub(r'https?://\S+', '', formatted_text)
            # Remove newline character
            formatted_text = formatted_text.replace('\n', ' ')
            # remove blank line at start and end of line
            formatted_text = formatted_text.strip()

            return formatted_text
        
        except Exception as e:
            print(f"Error occured {e}")
            print(traceback.format_exc())
            return formatted_text
        
    return ''
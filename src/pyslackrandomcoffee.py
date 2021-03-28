#!/usr/bin/env python

import os
import random
import logging
import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Setup - this function requires the SLACK_API_TOKEN environmental variable to run.
client = WebClient(token=os.environ["SLACK_API_TOKEN"])
CHANNEL         = '#randomcoffees'
CHANNEL_TESTING = '#bot_testing'
LOOKBACK_DAYS   = 28
MAGICAL_TEXT    = 'This weeks random coffees are'


def get_channel_id(channel):
    '''Convert a human readable channel name into a slack channel ID that can be used in the API.

    Args:
        channel: Human readable channel name, such as #randomcoffees

    Returns:
        channel_id: Slack ID for the channel, such as CE2G4C9L2
    '''

    try:
        # Get the channel ID of the channel
        channel_list = client.conversations_list(limit=1000)["channels"]
        for c in channel_list:
            if c.get('name') == channel.strip('#'):
                channel_id = c['id']

        return channel_id

    except SlackApiError as e:
        logging.debug(f"Error getting list of members in {channel}: {e}")
        return None


def get_previous_pairs(channel, testing, lookback_days=LOOKBACK_DAYS):
    '''
    Trawl through the messages in the channel and find those that contain magical text and extract the pairs from these
    messages.

    Args:
        channel (str): Human readable channel name, such as #randomcoffees
        testing (bool): A flag to use either @user1 or <@UABCDEFG1> syntax
        lookback_days (int): How man days back should the function look for previous messages

    Returns:
        previous_pairs (list of of list of tuples):
            [
                [('<@UABCDEFG1>', '<@UABCDEFG2>'), ('<@UABCDEFG5>', '<@UABCDEFG7>')],
                [('<@UABCDEFG3>', '<@UABCDEFG4>'), ('<@UABCDEFG6>', '<@UABCDEFG8>')]
            ]

    Note:
        The formatting of the names depends if in the job is in testing mode or not. The text @user1 will not generate
        notify the user1, but it will look like the correct link (but not blue). <@UABCDEFG1> on the other hand will
        notify the link and be a blue link that looks like @user1 in slack.
    '''

    try:
        # Setup params for client.conversations_history(). slack accepts time in seconds since epoch
        params = {
            'channel': get_channel_id(channel),  # Get channel id
            'limit': 200,  # Pagination - 200 messages per API call
            'oldest': (datetime.datetime.today() - datetime.timedelta(days=lookback_days)).timestamp(),
            'newest': datetime.datetime.now().timestamp()
        }

        # The results paginated, so loop until we get the them all. https://api.slack.com/methods/conversations.history
        conversation_history = []
        has_more = True
        next_cursor = None
        while has_more:
            response = client.conversations_history(**params, cursor=next_cursor)
            conversation_history += response["messages"]
            has_more = response['has_more']
            if has_more:
                next_cursor = response['response_metadata']['next_cursor']

    except SlackApiError as e:
        logging.debug(f"Error getting list of members in {channel}: {e}")

    # We are only interested in text that contain the MAGICAL_TEXT text and '<@U' (in prod) or '@' in testing.
    # TODO: only extract messages sent by the BOT, so we do not process messages from users using the same MAGICAL_TEXT
    if testing:
        texts = [t['text'] for t in conversation_history if MAGICAL_TEXT in t['text'] and '@' in t['text']]
    else:
        texts = [t['text'] for t in conversation_history if MAGICAL_TEXT in t['text'] and '<@U' in t['text']]

    if len(texts):
        # Each message text is a broken into a list by the newline character and the first and last line are disregarded
        # as they are not pairs. Then each pair is cleaned and the username is extracted the result is a list of list of
        # tupples. Example:
        # [
        #     [('<@UABCDEFG1>', '<@UABCDEFG2>'), ('<@UABCDEFG5>', '<@UABCDEFG7>')],
        #     [('<@UABCDEFG3>', '<@UABCDEFG4>'), ('<@UABCDEFG6>', '<@UABCDEFG8>')]
        # ]
        previous_pairs = [
            [
                (
                    e.split('. ')[1].split('and')[0].strip(),
                    e.split('. ')[1].split('and')[1].strip()
                ) for e in t.split('\n')[1:-1]
            ] for t in texts
        ]
    else:
        previous_pairs = None

    return previous_pairs


def post_to_slack_channel_message(message, channel):
    '''Send a message to a given slack channel.

    Args:
        message (str): Message to send
        channel (str): Name of the receiving channel (ex. #data-science-alert) or the unique user id for sending private
            messages

    Returns:
        bool: True of message was a send with success. False otherwise.
    '''

    try:
        if isinstance(message, list):
            # The user would like to send a block
            response = client.chat_postMessage(channel=channel, blocks=message)
        else:
            response = client.chat_postMessage(channel=channel, text=message)
    except SlackApiError as e:
        # From v2.x of the slack library failed responses are raised as errors. Here we catch the exception and
        # downgrade the alert
        print(e)
        return False
    else:
        # Capture soft problems
        if not response['ok']:
            print(response)
            return False
        else:
            return True


def get_members_list(channel, testing):
    '''Get the list of members of a channel.

    Args:
        channel (str): Name of the channel with #. i.e. "#randomcoffees".
        testing (bool): If True inactive usernames are written that does not notify the users, but if False active
            username links are used and the users are pinged when the message is posted

    Returns:
        members: Returns a list of users.
            If testing is True:  ['@user1', '@user2', '@user3', '@user4']
            If testing is False: ['<@UABCDEFG1>', '<@UABCDEFG2>', '<@UABCDEFG3>', '<@UABCDEFG4>']

    Note:
        The formatting of the names depends if in the job is in testing mode or not. The text @user1 will not generate
        notify the user1, but it will look like the correct link (but not blue). <@UABCDEFG1> on the other hand will
        notify the link and be a blue link that looks like @user1 in slack.
    '''

    try:
        # Get the member ids from the channel
        channel_id = get_channel_id(channel)
        member_ids = client.conversations_members(channel=channel_id)['members']

        # Get the mapping between member ids and names
        users_list = client.users_list()['members']

        # Return a list of members as should be written in slack. The @name syntax is not active and will not
        # contact the users in the slack channel, so perfect for testing.
        if testing:
            members = [f'@{u["name"]}' for u in users_list if u['id'] in member_ids and not u['is_bot']]
        else:
            members = [f'<@{u["id"]}>' for u in users_list if u['id'] in member_ids and not u['is_bot']]

        return members

    except SlackApiError as e:
        logging.error(f"Error getting list of members in {channel}: {e}")
        return None


def generate_pairs(members, previous_pairs=None):
    '''
    Shuffles the members list around and pairs them. If ther is uneven number of members one member will be matched
    twice. If there are no members (empty list) it will return an empty list. If the previous_pairs are present they
    will be used to avoid matching members up with previous matches. This is not also possible if there are few members.

    Args:
        members (list of strings): i.e. ['<@UABCDEFG1>', '<@UABCDEFG2>', '<@UABCDEFG3>', '<@UABCDEFG4>']
        previous_pairs (list of list of tuples):
            [
                [('<@UABCDEFG1>', '<@UABCDEFG2>'), ('<@UABCDEFG5>', '<@UABCDEFG7>')],
                [('<@UABCDEFG3>', '<@UABCDEFG4>'), ('<@UABCDEFG6>', '<@UABCDEFG8>')]
            ]

    Returns:
        pairs (list of tupples): i.e. [('<@UABCDEFG1>', '<@UABCDEFG2>'), ('<@UABCDEFG3>', '<@UABCDEFG4>')]

    Note:
        The formatting of the names depends if in the job is in testing mode or not. The text @user1 will not generate
        notify the user1, but it will look like the correct link (but not blue). <@UABCDEFG1> on the other hand will
        notify the link and be a blue link that looks like @user1 in slack.
    '''

    # Shuffle the channel members around
    random.shuffle(members)

    # For each memeber find previous matches. TODO: This is nasty, but premature optimization is the root of all evil.
    # The stored format is a list of lists of tuples with previous matches:
    #     [[...], [('@tk', '@abl'), ('@sh', '@lbr'), ('@tk', '@tj')], [...], ...]
    # This code turns that into a dict structure with unique matches
    #     members_previous_matches = {@cjb: [@tj,...]}
    members_previous_matches = {}
    if members and previous_pairs:
        for member in members:
            matches = []
            for pair_set in previous_pairs:
                for p1, p2 in pair_set:
                    if p1 == member or p2 == member:
                        if p1 == member:
                            matches.append(p2)
                        elif p2 == member:
                            matches.append(p1)
            members_previous_matches[member] = list(set(matches))

    def pair_excluding_historic_matches(member1, members, members_previous_matches):
        '''Walkthrough the members list and try to find matches that has not been done before.

        Args:
            member1 (str): '<@UABCDEFG1>' or '@user1'
            members (list): The list of members.
            members_previous_matches (dict):
                {
                    '<@UABCDEFG8>': ['<@UABCDEFG1>', '<@UABCDEFG2>', '<@UABCDEFG3>'],
                    '<@UABCDEFG7>': ['<@UABCDEFG1>', '<@UABCDEFG4>'],
                }

        Returns
            pair (tuple): The input member1 and the matched member2
            memebers (list): The members list, but with member2 removed
        '''
        if members_previous_matches:
            member2_candidates = [member for member in members if member not in members_previous_matches[member1]]

            try:
                member2 = random.sample(member2_candidates, 1)[0]
            except ValueError:
                # There is no untaken matches left, so just pick a random from members
                member2 = random.sample(members, 1)[0]
        else:
            member2 = random.sample(members, 1)[0]

        members.remove(member2)
        pair = (member1, member2)

        return pair, members

    # Ensure if there is uneven number of members one member will be matched twice. If there are no members return a
    # empty list
    pairs = []
    if members:
        first_member = members[-1]
        while len(members):
            if len(members) >= 2:
                member1 = members.pop()
                pair, members = pair_excluding_historic_matches(member1, members, members_previous_matches)
            else:
                pair, members = pair_excluding_historic_matches(first_member, members, members_previous_matches)

            pairs.append(pair)

    return pairs


def format_message_from_list_of_pairs(pairs):
    '''
    Takes the list of pairs and formats the output in a slack message that can then be posted to the slack channel.

    Args:
        pairs (list of tupples): i.e. [('<@UABCDEFG1>', '<@UABCDEFG2>'), ('<@UABCDEFG3>', '<@UABCDEFG4>')]

    Returns:
        message (multi-line str): The message
    '''

    if len(pairs):
        m1 = MAGICAL_TEXT + ':\n'
        pair_strings = ''.join([f' {i+1}. {p1} and {p2}\n' for i, (p1, p2) in enumerate(pairs)])
        m2 = f'An uneven number of members results in one person getting two coffee matches. Matches from the last {LOOKBACK_DAYS} days considered to avoid matching the same members several times in the time period.'
        message = m1 + pair_strings + m2
        return message
    else:
        return None


def pyslackrandomcoffee(work_ids=None, testing=False):
    '''Pairs the members of a slack channel up randomly and post it back to the channel in a message.

    Args:
        work_ids (list): Unused STAU required argument
        testing (bool): Flag if the CHANNEL_TESTING should be used.

    Note:
        This script does utilize work_ids, but STAU requires it, so it is present, but unused.
    '''

    if testing is False:
        channel = CHANNEL
    else:
        channel = CHANNEL_TESTING

    members        = get_members_list(channel, testing)
    previous_pairs = get_previous_pairs(channel, testing)
    pairs          = generate_pairs(members, previous_pairs)
    message        = format_message_from_list_of_pairs(pairs)

    if message:
        post_to_slack_channel_message(message, channel)


if __name__ == '__main__':
    pyslackrandomcoffee(testing=True)

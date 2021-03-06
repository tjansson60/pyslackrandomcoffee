#!/usr/bin/env python

import os
import random
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Setup - this function requires the SLACK_API_TOKEN environmental variable to run.
client = WebClient(token=os.environ["SLACK_API_TOKEN"])
CHANNEL         = '#randomcoffees'
CHANNEL_TESTING = '#bot_testing'


def post_to_slack_channel_message(message, channel):
    '''Send a message to a given slack channel.

    Args:
        message (str): Message to send
        channel (str): Name of the receiving channel (ex. #data-science-alert) or the unique user id for sending private messages

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
            print(response)  # Use print since LOG isn't an option
            return False
        else:
            return True


def get_members_list(channel, testing=False):
    '''
    Get the list of members of a channel.

    Args:
        channel (str): Name of the channel with #. i.e. "#randomcoffees".
        testing (bool): If True inactive usernames are written that does not ping the users, but if False active
            username links are used and the users are pinged when the message is posted

    Returns:
        members: Returns a list of users.
            If testing is True:  ['@user1', '@user2', '@user3', '@user4']
            If testing is False: ['<@UABCDEFG1>', '<@UABCDEFG2>', '<@UABCDEFG3>', '<@UABCDEFG4>']
    '''

    try:
        # Get the channel ID of the channel
        channel_list = client.conversations_list(limit=1000)["channels"]
        for c in channel_list:
            if c.get('name') == CHANNEL.strip('#'):
                channel_id = c['id']

        # Get the member ids from the channel
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
        logging.error(f"Error getting list of members in {CHANNEL}: {e}")


def generate_pairs_from_memberlist(members):
    '''
    Shuffles the members list around and pairs them. If ther is uneven number of members one member will be matched
    twice. If there are no members (empty list) it will return an empty list.

    Args:
        members (list of strings): i.e. ['<@UABCDEFG1>', '<@UABCDEFG2>', '<@UABCDEFG3>', '<@UABCDEFG4>']

    Returns:
        pairs (list of tupples): i.e. [('<@UABCDEFG1>', '<@UABCDEFG2>'), ('<@UABCDEFG3>', '<@UABCDEFG4>')]
    '''
    # Shuffle the channel members around
    random.shuffle(members)

    # Ensure if there is uneven number of members one member will be matched twice. If there are no members return a
    # empty list
    pairs = []
    if members:
        first_member = members[-1]
        while len(members):
            if len(members) >= 2:
                pair = (members.pop(), members.pop())
            else:
                pair = (first_member, members.pop())
            pairs.append(pair)

    return pairs


def format_message_from_list_of_pairs(pairs):
    '''
    Takes the list of pairs and formats the output in a slack message that can then be posted to the slack channel.

    Args:
        pairs (list of tupples): i.e. [('<@UABCDEFG1>', '<@UABCDEFG2>'), ('<@UABCDEFG3>', '<@UABCDEFG4>')]

    Returns:
        message (multiline str): The message

    '''
    if len(pairs):
        m1 = 'This weeks random coffees are:\n'
        pair_strings = ''.join([f' {i+1}. {p1} and {p2}\n' for i, (p1, p2) in enumerate(pairs)])
        m2 = 'If there are an uneven number of members one person will have two conversations'
        message = m1 + pair_strings + m2
        return message
    else:
        return None


def pyslackrandomcoffee(testing=False):
    members = get_members_list(CHANNEL, testing=testing)
    pairs = generate_pairs_from_memberlist(members)
    message = format_message_from_list_of_pairs(pairs)

    if message:
        if testing is False:
            post_to_slack_channel_message(message, CHANNEL)
        else:
            post_to_slack_channel_message(message, CHANNEL_TESTING)


if __name__ == '__main__':
    pyslackrandomcoffee(testing=True)

#!/usr/bin/env python

import src.pyslackrandomcoffee
from collections import Counter


def test_generate_pairs():

    def helper(members, number_of_pairs, expected_max_occurrences, previous_pairs):

        pairs = src.pyslackrandomcoffee.generate_pairs(members.copy(), previous_pairs)
        unpacked_members = [name for pair in pairs for name in pair]

        # Ensure all member names are used in the pairs
        assert set(unpacked_members) == set(members)

        # Ensure that we get the correct number of pairs
        assert len(pairs) == number_of_pairs

        # Count the occurrences of names in the unpacked_members list
        if expected_max_occurrences:
            counter = Counter(unpacked_members)
            max_occurrences = max(list(counter.values()))
            assert max_occurrences == expected_max_occurrences

    # Uneven number of members
    helper(['Liam', 'Olivia', 'Noah', 'Emma', 'Ava'], 3, 2, None)

    # Even number of members
    helper(['Liam', 'Olivia', 'Noah', 'Emma', 'Ava', 'Sophia'], 3, 1, None)

    # A single member pair with one-self
    helper(['Liam'], 1, 2, None)

    # No members found
    helper([], 0, 0, None)

    # Even with previous matches
    helper(['Liam', 'Olivia', 'Noah', 'Emma', 'Ava', 'Sophia'], 3, 1, [[('Olivia', 'Noah'), ('Olivia', 'Ava')]])

    # Uneven With previous matches
    helper(['Liam', 'Olivia', 'Emma', 'Ava', 'Sophia'], 3, 2, [[('Olivia', 'Noah'), ('Olivia', 'Ava')]])

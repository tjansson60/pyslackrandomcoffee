# pyslackrandomcoffee

A very simple random coffee bot for slack that takes all the members in a channel and randomly matches them up for a
coffee date and writes the matches in back in the same channel. Could be called weekly or daily from a scheduler or
manually.

The current implementation is very simple and has no memory of past matches, but that could easily be added by parsing
i.e. the last 4 previous posts to the same channel.

The slack app http://www.randomcoffees.com/ does the exact same thing, so this is much easier to use, but when it had an
outage earlier this week I chose to implement it myself in python to get the random coffees going again.  


## Setup
Get a Miniconda base install from https://docs.conda.io/en/latest/miniconda.html first then setup the environment using:
```bash
conda env create -n pyslackrandomcoffee -f pyslackrandomcoffee.yml
conda activate pyslackrandomcoffee
```
Make sure you have a valid slack API token in the environment called: `SLACK_API_TOKEN`

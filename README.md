# pyslackrandomcoffee

A very simple random coffee bot for slack that takes all the members in a channel and randomly matches them up for a
coffee date and writes the matches in back in the same channel. Could be called weekly or daily from a scheduler or
manually. The bot will look back in the history of the channel and find past matches and use these try to generate
matches not seen before. By default it looks back at the last 28 days of channel history.

The slack app http://www.randomcoffees.com/ does the exact same thing, so this is much easier to use, but when it had an
outage earlier this week I chose to implement it myself in python to get the random coffees going again.

## Setup
Get a Miniconda base install from https://docs.conda.io/en/latest/miniconda.html first then setup the environment using:
```bash
conda env create -n pyslackrandomcoffee -f pyslackrandomcoffee.yml
conda activate pyslackrandomcoffee
```
Make sure you have a valid slack API token in the environment called: `SLACK_API_TOKEN` with appropriate scopes such as
`channel:history`, ` channels:read`, `chat:write`, `users:read` etc. 

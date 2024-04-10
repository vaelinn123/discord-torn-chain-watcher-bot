## Introduction
This is meant to be a simple bot for managing and watching chains in torn city. It exposes a couple of commands to this effect:
!rotation-add {username} to add a user that is in the current channel to the rotation.
!rotation-remove {username} to remove a user that is in the channel from the rotation.
!rotation-info To print out the current rotation.
!rotation-clear To clear the current rotation.
!chain-timer To print out information about the factions current chain.
!chain-start This will start a loop where the current rotation and chain information will be printed every 30 seconds.
!chain-stop This will stop the 30 second loop.

## Setup
- Set up bot in discord with Server Message Intent and Message Content Intent enabled.
- Add config.json with BOT_TOKEN and TORN_API_KEY key/values (example below).
- `pip install discord`

## Example config
```
{
    "BOT_TOKEN": "your-discord-bot-token-here",
    "TORN_API_KEY": "your-torn-api-key"
}
```

## TODO
- [ ] Add a !help command
- [ ] Make !chain-start accept a time value.
- [ ] Make !chain-start output an ordered list, updated based on whether the current invocation has a chain timer that is longer than the last, reordering the rotation so that the previous first person is now last.
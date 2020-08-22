#!/bin/bash

CLIENT_ID="$1"
PERMS="317504"
SCOPE="bot"

open "https://discord.com/api/oauth2/authorize?client_id=$CLIENT_ID&scope=$SCOPE&permissions=$PERMS"

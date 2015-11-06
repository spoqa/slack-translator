# Slack Translator [![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy) [![Build Status](https://travis-ci.org/shinvee/slack-translator.svg)](https://travis-ci.org/shinvee/slack-translator)

You can translate your chat using slack translator.

## How to Setup

You need to setup 3 environment variables to integrate Google translator with
[Slack][1].

1. **Google API Key:** You can get the API Key from [Google Developers Console](https://console.developers.google.com/)
2. **SLACK_API_TOKEN:** You can get the API Token from [Slack Web API](https://api.slack.com/web)
3. **SLACK_WEBHOOK_URL:** You can get the Outgoing Webhook URL from [here](https://slack.com/services/new/outgoing-webhook)

Then you can add [Slash Commands](https://api.slack.com/slash-commands) to use
translator.

1. **Commands:** `/[target language]`
2. **URL**: `https://[host]/[source language]/[target language]`
3. **Method**: `POST`

For example, if you are using Korean, and you want to add Korean->Japanese
translation command, try to add Slash command like this.

1. **Commands:** `/ja`
2. **URL**: `https://[host]/ko/ja`
3. **Method**: `POST`

  [1]: https://www.slack.com/

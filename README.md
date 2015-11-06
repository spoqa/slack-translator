# Slack Translator [![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy) [![Build Status](https://travis-ci.org/spoqa/slack-translator.svg)](https://travis-ci.org/spoqa/slack-translator)

You can translate your chat using slack translator.

<img width="459" alt="2015-11-07 12 19 14" src="https://cloud.githubusercontent.com/assets/276766/11000456/3e07dad4-84e5-11e5-9b51-f777340e4909.png">


## How to Setup

You need to setup 3 [environment variables][2] to integrate
[Google translate API][3] with [Slack][1].

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
  [2]: https://en.wikipedia.org/wiki/Environment_variable
  [3]: https://cloud.google.com/translate/docs

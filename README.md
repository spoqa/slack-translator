# Slack Translator
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy) [![Build Status](https://travis-ci.org/spoqa/slack-translator.svg)](https://travis-ci.org/spoqa/slack-translator) [![Coverage Status](https://coveralls.io/repos/spoqa/slack-translator/badge.svg?service=github)](https://coveralls.io/github/spoqa/slack-translator)

You can translate your chat using slack translator.

<img width="459" alt="2015-11-07 12 19 14" src="https://cloud.githubusercontent.com/assets/276766/11000456/3e07dad4-84e5-11e5-9b51-f777340e4909.png">


## How to Setup

You need to setup the following [environment variables][2] to integrate
with [Slack][1]:

- `SLACK_API_TOKEN`: You can get the API Token from [Slack Web API](https://api.slack.com/web)
- `SLACK_WEBHOOK_URL`: You can get the Incoming Webhook URL from [here](https://services/new/incoming-webhook)

Also, you need to choose a translator vendor to use:

- `TRANSLATE_ENGINE`: The handle name of the translator vendor.  Currently only support `google` and `naver`.  `google` by default.

If you choose `google` as your `TRANSLATE_ENGINE`, you need to one more
environment variable for [Google Translate API][3] as well:

- `GOOGLE_API_KEY`: You can get the API Key from [Google Developers Console](https://console.developers.google.com/)

Note that you don't need any additional environment variables when you
choose `naver` as your `TRANSLATE_ENGINE`.

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

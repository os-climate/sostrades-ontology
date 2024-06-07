'''
Copyright 2022 Airbus SAS
Modifications on 2024/05/16 Copyright 2024 Capgemini

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import requests


def sendGChatNotification(webhook_url=None, textMessage=None, cards=None):
    """Hangouts Chat incoming webhook quickstart."""
    if webhook_url is not None and webhook_url != '':
        if textMessage is not None and textMessage != '':
            bot_message = {
                'text': textMessage}
        elif cards is not None and cards != '':
            bot_message = {
                'cards': cards}
        else:
            raise Exception("Nothing to send")

        response = requests.request(
            method='POST',
            url=webhook_url,
            json=bot_message,
            verify=False)

        print(response.status_code)

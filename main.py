#!/usr/bin/python3

import datetime
import json
import requests
import time

config = {}

with open("config.json", "r") as jsonfile:
    config = json.load(jsonfile)

bot_token = config["token"]
telegram_channel = config["channel_id"]
scoreboard_link = config["scoreboard_link"]
participants = config["participants"]
problems = config["problems"]
data_file = ".data.json"
start_time = datetime.datetime.fromtimestamp(config["start_timestamp"])

session = requests.session()
subscores = dict()


def send_to_channel(message):
    uri = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + telegram_channel + '&text=' + message
    result = session.request('GET', uri)
    time.sleep(0.25)
    if result.status_code != 200:
        if result.status_code == 429:
            time.sleep(result.json()["parameters"]["retry_after"] + 1)
            send_to_channel(message)
            return
        print(result.status_code)
        print(result.text)
        print(uri)
        exit(0)


def download(url):
    result = session.request('GET', url)
    if result.status_code != 200:
        print(url, result.status_code)
    return json.loads(result.text)


def print_submission(submission):
    def get_time(t):
        return str(datetime.datetime.fromtimestamp(t) - start_time).split('.')[0]

    part = submission["participant"]
    if part not in subscores:
        subscores[part] = dict()
    problem = submission["task"]
    score = submission['score']
    old_total = 0
    if problem not in subscores[part]:
        subscores[part][problem] = list(map(float, submission['extra']))
    else:
        old_total = sum(subscores[part][problem])
        for i in range(len(submission['extra'])):
            subscores[part][problem][i] = max(subscores[part][problem][i], float(submission['extra'][i]))
    total = sum(subscores[part][problem])
    message = "[{}] {} відправив(ла) {} на {:.2f} балів (сума: {:.2f} -> {:.2f})".format(get_time(submission['time']), participants[part], problems[problem], score, old_total, total)
    if old_total != total:
        message = "!!!!!!!!!!" + message
    print(message)
    send_to_channel(message)


while True:
    print('Updating')

    try:
        data = json.load(open(data_file))
    except FileNotFoundError:
        data = []

    for i in participants.keys():
        try:
            part_data = download(scoreboard_link + 'sublist/' + i)
            time.sleep(0.5)
            part_data.sort(key=lambda x: x["time"])
            for submit in part_data:
                submit["participant"] = i
                if submit not in data:
                    print_submission(submit)
                data.append(submit)
        except:
            print('ERROR')
            pass

    open(data_file, 'w').write(json.dumps(data))
    time.sleep(10)

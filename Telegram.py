import tomli
from time import sleep
import random
import re
import sans
import threading
from datetime import datetime

#Load TOML file
with open("config.toml","rb") as config:
    info = tomli.load(config)
ua = "{} using Simple Telegrammer Beta".format(info["user_agent"])

#Find out how many campaigns we're running
n = len(info["templates"])
print("{} Campaigns To Be Run".format(n))

nations_queue = []

def sse_listener():
    """
    Function which uses sans to listen to the happenings for new nations.
    To be run in a thread
    """
    sans.set_agent(ua)
    global nations_queue
    while True:
        try:
            now = datetime.now().strftime("%H:%M:%S")
            print("THREAD START: SSE THREAD [{}]".format(now))
            for event in sans.serversent_events(sans.Client(),"founding"):
                event_text = event["str"]
                nname = re.search(r"@@(.*)@@",event_text).group(1)
                matchness = 0
                for comp_name in nations_queue:
                    i = 0
                    for (cha, chb) in zip(nname,comp_name):
                        if cha != chb:
                            break
                        else:
                            i += 1
                    if i/len(nname) > matchness:
                        matchness = i/len(nname)
                if matchness < 0.6:
                    nations_queue.append(nname)
                    print("NATION FOUND: {}".format(nname))
                else:
                    print("NATION REJECTED: {} is {} similar to existing nation".format(nname,matchness))
                if len(nations_queue) > 40:
                    nations_queue.pop(0)
        except Exception as e:
            print("EXCEPTION in the SSE Thread")
            print(e)
            sleep(180)

#Start the SSE thread
threading.Thread(target=sse_listener,daemon=True).start()

#Telegramming Loop
while True:
    pick = random.randint(0,(n-1))
    if len(nations_queue) == 0:
        print("TELEGRAM: No Nations To Telegram. Waiting 30s")
        sleep(30)
    else:
        for i in range(len(nations_queue)):
            candidate = nations_queue.pop()
            now = datetime.now().strftime("%H:%M:%S")
            print("REQUEST: Trying {} with campaign {} [{}]".format(candidate,pick,now))
            try:
                response = sans.get(sans.Nation(candidate,"tgcanrecruit"))
                if response.xml.find("TGCANRECRUIT").text == "1":
                    break
                else:
                    print("TELEGRAM: {} cannot receive recruitment".format(candidate))
            except Exception as e:
                print("EXCEPTION: Trying a different nation due to error")
                print(e)
        now = datetime.now().strftime("%H:%M:%S")
        print("REQUEST: Sending Telegram [{}]".format(now))
        try:
            response = sans.get(sans.Telegram(client=info["client_key"], tgid=info["templates"][pick], key=info["secret_keys"][pick], to=candidate))
            print(response)
        except Exception as e:
            print("EXCEPTION in Telegrams Thread")
            print(e)
        sleep(180.1)
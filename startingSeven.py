"""
DONE: --------
Parse decklist txt file
Fetch images into directory with Scryfall API
Insert actual decklist into text file

TO DO: --------
Concatenate images horizontally with Pillow
Generate starting 7 with decklist
Post to facebook with page token
Implement Schedule loop (copy from piBot)

"""

print("hello world! (bot program starts)")

decks = [
            ["./decklists/pBurn.txt", "Burn in Pauper"], 
            ["./decklists/tron.txt", "G Tron in Modern"],
            ["./decklists/fish.txt", "Fish in Legacy"],
            ["./decklists/stoneblade.txt", "Stoneblade in Modern"],
            ["./decklists/storm.txt", "Botmin's Modern Storm"],
            ["./decklists/riverfall.txt", "Ouzel Ocean's Riverfall Modern"],
            ["./decklists/bgFood.txt", "Golgari Food (with Lurrus) in Historic"],
            ["./decklists/sligh.txt", "Paul's Sligh deck"],
            ["./decklists/elves.txt", "Chris Scull's Pauper Elves"]
        ]


from fileinput import filename
from inspect import getcallargs
from stat import filemode
import requests
import random
import facebook
import schedule
import time
import shutil
import os
cwd = os.getcwd()
shutil.rmtree('deckImages', ignore_errors=True)
os.makedirs(format(cwd) + '/deckImages', exist_ok = True)
import itertools
import io
import json
from PIL import Image

"""
# Sulfur Falls example..
response = requests.get("https://api.scryfall.com/cards/znr/80")
#print(response.json())
#print(response.json()[image_uris][small])
#parsed = json.loads(response.json())

# Print JSON in pretty format (.dumps() operates on dict, which is right)
print(json.dumps(response.json(), indent=4, sort_keys=True))

image_url = response.json()["image_uris"]["small"]
fileName = "Sulfur Falls" + ".png"
imgReq = requests.get(image_url, stream = True)
if imgReq.status_code == 200: # if the request was successful
    imgReq.raw.decode_content = True # make sure we can write the file
    with open(fileName,'wb') as f:
        shutil.copyfileobj(imgReq.raw, f)
else:
    print("Error retrieving image.")
"""

# Helper function used in decToFormat. Takes a strict name, searches scryfall API, gets the set/collector number of the first result.
def setNumberFromName(name):
    # name = title.replace(' ', '%')
    response = requests.get('https://api.scryfall.com/cards/search?q=!"' + name + '"')
    #print(json.dumps(response.json(), indent=4, sort_keys=True))
    set = response.json()['data'][0]['set']
    cn = response.json()['data'][0]['collector_number']
    time.sleep(0.1)
    return [set, cn]

# Converts a MTGO .dec style list to the format we use to get Scryfall deck images. Has strict format rules.
def decToFormat(decfile):
    decklist = []
    with io.open("./deckdrafts/" + decfile, mode="r", encoding="utf-8") as f:
        deckraw = f.readlines()
        for card in deckraw:
            if card != "\n":
                for x in range(int(card.split()[0])):
                    decklist.append(setNumberFromName(card[2:]))
    with open("./decklists/" + decfile, 'w') as filehandle:
        filehandle.writelines("%s %s\n" % (card[0], card[1]) for card in decklist)
    return decklist
    

# Without converting, get card picture from name directly. Deprecated.
def getCardIconFromName(title): # deprecated
    name = title.replace(" ", "%")
    response = requests.get("https://api.scryfall.com/cards/search?q=" + name)
    try: 
        image_url = response.json()['data'][0]["image_uris"]["normal"]
    except: # except double face cards
        image_url = response.json()['data'][0]["card_faces"][0]["image_uris"]["normal"]
    fileName = name + ".png"
    imgReq = requests.get(image_url, stream = True)
    if imgReq.status_code == 200: # if the request was successful
        imgReq.raw.decode_content = True # make sure we can write the file
        with open(fileName,'wb') as f:
            shutil.copyfileobj(imgReq.raw, f)
    else:
        print("Error retrieving image.")

    # shutil is fucking amazing
    shutil.move(name + ".png", "deckImages/" + name + ".png")
    time.sleep(0.05)
    quit()

def getCardIcon(set,code):
    response = requests.get("https://api.scryfall.com/cards/"+set+"/"+code)
    try: 
        image_url = response.json()["image_uris"]["normal"]
    except: # except double face cards
        image_url = response.json()["card_faces"][0]["image_uris"]["normal"]
    fileName = set + code + ".png"
    imgReq = requests.get(image_url, stream = True)
    if imgReq.status_code == 200: # if the request was successful
        imgReq.raw.decode_content = True # make sure we can write the file
        with open(fileName,'wb') as f:
            shutil.copyfileobj(imgReq.raw, f)
    else:
        print("Error retrieving image.")
    
    # shutil is fucking amazing
    shutil.move(set + code + ".png", "deckImages/" + set + code + ".png")
    time.sleep(0.05)

def parse(fileName):
    decklist = []
    #with open(fileName, 'r') as f:
    with io.open(fileName, mode="r", encoding="utf-8") as f:
        deckraw = f.readlines()
        for card in deckraw:
            if card != "\n":
                decklist.append(card.split())
    # print(decklist)
    return decklist

def getDeckIcons(fileName):
    decklist = set(tuple(x) for x in parse(fileName))
    for card in list(decklist):
        try: 
            getCardIcon(card[0],card[1])
        except:
            print(card[0],card[1]) 

# Save decklist as list of strings. [#0..#59] and draw a random 7
def drawHand(fileName):
    decklist = parse(fileName)
    handSeed = random.sample(range(0,len(decklist)-1), 7) # enables greater than 60 cards
    hand = []
    start = "You are on the "
    if handSeed[0] % 2: # deprecated. We flip the turn coin later on.
        start += "play."
    else:
        start += "draw."
    for c in handSeed:
        hand.append(decklist[c])
    print(start)
    print(hand)
    return hand

def handToImage(hand):
    for card in hand:
        # later: check if the file exists.
        try: 
            getCardIcon(card[0],card[1])
        except:
            print(card[0],card[1])

    imgList = list(Image.open("deckImages/"+card[0]+card[1]+".png") for card in hand)
    result = Image.new('RGB', (imgList[0].width*4, imgList[0].height*2))
    for x in range(7):
        if x < 4:
            result.paste(imgList[x],(x*imgList[0].width, 0))
        else:
            result.paste(imgList[x],((x-4)*imgList[0].width + (imgList[0].width)//2, imgList[0].height))
    result.save('Test.png')
    return result

def postToFacebook(token, message):
	graph = facebook.GraphAPI(token)
	post_id = graph.put_photo(image = open('Test.png', 'rb'), message = message)["post_id"]
	print(f"Successfully posted {post_id} to Facebook page")



def job():
    pickedDeck = random.randint(0,len(decks)-1)
    handToImage(drawHand(decks[pickedDeck][0]))
    token = " some facebook token "
    role = random.randint(0,1)
    if role == 0:
        roleword = "play."
    else:
        roleword = "draw."
    deckname = decks[pickedDeck][1] 
    message = "The deck is " + deckname + ". You are on the " + roleword
    postToFacebook(token, message)
    

def firstJob(arg): # same as Job but not random seed
    handToImage(drawHand(decks[arg][0]))
    token = "EAACVS6jUj0QBAC0qmIbBUFEYyJP1Jdwwq6Q41S8G6h9x2aJUyAgPQiAWdsRuzQ8NlVs1Mt5nVgXxnvZChJgMZAnZAQqBtgRTS3HH4E2xsS527AtZCAO4E9CjkB1cuybbAlZAPDjyMaTOM4B3K7N1CADB0f5k7vNpMi3PAtAbNqpQeWuUC2Gye"
    role = random.randint(0,1)
    if role == 0:
        roleword = "play."
    else:
        roleword = "draw."
    deckname = decks[arg][1]
    message = "Testing new addition. The deck is " + deckname + ". You are on the " + roleword
    postToFacebook(token, message)


if __name__ == '__main__':
    """
    for deck in decks:
        getDeckIcons(deck[0])
    """
        # REMOVED . CALL SCRYFALL API EACH TIME HAND IS DRAWN
    firstJob(8)
    schedule.every().hour.at(":00").do(job) 
    #schedule.every().hour.at(":30").do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
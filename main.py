import discord
import random
from collections import defaultdict
from pysyllables import get_syllable_count
import pymongo
import os
 
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
client = discord.Client(intents=intents)

# Token
from dotenv import load_dotenv
load_dotenv()

def count_syllables(words):
    num_syllables = 0
    for word in words:
        num_syllables += get_syllable_count(word)
    return num_syllables

def build_chain(words):
    chain = defaultdict(list)
    for i, word in enumerate(words):
        if i == (len(words) - 1):
            chain[word].append(None)
        else:
            chain[word].append(words[i+1])
    return chain

def generate_message(chain):
    message = []
    current_word = random.choice(list(chain.keys()))
    while current_word is not None:
        message.append(current_word)
        current_word = random.choice(chain[current_word])
    return ' '.join(message)

@client.event
async def on_ready():
    print("uClone is ready to clone.")

@client.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return

    # Haiku functionality
    words = message.content.split()

    haiku = {
        "line1": "",
        "line2": "",
        "line3": "",
        "author": client.user
    }

    # Connect to MongoDB server, fix MongoDB
    mongo_client = pymongo.MongoClient(os.getenv("MONGODB_SRV"))
    # Select database and collection
    db = mongo_client.haiku_database
    haiku_collection = db.haikus

    l1_syllables = 0
    l2_syllables = 0
    l3_syllables = 0

    for i, word in enumerate(words):
        if l1_syllables <= 5:
            l1_syllables += count_syllables(word)
            haiku["line1"] += word + " "
        elif l2_syllables <= 7:
            l2_syllables += count_syllables(word)
            haiku["line2"] += word + " "
        elif l3_syllables <= 5:
            l3_syllables += count_syllables(word)
            haiku["line3"] += word + " "

    if l1_syllables == 5 and l2_syllables == 7 and l3_syllables == 5:
        print("This message is a haiku!")
        await message.channel.send('This message is a haiku!')
        # Only store in collection if the message is a haiku
        haiku_collection.insert_one(haiku)

    # Retrieve all haikus from collection
    cursor = haiku_collection.find()
    for haiku in cursor:
        print(haiku["line1"], haiku["line2"], haiku["line3"])

    # Generate text from history 
    # Markov chain from list of words
    if message.content.startswith('!gen'):
        parts = message.content.split()
        user_messages = await client.get_messages(message.channel, limit = 200)
        if len(parts) > 1:
            target_user = parts[1]
            user_messages = [m for m in user_messages if str(m.author) == target_user]
        else:
            user_messages = [m for m in user_messages if m.author == message.author]
        
        text = '\n'.join([m.content for m in user_messages])

        words = text.split()
        chain = build_chain(words)
        generated_message = generate_message(chain)
        await message.channel.send(generated_message)

TOKEN = os.getenv("DISCORD_TOKEN")
client.run("TOKEN")
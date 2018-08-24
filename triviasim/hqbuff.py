'''
MIT License

Copyright (c) 2018, Oliver Bell <freshollie@gmail.com>

HQBuff api interface
'''

import asyncio
import datetime
import json
import random

import aiohttp
from bs4 import BeautifulSoup

# HQBuff started recording quizes here
START_DATE = datetime.datetime(2018, 5, 9)

COUNTRY_UK = "uk"
COUNTRY_US = "us"

_API_ADDR = "https://hqbuff.com/api"

async def get_quiz(date, game_num, country=COUNTRY_US):
    '''
    Fetch a quiz on the given date with the given game number
    from hqbuff

    A list of rounds are returned, containing the questions
    choices and answers
    '''

    url = f"{_API_ADDR}/{country}/{date.strftime('%Y-%m-%d')}"

    print(f"Getting quiz {game_num} from: {url}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response = await response.json()
    
    questions = []

    for game in response:
        if game["game_number"] != game_num:
            continue
        
        for question in game["questions"]:
            choices = []
            answer = ""

            for choice in question["answers"]:
                choices.append(choice["text"])
                if choice["correct"]:
                    answer = choice["text"]

            questions.append({
                "question": question["text"],
                "choices": choices,
                "answer": answer
            })

    return questions


async def try_get_quiz(date, num):
    '''
    Try to get a quiz from HQBuff,
    returning null if HQBuff was not available
    '''
    try:
        return await get_quiz(date, num)
    except:
        print(f"Could not get " + date.strftime('%Y-%m-%d'))
        return None


async def get_random_quiz():
    '''
    Get a random HQTrivia quiz
    from hqbuff
    '''

    quiz = []
    today = datetime.datetime.now()

    diff = (today - START_DATE).days

    # Keep trying to get random quizes until the quiz is not empty
    while not quiz:
        quiz = await try_get_quiz(today + datetime.timedelta(days=-random.randint(0, diff)), num=random.randint(1, 2))

    return quiz


async def make_db():
    '''
    Create a JSON database of ALL
    questions on HQBuff

    Outputted to db.json
    '''
    quiz_db = []

    today = datetime.datetime.now()
    quiz_date = START_DATE
    while quiz_date <= today:
        collectors = [] 
        for i in range(10):
            for j in range(2):
                collectors.append(get_quiz(quiz_date, j + 1))
            quiz_date += datetime.timedelta(days=1)

        for quiz in await asyncio.gather(*collectors):
            if not quiz:
                continue
            quiz_db.append(quiz)
    
    print(f"{sum([len(quiz) for quiz in quiz_db])} questions")

    with open("db.json", "w") as db:
        db.write(json.dumps(quiz_db))


async def test_get_quiz_game():
    questions = await get_random_quiz()
    print(questions)
 
    
if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(test_get_quiz_game())
    #asyncio.get_event_loop().run_until_complete(make_db())

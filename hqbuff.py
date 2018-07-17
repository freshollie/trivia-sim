import datetime
import aiohttp
import asyncio
import json
import random
from bs4 import BeautifulSoup

# HQBuff started recording quizes here
START_DATE = datetime.datetime(2018, 5, 9)

async def get_quiz(date=None, url=None, num=1):
    '''
    Fetch a quiz on the given date with the given game number
    from hqbuff

    A list of rounds are returned, containing the questions
    choices and answers

    Without a date, the latest quiz is fetched.

    A specific URL can be given for a quiz if desired.
    '''

    if url == None:
        url = "https://hqbuff.com/"
        if date:
            url += f"game/{date.strftime('%Y-%m-%d')}/{num}"

    print(f"Getting quiz: {url}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response = await response.text()

    data = BeautifulSoup(response, "html.parser")

    questions = []

    # The questions of the game are broken up into
    # question divs
    for game_round in data.findAll("div", class_="question"):
        
        # We find the question text in this div
        question_element = game_round.find("h3", class_="question__text")
        if not question_element:
            continue

        # And then find the answers in the div too
        question = question_element.text.replace("Savage", "").strip()
        choices_list = game_round.find("ul", class_="questions")
        if not choices_list:
            continue
        
        choices = []
        correct_answer = ""
        for choice_element in choices_list.findAll("li"):
            choice = choice_element.text.replace("Correct", "").strip()

            # The correct answer is highlighted by the correct question class
            if choice_element.get('class', '') == ['questions__correct']:
                correct_answer = choice
            
            choices.append(choice)
        
        questions.append({
            "question": question,
            "choices": choices,
            "answer": correct_answer
        })

    return questions


async def try_get_quiz(date, num):
    '''
    Try to get a quiz from HQBuff,
    returning null if HQBuff was not available
    '''
    try:
        return await get_quiz(date, num=num)
    except:
        print("Could not get " + date)
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
                collectors.append(get_quiz(quiz_date, num=j + 1))
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

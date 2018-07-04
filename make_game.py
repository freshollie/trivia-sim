import requests
import datetime
import aiohttp
import asyncio
import json
from bs4 import BeautifulSoup

START_DATE = datetime.datetime(2018, 5, 9)

async def get_quiz(date=None, url=None, num=1):
    if url == None:
        url = "https://hqbuff.com/"
        if date:
            url += "game/" + date.strftime("%Y-%m-%d") + "/" + str(num)
    print(url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response = await response.text()

    data = BeautifulSoup(response, "html.parser")

    questions = []

    for game_round in data.findAll("div", class_="question"):
        question_element = game_round.find("strong", class_="question__text")
        if not question_element:
            continue
        question = question_element.text.replace("Savage", "").strip()
        choices_list = game_round.find("ul", class_="questions")
        if not choices_list:
            continue
        
        choices = []
        correct_answer = ""
        for choice_element in choices_list.findAll("li"):
            choice = choice_element.text.replace("Correct", "").strip()

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
    try:
        return await get_quiz(date, num=num)
    except:
        print("Could not get " + date)
        return None


async def make_db():
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

    with open("db.txt", "w") as db:
        db.write(json.dumps(quiz_db))

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(make_db())

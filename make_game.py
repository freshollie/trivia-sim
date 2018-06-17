import requests
import datetime
from bs4 import BeautifulSoup

def get_quiz(date=None, url=None):
    if url == None:
        url = "https://hqbuff.com/"
        if date:
            url += "game/" + date.strftime("%Y-%m-%d")
    print(url)
    response = requests.get(url)
    response.encoding = "utf-8"
    data = BeautifulSoup(response.text, "html.parser")

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

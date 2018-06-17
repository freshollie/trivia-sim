import asyncio
import json
import random
import time

from datetime import timedelta, datetime
import websockets

from make_game import get_quiz


PLAYERS = set()

def generate_question_event(question, num, count):
    answers = []

    for choice in question["choices"]:
        answers.append({"text": choice})

    return {
        "type":  "question",
        "question": question["question"],
        "answers": answers,
        "questionNumber": num,
        "questionCount": count
    }


def generate_round_summary_event(question):
    answer_counts = []

    for choice in question["choices"]:
        answer_count = {
            "count": random.randint(0, 1000)
        }
        answer_count["correct"] = (choice == question["answer"])
        answer_count["answer"] = choice

        answer_counts.append(answer_count)
    
    return {
        "type": "questionSummary",
        "advancingPlayersCount": random.randint(1, 10000),
        "eliminatedPlayersCount": random.randint(1, 10000),
        "answerCounts": answer_counts
    }


async def broadcast_event(event):
    if PLAYERS:
        await asyncio.wait([player.send(json.dumps(event)) for player in PLAYERS])


async def game():
    print("Starting a game")
    print("Loading a quiz")
    QUIZ = []
    while not QUIZ:
        QUIZ = get_quiz(datetime.now() + timedelta(days=-random.randint(0, 50)))#, url="https://hqbuff.com/game/2018-05-23")

    print("Waiting for players to connect")
    # Wait for everyone to connect
    await asyncio.sleep(3)

    quiz_length = len(QUIZ)
    round_num = 1
    for question_round in QUIZ:
        print(f"Round {round_num}")

        print(question_round["question"])
        # Provide a question and wait for it to be answered 
        question_event = generate_question_event(question_round, round_num, quiz_length)
        await broadcast_event(question_event)
        await asyncio.sleep(10)

        summary_event = generate_round_summary_event(question_round)
        await broadcast_event(summary_event)
        await asyncio.sleep(5)

        round_num += 1
    print("Game finished")
    await asyncio.sleep(5)

def register(player):
    PLAYERS.add(player)

def unregister(player):
    PLAYERS.remove(player)

async def player_connection(websocket, path):
    print("Player connected")
    register(websocket)
    try:
        # Keep listen for answers. But ignore as we
        # don't use them
        async for message in websocket:
            pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        print("Player disconnected")
        unregister(websocket)

async def main():
    while True:
        # Provide a server, and start a game
        server = await websockets.serve(player_connection, "localhost", 8765)
        await game()

        server.close()
        await server.wait_closed()
        await asyncio.sleep(5)

asyncio.get_event_loop().run_until_complete(main())

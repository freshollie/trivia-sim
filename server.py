import asyncio
import json
import random
import time
import socket

from datetime import timedelta, datetime, timezone
from aiohttp import web
import websockets

from make_game import get_quiz, START_DATE

SOCKET_PORT = 8765
GAME_RUNNING = False

class GameServer:
    PORT = 8765

    def __init__(self):
        self.active = False
        self._players = set()
        self._socket = None

    @staticmethod
    def generate_question_event(question, num, count):
        answers = []

        for choice in question["choices"]:
            answers.append({"text": choice})

        return {"type":  "question",
                "question": question["question"],
                "answers": answers,
                "questionNumber": num,
                "questionCount": count}

    @staticmethod
    def generate_round_summary_event(question):
        answer_counts = []

        for choice in question["choices"]:
            answer_count = {
                "count": random.randint(0, 1000)
            }
            answer_count["correct"] = (choice == question["answer"])
            answer_count["answer"] = choice

            answer_counts.append(answer_count)
        
        return {"type": "questionSummary",
                "advancingPlayersCount": random.randint(1, 10000),
                "eliminatedPlayersCount": random.randint(1, 10000),
                "answerCounts": answer_counts}
    
    async def _broadcast_event(self, event):
        if self._players:
            await asyncio.wait([player.send(json.dumps(event)) for player in self._players])
    
    async def host_game(self):
        self.active = True
        print("Starting a game")
        print("Loading a quiz")
        QUIZ = []

        today = datetime.now()
        diff = (today - START_DATE).days

        while not QUIZ:
            QUIZ = await get_quiz(datetime.now() + timedelta(days=-random.randint(0, diff)), num=random.randint(1, 2))

        print("Waiting for players to connect")
        # Wait for everyone to connect
        await asyncio.sleep(3)

        quiz_length = len(QUIZ)
        round_num = 1
        for question_round in QUIZ:
            print(f"Round {round_num}")

            print(question_round["question"])
            # Provide a question and wait for it to be answered 
            question_event = self.generate_question_event(question_round, round_num, quiz_length)
            await self._broadcast_event(question_event)
            await asyncio.sleep(10)
            print("Sending answers")

            summary_event = GameServer.generate_round_summary_event(question_round)
            await self._broadcast_event(summary_event)
            await asyncio.sleep(5)

            round_num += 1
        print("Game finished")
        self.active = False

    def _register_player(self, player):
        self._players.add(player)

    def _unregister_player(self, player):
        self._players.remove(player)

    async def player_connection(self, websocket, path):
        print("Player connected")
        self._register_player(websocket)
        try:
            # Keep listen for answers. But ignore as we
            # don't use them
            async for _ in websocket:
                pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            print("Player disconnected")
            self._unregister_player(websocket)
    
    async def start(self):
        self._socket = await websockets.serve(self.player_connection, "0.0.0.0", GameServer.PORT)
    
    async def close(self):
        if self._socket:
            self._socket.close()
            await self._socket.wait_closed()


class Server():
    PORT = "8732"

    def __init__(self):
        self._next_game = None
        self._game_server = GameServer()
        self._event_loop = asyncio.get_event_loop()

    @staticmethod
    def get_ip():
        return socket.gethostbyname(socket.gethostname())

    def _generate_nextgame_info(self):
        return {"nextShowTime": self._next_game.strftime('%Y-%m-%dT%H:%M:%S.000Z'), 
                "nextShowPrize": "£400,000"}
    
    def _generate_broadcast_info(self):
        return {"broadcast": {"socketUrl": f"ws://{Server.get_ip()}:{GameServer.PORT}"}}

    async def _serve_game_info(self, request):
        if self._game_server.active:
            return web.json_response(self._generate_broadcast_info())
        else:
            return web.json_response(self._generate_nextgame_info())

    async def run(self):
        web_server = web.Server(self._serve_game_info)
        await self._event_loop.create_server(web_server, "0.0.0.0", Server.PORT)
        print(f"Webserver listen on {Server.PORT}")

        while True:
            next_game_wait = random.randint(1, 120)
            self._next_game = datetime.utcnow() + timedelta(seconds=next_game_wait)
            print(f"Game starting in {next_game_wait} seconds")
            await asyncio.sleep(next_game_wait)

            # Provide a server, and start a game
            await self._game_server.start()
            await self._game_server.host_game()
            await self._game_server.close()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(Server().run())

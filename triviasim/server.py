'''
HQTrivia Server Emulation
- Oliver Bell 2018

Running this file will create an API and game
server which mocks/simulates the real HQTrivia.

Connecting your analysis tool to this server will enable you
to be able to test it without waiting for a real game.

Quizes are provided by scraping HQBuff (No permission for this)
'''
import asyncio
import json
import random
import socket
import time
from datetime import datetime, timedelta, timezone

import websockets
from aiohttp import web

from triviasim import hqbuff

SOCKET_PORT = 8765
GAME_RUNNING = False


class GameServer:
    '''
    A representation of a HQTrivia Game socket
    server.

    Provides questions and answers in succession
    for a game to any client that connects to the socket
    '''
    PORT = 8765

    def __init__(self):
        self.active = False
        self._players = set()
        self._socket = None

    @staticmethod
    def generate_question_event(question, num, count):
        '''
        When a question needs to be distributed to
        the connected clients the correctly formatted
        JSON object can be generated with this method
        '''
        answers = []

        # Choices end up being formatted with their text and
        # values, however their values are not important
        for choice in question["choices"]:
            answers.append({"text": choice})

        return {"type":  "question",
                "question": question["question"],
                "answers": answers,
                "questionNumber": num,
                "questionCount": count}

    @staticmethod
    def generate_round_summary_event(question):
        '''
        After round is over, this method
        is used to generate a round summary of the answers to
        the quiz.

        Random player counts are provided
        '''
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
        '''
        Broadcast the given even to all connected
        players
        '''

        if self._players:
            await asyncio.wait([player.send(json.dumps(event)) for player in self._players])
    
    async def host_game(self):
        '''
        Hosts a HQTrivia game on the
        HQTrivia game socket.
        '''

        self.active = True
        print("Starting a game")
        print("Loading a quiz")

        quiz = await hqbuff.get_random_quiz()

        print("Waiting for players to connect")
        await asyncio.sleep(3)

        quiz_length = len(quiz)
        round_num = 1

        for question_round in quiz:
            print(f"Round {round_num}")

            print(question_round["question"])

            # Provide a question and wait for it to be answered 
            question_event = self.generate_question_event(question_round, round_num, quiz_length)
            await self._broadcast_event(question_event)
            # Give 10 seconds to answer
            await asyncio.sleep(10)

            # And then broadcast the answers
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

    async def _player_connection(self, websocket, path):
        ''' 
        Handles players connecting to the socket and registers
        them for broadcasts
        '''
        print("Player connected")
        self._register_player(websocket)
        try:
            # Keep listen for answers. But ignore all answers
            # as they are not used.
            async for _ in websocket: pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            print("Player disconnected")
            self._unregister_player(websocket)
    
    async def start(self):
        ''' 
        Start the socket listening for player connections
        '''
        self._socket = await websockets.serve(self._player_connection, "0.0.0.0", GameServer.PORT)
    
    async def close(self):
        '''
        Drain the player connections and close the socket
        '''
        if self._socket:
            self._socket.close()
            await self._socket.wait_closed()


class Server:
    '''
    Represents the HQTrivia Emulation Server
    '''

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
        '''
        Create a websever and host a HQTrivia game
        every minute or so. Broadcasting when the game will
        begin on the API.
        '''

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

def run():
    asyncio.get_event_loop().run_until_complete(Server().run())
    

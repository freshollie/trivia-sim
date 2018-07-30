'''
MIT License

Copyright (c) 2018, Oliver Bell <freshollie@gmail.com>

Running this file will create a mock REST api and game
server which simulates the real HQTrivia socket.

Connecting your analysis tool to this server will enable you
to be able to test the tool without waiting for a real game.

Quizes are provided by scraping HQBuff (No permission for this)
'''

from triviasim import server

server.run()

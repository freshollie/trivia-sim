# trivia-sim

Simulate the HQTrivia API and Game socket. Designed for testing HQTrivia prediction tools without relying on waiting for an active game.

## Usage

This project uses `pipenv` for dependency management. To run the server: `pipenv run python run.py`

The server API will be listening on port 8732 and will broadcast the socket IP and port when a emulated game
is running, just like how the real API does it.

## Questions

Questions used by the simulation are scraped from HQBuff. This is done without
permission.

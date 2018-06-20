FROM python:3.6
RUN pip install pipenv

WORKDIR /hqtrivia-socket-emulator

COPY Pipfile.lock Pipfile ./
RUN pipenv install --deploy --system --ignore-pipfile

COPY make_game.py server.py ./

ENTRYPOINT ["python3.6", "-u", "/hqtrivia-socket-emulator/server.py"]

FROM python:3.6
LABEL maintainer="Oliver Bell <freshollie@gmail.com>"
RUN pip install pipenv

WORKDIR /trivia-sim

COPY Pipfile.lock Pipfile ./
RUN pipenv install --deploy --system --ignore-pipfile

COPY triviasim triviasim
COPY run.py run.py

ENTRYPOINT ["python3.6", "-u", "/trivia-sim/run.py"]

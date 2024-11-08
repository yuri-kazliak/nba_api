FROM python:3.13-rc-slim
RUN pip install poetry
WORKDIR /src
COPY . .
RUN poetry install
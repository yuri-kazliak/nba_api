# nba_api

poetry run uvicorn src.main:app --reload


docker run -d --name nba_api -p 8018:8000 yurasick/my_basket_api:0.0.1
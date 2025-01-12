import http.client
from django.conf import settings
import json


def fetch_games_by_date(league, date):
    """
    fetch games by date and league from
    HOST: v1.american-football.api-sports.io
    league: 1 - NFL, 2 - NCAA
    date format: yyyy-mm-dd
    """

    print(f"fetch_game_by_date: {league}, {date}")
    league_id = ""
    if league == "NFL":
        league_id = "1"
    elif league == "NCAA":
        league_id = "2"
    else:
        print("fetch_data.fetch_game_by_date(): Error - Invalid League ID")
    conn = http.client.HTTPSConnection(settings.API_HOST)
    headers = {
        "x-rapidapi-host": settings.API_HOST,
        "x-rapidapi-key": settings.API_KEY,
    }

    conn.request(
        "GET",
        f"/games?league={league_id}&date={date}&timezone=America/New_York",
        headers=headers,
    )

    try:
        res = conn.getresponse()
        if res.status != 200:
            # If the response code is not OK, raise an exception
            raise Exception(f"API request failed with status code {res.status}")

        # Read the response data and decode it
        data = res.read().decode("utf-8")
        games_data = json.loads(data)

        # print(games_data)

        # Return the games data as JSON (or use as needed)
        return games_data

    except Exception as e:
        # Handle any errors that occur during the request
        print(f"Error fetching games: {str(e)}")
        return None

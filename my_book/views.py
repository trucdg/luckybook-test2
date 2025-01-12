from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import formset_factory
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
    TemplateView,
)
from django.views import View
from django.db.models import Q
from .models import Player, Game, Bet, SingleBet
from .models import Straight, Action, Parlay3, Parlay4
from .forms import (
    BetTypeForm,
    SingleBetForm,
    GameForm,
    GameSearchForm,
    PlayerForm,
    BetTypeFilterForm,
)
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.safestring import mark_safe
import json
from itertools import chain
from operator import attrgetter
from .utils import *
from .fetch_data import *
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required


class HomeView(TemplateView):
    """
    Class-based view for the homepage.
    """

    template_name = "my_book/home.html"


# Player Views
class PlayerListView(LoginRequiredMixin, ListView):
    """
    A View to list out Player and a summary of their betting money and payout
    - handles create new player post requests
    """

    model = Player
    template_name = "players/player_list.html"
    context_object_name = "players"

    def get_login_url(self) -> str:
        return reverse("login")

    def get_context_data(self, **kwargs):
        # Add the form to the context
        context = super().get_context_data(**kwargs)
        if "player_form" not in context:
            context["player_form"] = PlayerForm()

        # Fetch all players with their calculated fields
        players = Player.objects.all()

        # update all calculated money
        for player in players:
            player.calculate_total_betting_money()
            player.calculate_total_payout()

        context["players"] = players

        return context

    def post(self, request, *args, **kwargs):
        """Handle player creation when the form is submitted."""
        form = PlayerForm(request.POST)
        if form.is_valid():
            form.save()  # Create a new player instance
            return redirect("player-list")
        else:
            context = self.get_context_data()
            context["player_form"] = (
                form  # Pass the form with errors back to the template
            )
            return self.render_to_response(context)


class PlayerUpdateView(LoginRequiredMixin, UpdateView):
    model = Player
    form_class = PlayerForm
    template_name = "players/player_edit.html"
    context_object_name = "player"

    def get_login_url(self) -> str:
        return reverse("login")

    def get_success_url(self):
        # Redirect to the player list after editing
        return reverse_lazy("player-list")


class PlayerDetailView(LoginRequiredMixin, DetailView):
    model = Player
    template_name = "players/player_detail.html"
    context_object_name = "player"

    def get_login_url(self) -> str:
        return reverse("login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["bets_flat"] = self._get_player_bets_flat()

        return context

    def _get_player_bets_flat(self):
        # Retrieve the current player instance
        player = self.object

        bet_querysets = {
            "Straight": Straight.objects.filter(player=player),
            "Action": Action.objects.filter(player=player),
            "Parlay3": Parlay3.objects.filter(player=player),
            "Parlay4": Parlay4.objects.filter(player=player),
        }

        # Flatten bets into a single list
        bets_flat = []
        index = 1
        for bet_type, bet_list in bet_querysets.items():
            for bet in bet_list:
                # Extract single bets dynamically
                single_bets = []
                for i in range(1, 5):  # Up to 4 single bets
                    single_bet_attr = f"single_bet{i}"
                    if hasattr(bet, single_bet_attr):
                        single_bet = getattr(bet, single_bet_attr, None)
                        single_bets.append(single_bet)
                    else:
                        single_bets.append(None)  # Append None for missing single bets

                # Add bet details
                bets_flat.append(
                    {
                        "index": index,
                        "bet_pk": bet.pk,
                        "player_name": bet.player.name,
                        "bet_type": bet_type,
                        "amount": bet.bet_amount,
                        "payout": bet.payout,
                        "single_bet1": single_bets[0] if len(single_bets) > 0 else None,
                        "single_bet2": single_bets[1] if len(single_bets) > 1 else None,
                        "single_bet3": single_bets[2] if len(single_bets) > 2 else None,
                        "single_bet4": single_bets[3] if len(single_bets) > 3 else None,
                    }
                )
                index += 1
        return bets_flat


class PlayerDeleteView(LoginRequiredMixin, DeleteView):
    model = Player
    template_name = "players/player_delete.html"
    success_url = reverse_lazy("player-list")
    context_object_name = "player"

    def get_login_url(self) -> str:
        return reverse("login")


# GAME Views
class GameCreateView(LoginRequiredMixin, CreateView):
    model = Game
    form_class = GameForm
    template_name = "games/game_create.html"
    success_url = reverse_lazy("game-list")

    def get_login_url(self) -> str:
        return reverse("login")


@login_required(login_url="/login/")
def game_search_view(request):
    """
    A function view to handle search game by date request to Sports API
    To optimize:
    - Whenever a user fetch live game data, we use that data to update all unfinished games
    by calling __update_games_in_db()
    """
    if request.method == "POST":
        form = GameSearchForm(request.POST)
        if form.is_valid():
            league = form.cleaned_data["league"]
            date = form.cleaned_data["date"]

            # Get games from the API
            raw_games_data = fetch_games_by_date(league, date)

            """
            raw_games_data = {
                "get": "games",
                "parameters": {
                    "league": "1",
                    "date": "2025-01-04",
                    "timezone": "America/New_York",
                },
                "errors": [],
                "results": 2,
                "response": [
                    {
                        "game": {
                            "id": 13457,
                            "stage": "Regular Season",
                            "week": "Week 18",
                            "date": {
                                "timezone": "America/New_York",
                                "date": "2025-01-04",
                                "time": "16:30",
                                "timestamp": 1736026200,
                            },
                            "venue": {"name": "M&T Bank Stadium", "city": "Baltimore"},
                            "status": {
                                "short": "FT",
                                "long": "Finished",
                                "timer": None,
                            },
                        },
                        "league": {
                            "id": 1,
                            "name": "NFL",
                            "season": "2024",
                            "logo": "https://media.api-sports.io/american-football/leagues/1.png",
                            "country": {
                                "name": "USA",
                                "code": "US",
                                "flag": "https://media.api-sports.io/flags/us.svg",
                            },
                        },
                        "teams": {
                            "home": {
                                "id": 5,
                                "name": "Baltimore Ravens",
                                "logo": "https://media.api-sports.io/american-football/teams/5.png",
                            },
                            "away": {
                                "id": 9,
                                "name": "Cleveland Browns",
                                "logo": "https://media.api-sports.io/american-football/teams/9.png",
                            },
                        },
                        "scores": {
                            "home": {
                                "quarter_1": 7,
                                "quarter_2": 7,
                                "quarter_3": 7,
                                "quarter_4": 14,
                                "overtime": None,
                                "total": 35,
                            },
                            "away": {
                                "quarter_1": 0,
                                "quarter_2": 3,
                                "quarter_3": 0,
                                "quarter_4": 7,
                                "overtime": None,
                                "total": 10,
                            },
                        },
                    },
                    {
                        "game": {
                            "id": 13455,
                            "stage": "Regular Season",
                            "week": "Week 18",
                            "date": {
                                "timezone": "America/New_York",
                                "date": "2025-01-04",
                                "time": "20:00",
                                "timestamp": 1736038800,
                            },
                            "venue": {"name": "Acrisure Stadium", "city": "Pittsburgh"},
                            "status": {
                                "short": "FT",
                                "long": "Finished",
                                "timer": None,
                            },
                        },
                        "league": {
                            "id": 1,
                            "name": "NFL",
                            "season": "2024",
                            "logo": "https://media.api-sports.io/american-football/leagues/1.png",
                            "country": {
                                "name": "USA",
                                "code": "US",
                                "flag": "https://media.api-sports.io/flags/us.svg",
                            },
                        },
                        "teams": {
                            "home": {
                                "id": 22,
                                "name": "Pittsburgh Steelers",
                                "logo": "https://media.api-sports.io/american-football/teams/22.png",
                            },
                            "away": {
                                "id": 10,
                                "name": "Cincinnati Bengals",
                                "logo": "https://media.api-sports.io/american-football/teams/10.png",
                            },
                        },
                        "scores": {
                            "home": {
                                "quarter_1": 0,
                                "quarter_2": 7,
                                "quarter_3": 0,
                                "quarter_4": 10,
                                "overtime": None,
                                "total": 17,
                            },
                            "away": {
                                "quarter_1": 10,
                                "quarter_2": 3,
                                "quarter_3": 3,
                                "quarter_4": 3,
                                "overtime": None,
                                "total": 19,
                            },
                        },
                    },
                ],
            }
            """

            # NOTE: in the API,game['status']['long'] for finished game is Finished or "Final/OT"

            raw_games_response = raw_games_data.get("response", [])

            if raw_games_response is None:
                print(f"views.game_search_view(): Failed to fetch games data.")
                return None

            # Preprocess games into a clean format
            games = []
            for raw_game in raw_games_response:
                game = {
                    "league": raw_game["league"]["name"],
                    "stage": raw_game["game"]["stage"],
                    "week": raw_game["game"]["week"],
                    "date": raw_game["game"]["date"]["date"],
                    "time": raw_game["game"]["date"]["time"],
                    "team_a": raw_game["teams"]["away"]["name"],
                    "team_a_logo_url": raw_game["teams"]["away"]["logo"],
                    "team_b": raw_game["teams"]["home"]["name"],
                    "team_b_logo_url": raw_game["teams"]["home"]["logo"],
                    "status": raw_game["game"]["status"]["long"],
                    "score_team_a": raw_game["scores"]["away"]["total"],
                    "score_team_b": raw_game["scores"]["home"]["total"],
                }

                games.append(game)

            # Convert each game to JSON format
            for game in games:
                game["json_data"] = json.dumps(game)

            # Prepare lists for query
            team_a_list = [game["team_a"] for game in games]
            team_b_list = [game["team_b"] for game in games]
            game_dates = [
                datetime.strptime(game["date"], "%Y-%m-%d").date() for game in games
            ]

            # get games query set from db that match the same teams and date
            db_games_queryset = Game.objects.filter(
                Q(
                    team_a__in=team_a_list,
                    team_b__in=team_b_list,
                    game_date__in=game_dates,
                )
                | Q(
                    team_a__in=team_b_list,
                    team_b__in=team_a_list,
                    game_date__in=game_dates,
                )
            )
            added_games = set(
                db_games_queryset.values_list("team_a", "team_b", "game_date")
            )

            # Normalize `date` in `games` and check membership
            for game in games:
                game_date_obj = datetime.strptime(game["date"], "%Y-%m-%d").date()
                game["is_added"] = (
                    game["team_a"],
                    game["team_b"],
                    game_date_obj,
                ) in added_games or (
                    game["team_b"],
                    game["team_a"],
                    game_date_obj,
                ) in added_games

            # update unfinished games in database
            __update_game_in_db(games, db_games_queryset)

            # Display games in the template
            return render(
                request,
                "games/game_search.html",
                {"form": form, "games": games},
            )
    else:
        form = GameSearchForm()

    return render(request, "games/game_search.html", {"form": form})


def __update_game_in_db(games_data, db_games_queryset):
    """
    method for optimization purpose:
    - whenever user fetch live game data, use that game data to update
    unfinished games in db
    input:
     - games_data: data fetched from live api
     - added_games: queryset of games in the database with same team_a, team_b and date
    """

    unfinished_games_qs = db_games_queryset.filter(is_finished=False)

    # Build a lookup dictionary from games_data
    games_lookup = {
        (
            game["team_a"],
            game["team_b"],
            datetime.strptime(game["date"], "%Y-%m-%d").date(),
        ): game
        for game in games_data
    }

    updated_count = 0

    # Iterate through unfinished games and update them
    for db_game in unfinished_games_qs:
        # Check if the game exists in the live data (accounting for team order)
        game_key = (db_game.team_a, db_game.team_b, db_game.game_date)
        reverse_game_key = (db_game.team_b, db_game.team_a, db_game.game_date)

        live_game_data = games_lookup.get(game_key) or games_lookup.get(
            reverse_game_key
        )

        if live_game_data:
            fields_to_update = []
            update_total = False

            if live_game_data.get("score_team_a") not in ["None", None]:
                db_game.score_team_a = float(live_game_data["score_team_a"])
                fields_to_update.append("score_team_a")
                update_total = True

            if live_game_data.get("score_team_b") not in ["None", None]:
                db_game.score_team_b = float(live_game_data["score_team_b"])
                fields_to_update.append("score_team_b")
                update_total = True

            if update_total:
                db_game.total_points = db_game.score_team_a + db_game.score_team_b
                fields_to_update.append("total_points")

            if live_game_data.get("team_a_logo_url") not in ["None", None]:
                db_game.team_a_logo_url = live_game_data["team_a_logo_url"]
                fields_to_update.append("team_a_logo_url")

            if live_game_data.get("team_b_logo_url") not in ["None", None]:
                db_game.team_b_logo_url = live_game_data["team_b_logo_url"]
                fields_to_update.append("team_b_logo_url")

            if live_game_data.get("status") in ["Finished", "Final/OT"]:
                db_game.is_finished = True
                fields_to_update.append("is_finished")

            # Save the game only if there are fields to update
            if fields_to_update:
                db_game.save(update_fields=fields_to_update)
                updated_count += 1

    print(
        f"views.__update_game_in_db():Updated {updated_count} unfinished games in the database."
    )
    return updated_count


@login_required(login_url="/login/")
def game_review_view(request):
    """
    Review selected games resulted from the live search
    In this view, user need to insert the game favorite team and the spread
    before the game is added to database
    """
    if request.method == "POST":
        # print("REQUEST.POST", request.POST)
        selected_games_json = request.POST.getlist("selected_games")

        # Parse the JSON strings into Python dictionaries
        selected_games = [json.loads(game_json) for game_json in selected_games_json]

        return render(request, "games/game_review.html", {"games": selected_games})
    return redirect("game-search")


@login_required(login_url="/login/")
def add_reviewed_games_to_db_view(request):
    """
    handle POST request to add-reviewed-games url and add games into database
    - reviewed games should have fav and fav_spread provided by user along
    with all information pulled from live api

    example of a request.POST with 2 reviewed games:
    ADD GAME request.POST
    <QueryDict: {'csrfmiddlewaretoken': ['kdynGLGgTZ5D'],
    'games[0][game_date]': ['2025-01-04'],
    'games[0][league]': ['NFL'],
    'games[0][team_a]': ['Baltimore Ravens'],
    'games[0][team_b]': ['Cleveland Browns'],
    'games[0][score_team_a]': ['35'],
    'games[0][score_team_b]': ['10'],
    'games[0][team_a_logo_url]': ['https://media.api-sports.io/american-football/teams/5.png'],
    'games[0][team_b_logo_url]': ['https://media.api-sports.io/american-football/teams/9.png'],
    'games[0][fav_spread]': ['1.2'],
    'games[0][over_under_points]' : '[41.0]',
    'games[0][fav]': ['Baltimore Ravens'],
    'games[1][game_date]': ['2025-01-04'],
    'games[1][league]': ['NFL'],
    'games[1][team_a]': ['Pittsburgh Steelers'],
    'games[1][team_b]': ['Cincinnati Bengals'],
    'games[1][score_team_a]': ['17'],
    'games[1][score_team_b]': ['19'],
    'games[1][team_a_logo_url]': ['https://media.api-sports.io/american-football/teams/22.png'],
    'games[1][team_b_logo_url]': ['https://media.api-sports.io/american-football/teams/10.png'],
    'games[1][fav_spread]': ['1.3'],
    'games[1][over_under_points]' : '[42.0]',
    'games[1][fav]': ['Pittsburgh Steelers']}>
    """
    if request.method == "POST":
        try:
            games_data = []
            # Iterate through the request.POST to gather game data
            for key, value in request.POST.items():
                if key.startswith("games"):
                    # Parse the incoming nested dictionary structure
                    key_parts = key.split("[")
                    index = int(key_parts[1][:-1])  # Extract the index from 'games[0]'
                    field_name = key_parts[2][:-1]  # Extract the field name ('team_a')

                    # Ensure the games_data list is properly initialized
                    while len(games_data) <= index:
                        games_data.append({})
                    games_data[index][field_name] = value

            print("in ADD, games_data=", games_data)

            # Validate and save each game entry
            saved_games = []
            default_logo = "https://as2.ftcdn.net/v2/jpg/05/97/47/95/1000_F_597479556_7bbQ7t4Z8k3xbAloHFHVdZIizWK1PdOo.jpghttps://as2.ftcdn.net/v2/jpg/05/97/47/95/1000_F_597479556_7bbQ7t4Z8k3xbAloHFHVdZIizWK1PdOo.jpg"
            for game_data in games_data:
                game, created = Game.objects.update_or_create(
                    game_date=game_data.get("game_date"),
                    team_a=game_data.get("team_a"),
                    team_b=game_data.get("team_b"),
                    # if game is found, the fields in defaults are updated with the new values
                    defaults={
                        "league": game_data.get("league"),
                        "is_finished": (
                            True
                            if game_data.get("status") in ["Finished", "Final/OT"]
                            else False
                        ),
                        "team_a_logo_url": (
                            game_data.get("team_a_logo_url")
                            if game_data.get("team_a_logo_url") not in ["None", None]
                            else default_logo
                        ),
                        "team_b_logo_url": (
                            game_data.get("team_b_logo_url")
                            if game_data.get("team_b_logo_url") not in ["None", None]
                            else default_logo
                        ),
                        "fav_spread": float(game_data.get("fav_spread")),
                        "over_under_points": float(game_data.get("over_under_points")),
                        "fav": game_data.get("fav"),
                        "score_team_a": (
                            float(game_data.get("score_team_a", 0.0))
                            if game_data.get("score_team_a") not in ["None", None]
                            else 0.0
                        ),
                        "score_team_b": (
                            float(game_data.get("score_team_b", 0.0))
                            if game_data.get("score_team_b") not in ["None", None]
                            else 0.0
                        ),
                    },
                )
                if created:
                    saved_games.append(
                        {
                            "game_date": game.game_date,
                            "team_a": game.team_a,
                            "team_b": game.team_b,
                            "score_team_a": game.score_team_a,
                            "score_team_b": game.score_team_b,
                            "team_a_logo_url": game.team_a_logo_url,
                            "team_b_logo_url": game.team_b_logo_url,
                            "fav": game.fav,
                            "fav_spread": game.fav_spread,
                            "over_under_points": game.over_under_points,
                            "created": created,
                        }
                    )

            return render(
                request,
                "games/game_successfully_added.html",
                {"saved_games": saved_games},
            )
        except Exception as e:
            print("views.add_reviewed_games_to_db_view() Exception: ", e)
            return redirect("game-review")
    return redirect("game-review")


@login_required(login_url="/login/")
def get_game_results_view(request):
    """
    Fetch games for dates with unfinished games and update the database.
    """

    league = request.GET.get("league")

    if league not in ["NFL", "NCAA"]:
        print("views.get_game_results_view(): Error! Invalid league")
        messages.error(request, "Invalid league specified.")
        return redirect("game-list")

    unfinished_games_qs = Game.objects.filter(is_finished=False)

    unfinished_game_dates = unfinished_games_qs.values_list(
        "game_date", flat=True
    ).distinct()

    # Fetch and update games
    updated_count = 0
    for game_date in unfinished_game_dates:
        raw_games_data = fetch_games_by_date(league, game_date)
        raw_games_response = raw_games_data.get("response", [])

        if not raw_games_response:
            continue

        # Preprocess games into a clean format
        games_lookup = {}
        for raw_game in raw_games_response:
            game_key = (
                raw_game["teams"]["away"]["name"],
                raw_game["teams"]["home"]["name"],
                raw_game["game"]["date"]["date"],
            )
            games_lookup[game_key] = {
                "team_a": raw_game["teams"]["away"]["name"],
                "team_b": raw_game["teams"]["home"]["name"],
                "score_team_a": raw_game["scores"]["away"]["total"],
                "score_team_b": raw_game["scores"]["home"]["total"],
                "team_a_logo_url": raw_game["teams"]["away"]["logo"],
                "team_b_logo_url": raw_game["teams"]["home"]["logo"],
                "status": raw_game["game"]["status"]["long"],
            }

        # Update unfinished games in the database
        for db_game in unfinished_games_qs.filter(game_date=game_date):

            game_key = (db_game.team_a, db_game.team_b, str(db_game.game_date))
            reverse_game_key = (db_game.team_b, db_game.team_a, str(db_game.game_date))

            live_game_data = games_lookup.get(game_key) or games_lookup.get(
                reverse_game_key
            )

            if live_game_data:
                fields_to_update = []
                update_total = False

                if live_game_data.get("status") in ["Finished", "Final/OT"]:
                    db_game.is_finished = True
                    fields_to_update.append("is_finished")
                    update_total = True

                if live_game_data.get("score_team_a") not in ["None", None]:
                    db_game.score_team_a = float(live_game_data["score_team_a"])
                    fields_to_update.append("score_team_a")
                    update_total = True

                if live_game_data.get("score_team_b") not in ["None", None]:
                    db_game.score_team_b = float(live_game_data["score_team_b"])
                    fields_to_update.append("score_team_b")
                    update_total = True

                if update_total:
                    db_game.total_points = db_game.score_team_a + db_game.score_team_b
                    fields_to_update.append("total_points")

                if live_game_data.get("team_a_logo_url") not in ["None", None]:
                    db_game.team_a_logo_url = live_game_data["team_a_logo_url"]
                    fields_to_update.append("team_a_logo_url")

                if live_game_data.get("team_b_logo_url") not in ["None", None]:
                    db_game.team_b_logo_url = live_game_data["team_b_logo_url"]
                    fields_to_update.append("team_b_logo_url")

                # Save the game only if there are fields to update
                if fields_to_update:
                    db_game.save(update_fields=fields_to_update)
                    updated_count += 1

    if updated_count:
        messages.success(
            request, f"Successfully updated {updated_count} games for {league}."
        )
    else:
        messages.info(request, f"No games to update for {league}.")

    return redirect("game-list")


@login_required(login_url="/login/")
def game_list_view(request):
    """
    A function view to display a lst of all games
    """
    nfl_games = Game.objects.filter(league="NFL").order_by("-game_date")
    ncaa_games = Game.objects.filter(league="NCAA").order_by("-game_date")
    return render(
        request,
        "games/game_list.html",
        {
            "nfl_games": nfl_games,
            "ncaa_games": ncaa_games,
        },
    )


class GameDetailView(LoginRequiredMixin, DetailView):
    """
    Class-based view for displaying detailed information about a specific game.
    """

    model = Game
    template_name = "games/game_detail.html"
    context_object_name = "game"

    def get_login_url(self) -> str:
        return reverse("login")


class GameUpdateView(LoginRequiredMixin, UpdateView):
    """
    A view class to update Game detail
    """

    model = Game
    form_class = GameForm
    template_name = "games/game_edit.html"
    success_url = reverse_lazy("game-list")

    def get_login_url(self) -> str:
        return reverse("login")


class GameDeleteView(LoginRequiredMixin, DeleteView):
    model = Game
    template_name = "games/game_delete.html"
    success_url = reverse_lazy("game-list")
    context_object_name = "game"

    def get_login_url(self) -> str:
        return reverse("login")


# Bet Views
class BetListView(LoginRequiredMixin, ListView):
    template_name = "bets/bet_list.html"
    SingleBetFormSet = formset_factory(SingleBetForm, extra=0)

    def get_login_url(self) -> str:
        return reverse("login")

    def get_queryset(self):
        """
        We define a get_queryset() for ListView
        However, in the template, we display bets from the bets_flat list made by _get_flat_bet_list
        """
        # Fetch all bets from different models
        straight_bets = Straight.objects.all()
        action_bets = Action.objects.all()
        parlay3_bets = Parlay3.objects.all()
        parlay4_bets = Parlay4.objects.all()

        # Combine all the querysets into one list
        all_bets = list(chain(straight_bets, action_bets, parlay3_bets, parlay4_bets))

        # Order the combined list by the 'created_at' field
        all_bets.sort(key=attrgetter("created_at"), reverse=True)

        return all_bets

    def get_context_data(
        self,
        bet_type_form=None,
        single_bet_forms=None,
        bet_type_filter_form=None,
        **kwargs,
    ):
        """
        Pass in extra data to use in the templates:
        - bet_type_form = BetTypeForm() is used to create a new bet in that type
        - bet_type_filter_form = BetTypeFilterForm() is used to filter the displaying results by bet type
        """
        context = super().get_context_data(**kwargs)

        # if default forms are not provided, create new
        if bet_type_form is None:
            bet_type_form = BetTypeForm()
        if single_bet_forms is None:
            single_bet_forms = self.SingleBetFormSet()

        # create the filter form instance
        if bet_type_filter_form is None:
            bet_type_filter_form = BetTypeFilterForm()

        # Fetch all available games
        games = Game.objects.all().values(
            "id",
            "team_a",
            "team_b",
            "name",
            "game_date",
            "fav_spread",
            "over_under_points",
        )

        # Flatten the bet objects into a list with global index
        bet_type_filter = self.request.GET.get("bet_type_filter")
        bets_flat = self._get_flat_bet_list(bet_type_filter)

        context["bet_type_form"] = bet_type_form
        context["single_bet_forms"] = single_bet_forms
        context["bet_type_filter_form"] = bet_type_filter_form
        context["bets_flat"] = bets_flat
        context["games_json"] = mark_safe(
            json.dumps(list(games), cls=DjangoJSONEncoder)
        )

        return context

    def post(self, request, *args, **kwargs):
        """
        Handle bet creation and deletion form submission.
        """
        # Ensure `object_list` is populated
        self.object_list = self.get_queryset()

        # handle bet DELETION
        if "delete_bet_pk" in request.POST:
            delete_bet_id = request.POST.get("delete_bet_pk")
            delete_bet_type = request.POST.get("delete_bet_type")
            return redirect(
                reverse("bet-delete", args=[delete_bet_type, delete_bet_id])
            )

        bet_type_form = BetTypeForm(request.POST)
        single_bet_forms = self.SingleBetFormSet(request.POST)

        if not single_bet_forms.is_valid():
            for form in single_bet_forms:
                if not form.is_valid():
                    print(f"Form errors: {form.errors}")
            print(f"Non-form errors: {single_bet_forms.non_form_errors()}")

        # Initial Validation Check: This block ensures that the top-level forms
        # (BetTypeForm and the SingleBetFormSet) are valid.
        # if the Forms are not valid, rerender the page
        if not bet_type_form.is_valid() or not single_bet_forms.is_valid():
            return self._re_render_with_context(
                request, bet_type_form, single_bet_forms
            )

        # Extract the necessary data from request.POST
        post_data = request.POST

        # Extract bet type and create the appropriate form
        player_id = post_data["player"]
        bet_type = post_data["bet_type"]
        bet_amount = post_data["bet_amount"]

        # get the player instance
        try:
            player = Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            print("User with the specified name does not exist.")

        single_bets = []

        # Iterate through the total forms to create SingleBet instances
        for i in range(len(single_bet_forms)):
            try:
                # Dynamically construct field names
                game_id = post_data.get(f"single_bet_{i}_game")
                single_bet_type = post_data.get(f"single_bet_{i}_single_bet_type")
                selected_team = post_data.get(f"single_bet_{i}_selected_team")
                is_over = (
                    post_data.get(f"single_bet_{i}_is_over") == "on"
                )  # Convert checkbox to boolean

                # Ensure the Game instance exists
                game = Game.objects.get(id=game_id)

                # Create the SingleBet instance
                single_bet = SingleBet(
                    game=game,
                    single_bet_type=single_bet_type,
                    selected_team=selected_team,
                    is_over=(
                        is_over if single_bet_type == "OVER-UNDER" else None
                    ),  # Apply only if relevant
                )

                # save the single bet instance so that we can use to create the other bet type
                single_bet.save()

                single_bets.append(single_bet)

            except Game.DoesNotExist:
                print(
                    f"Game with ID {game_id} does not exist. Skipping this SingleBet."
                )
            except Exception as e:
                print(f"Error creating SingleBet for form {i}: {e}")

        # Now that we have enough information, we can create the bet object
        bet = self.create_bet(bet_type, player, bet_amount, single_bets)

        # Redirect to refresh the page
        return redirect(reverse("bet-list"))

    def create_bet(self, bet_type, player, bet_amount, single_bets):
        """
        Create a bet instance based on the bet_type and a list of SingleBet instances.

        input:
            bet_type (str): The type of bet (e.g., "Straight", "Action", "Parlay3", "Parlay4").
            player (Player): The player placing the bet.
            bet_amount (Decimal): The amount of the bet.
            single_bets (list): A list of SingleBet instances.

        Returns:
            Bet instance: The created bet instance.
        """
        try:
            if bet_type == "Straight" and len(single_bets) == 1:
                bet = Straight(
                    player=player,
                    bet_amount=bet_amount,
                    single_bet1=single_bets[0],
                )

            elif bet_type == "Action" and len(single_bets) == 2:
                bet = Action(
                    player=player,
                    bet_amount=bet_amount,
                    single_bet1=single_bets[0],
                    single_bet2=single_bets[1],
                )

            elif bet_type == "Parlay3" and len(single_bets) == 3:
                bet = Parlay3(
                    player=player,
                    bet_amount=bet_amount,
                    single_bet1=single_bets[0],
                    single_bet2=single_bets[1],
                    single_bet3=single_bets[2],
                )

            elif bet_type == "Parlay4" and len(single_bets) == 4:
                bet = Parlay4(
                    player=player,
                    bet_amount=bet_amount,
                    single_bet1=single_bets[0],
                    single_bet2=single_bets[1],
                    single_bet3=single_bets[2],
                    single_bet4=single_bets[3],
                )

            else:
                raise ValueError(
                    f"Invalid bet type or mismatched SingleBet count for {bet_type}."
                )

            # Validate and save the bet instance
            bet.full_clean()  # Run model validation
            bet.save()
            # print(f"BetListView.create_bet(): Created {bet_type} bet: {bet}")
            return bet

        except Exception as e:
            print(f"BetListView.create_bet(): Error creating {bet_type} bet: {e}")
            return None

    def _re_render_with_context(self, request, bet_type_form, single_bet_forms):
        """
        re-render the page with updated context
        """
        context = self.get_context_data(
            bet_type_form=bet_type_form, single_bet_forms=single_bet_forms
        )
        return render(self.request, self.template_name, context)

    def _get_flat_bet_list(self, bet_type_filter=None):
        """
        Flatten the bet list for context.
        Args:
            bet_type_filter (str): Filter to display specific bet type or None for all types.
        Returns:
            List[dict]: Flattened list of bets with details.
        """
        bet_querysets = {
            "Straight": Straight.objects.all(),
            "Action": Action.objects.all(),
            "Parlay3": Parlay3.objects.all(),
            "Parlay4": Parlay4.objects.all(),
        }

        # Filter querysets if bet_type_filter is provided
        if bet_type_filter is not None and bet_type_filter != "":
            bet_querysets = {
                bet_type: queryset
                for bet_type, queryset in bet_querysets.items()
                if bet_type == bet_type_filter
            }

        # Flatten bets into a single list
        bets_flat = []
        index = 1
        for bet_type, bet_list in bet_querysets.items():
            for bet in bet_list:
                # Extract single bets dynamically
                single_bets = []
                for i in range(1, 5):  # Up to 4 single bets
                    single_bet_attr = f"single_bet{i}"
                    if hasattr(bet, single_bet_attr):
                        single_bet = getattr(bet, single_bet_attr, None)
                        single_bets.append(single_bet)
                    else:
                        single_bets.append(None)  # Append None for missing single bets

                # Add bet details
                bets_flat.append(
                    {
                        "index": index,
                        "bet_pk": bet.pk,
                        "player_name": bet.player.name,
                        "player_id": bet.player.id,
                        "bet_type": bet_type,
                        "amount": bet.bet_amount,
                        "payout": bet.payout,
                        "single_bet1": single_bets[0] if len(single_bets) > 0 else None,
                        "single_bet2": single_bets[1] if len(single_bets) > 1 else None,
                        "single_bet3": single_bets[2] if len(single_bets) > 2 else None,
                        "single_bet4": single_bets[3] if len(single_bets) > 3 else None,
                    }
                )
                index += 1
        return bets_flat

    def get_bet_details(self, bet, bet_type):
        if bet_type == "Straight":
            return bet.single_bet
        elif bet_type == "Action":
            return f"{bet.single_bet1} and {bet.single_bet2}"
        elif bet_type == "Parlay3":
            return f"{bet.single_bet1}, {bet.single_bet2}, {bet.single_bet3}"
        elif bet_type == "Parlay4":
            return f"{bet.single_bet1}, {bet.single_bet2}, {bet.single_bet3}, {bet.single_bet4}"
        return ""


@login_required(login_url="/login/")
def delete_bet(request, bet_type, bet_id):
    """
    this is a function based view that shows the bet delete confirmation page
    """
    try:
        # Determine the model based on bet type and get the bet instance
        if bet_type == "Straight":
            bet = get_object_or_404(Straight, id=bet_id)
        elif bet_type == "Action":
            bet = get_object_or_404(Action, id=bet_id)
        elif bet_type == "Parlay3":
            bet = get_object_or_404(Parlay3, id=bet_id)
        elif bet_type == "Parlay4":
            bet = get_object_or_404(Parlay4, id=bet_id)
        else:
            print("delete_bet(): Invalid bet type")
            return redirect("bet-list")

        if request.method == "POST":
            # Perform the deletion if user confirms delete
            bet.delete()
            print(f"{bet_type}(pk={bet_id}) bet deleted successfully.")
            return redirect(reverse("bet-list"))

    except Exception as e:
        print(f"delete_bet(): Error {str(e)}")

    return render(
        request,
        "bets/bet_confirm_delete.html",
        {
            "bet": bet,
            "bet_type": bet_type,
        },
    )


class CalculatePayoutView(LoginRequiredMixin, View):
    """
    A view class to calculate the payout for all bets if scores available
    """

    def get_login_url(self) -> str:
        return reverse("login")

    def post(self, request, *args, **kwargs):
        """
        when received a post request to calculate all payout
        """
        # Collect all bet types
        all_bets = [
            Straight.objects.all(),
            Action.objects.all(),
            Parlay3.objects.all(),
            Parlay4.objects.all(),
        ]

        # Iterate through each bet and calculate payout
        for bet_queryset in all_bets:
            for bet in bet_queryset:  # Iterate through each individual bet
                bet.calculate_payout()
                bet.save(update_fields=["payout"])

        # Redirect back to the bet list page
        return redirect("bet-list")


@login_required(login_url="/login/")
def insights_page(request):
    # Generate the graph for comparing bet types
    bet_type_graph = generate_bet_type_comparison_graph()

    # Generate the graph for comparing money/payout for each bet type
    money_payout_graph = generate_money_payout_comparison_graph()

    # Pass the context to the template
    context = {
        "bets_type_graph": bet_type_graph,
        "money_payout_graph": money_payout_graph,
    }

    # Render the template with the context data
    return render(request, "insights/insights_page.html", context)

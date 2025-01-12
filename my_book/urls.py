from django.urls import path
from .views import (
    HomeView,
    PlayerListView,
    PlayerDetailView,
    PlayerUpdateView,
    PlayerDeleteView,
    GameCreateView,
    game_list_view,
    game_search_view,
    game_review_view,
    add_reviewed_games_to_db_view,
    get_game_results_view,
    GameDetailView,
    GameUpdateView,
    GameDeleteView,
    BetListView,
    delete_bet,
    CalculatePayoutView,
    insights_page,
)

from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    # Player URLs
    path(
        "players/", PlayerListView.as_view(), name="player-list"
    ),  # also handle player creation
    path("players/<int:pk>/", PlayerDetailView.as_view(), name="player-detail"),
    path("players/<int:pk>/edit/", PlayerUpdateView.as_view(), name="player-edit"),
    path("players/<int:pk>/delete/", PlayerDeleteView.as_view(), name="player-delete"),
    # Game URLs
    path("games/", game_list_view, name="game-list"),
    path(
        "games/create/", GameCreateView.as_view(), name="game-create"
    ),  # handle manual game creation and save to db
    path(
        "games/search/", game_search_view, name="game-search"
    ),  # handle search game by fetching data from api
    path("games/review/", game_review_view, name="game-review"),
    path(
        "games/add-reviewed-games-to-db",
        add_reviewed_games_to_db_view,
        name="add-reviewed-games",
    ),
    path(
        "games/get-game-results/", get_game_results_view, name="get-game-results"
    ),  # get results for unfinished games in database
    path("games/<int:pk>/", GameDetailView.as_view(), name="game-detail"),
    path("games/<int:pk>/edit/", GameUpdateView.as_view(), name="game-edit"),
    path("games/<int:pk>/delete/", GameDeleteView.as_view(), name="game-delete"),
    # Bet URLs
    path("bets/", BetListView.as_view(), name="bet-list"),
    path("bet/<str:bet_type>/<int:bet_id>/delete/", delete_bet, name="bet-delete"),
    # Calculate Payout
    path("calculate-payout/", CalculatePayoutView.as_view(), name="calculate-payout"),
    # Insights page
    path("insights/", insights_page, name="insights"),
    # authentication URLs
    path(
        r"login/",
        auth_views.LoginView.as_view(template_name="my_book/login.html"),
        name="login",
    ),
    path(
        r"logout/",
        auth_views.LogoutView.as_view(template_name="my_book/logged_out.html"),
        name="logout",
    ),
]

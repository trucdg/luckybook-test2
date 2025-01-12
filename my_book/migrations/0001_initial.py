# Generated by Django 5.1.4 on 2025-01-12 04:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Player",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                (
                    "total_betting_money",
                    models.DecimalField(decimal_places=2, default=0.0, max_digits=12),
                ),
                (
                    "total_payout",
                    models.DecimalField(decimal_places=2, default=0.0, max_digits=12),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Game",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                ("team_a", models.CharField(max_length=100)),
                ("team_b", models.CharField(max_length=100)),
                (
                    "team_a_logo_url",
                    models.URLField(
                        blank=True,
                        default="https://as2.ftcdn.net/v2/jpg/05/97/47/95/1000_F_597479556_7bbQ7t4Z8k3xbAloHFHVdZIizWK1PdOo.jpghttps://as2.ftcdn.net/v2/jpg/05/97/47/95/1000_F_597479556_7bbQ7t4Z8k3xbAloHFHVdZIizWK1PdOo.jpg",
                        max_length=400,
                        null=True,
                    ),
                ),
                (
                    "team_b_logo_url",
                    models.URLField(
                        blank=True,
                        default="https://as2.ftcdn.net/v2/jpg/05/97/47/95/1000_F_597479556_7bbQ7t4Z8k3xbAloHFHVdZIizWK1PdOo.jpghttps://as2.ftcdn.net/v2/jpg/05/97/47/95/1000_F_597479556_7bbQ7t4Z8k3xbAloHFHVdZIizWK1PdOo.jpg",
                        max_length=400,
                        null=True,
                    ),
                ),
                (
                    "league",
                    models.CharField(
                        choices=[("NFL", "NFL"), ("NCAA", "NCAA")], max_length=20
                    ),
                ),
                ("game_date", models.DateField()),
                (
                    "fav",
                    models.CharField(
                        help_text="Exact match of either Team A's name or Team B's name.",
                        max_length=100,
                    ),
                ),
                (
                    "fav_spread",
                    models.DecimalField(
                        decimal_places=1,
                        help_text="Spread for the favorite team (i.e: 3.0, 2.5)",
                        max_digits=4,
                    ),
                ),
                (
                    "score_team_a",
                    models.DecimalField(
                        blank=True,
                        decimal_places=1,
                        default=0.0,
                        help_text="Final score for Team A.",
                        max_digits=4,
                        null=True,
                    ),
                ),
                (
                    "score_team_b",
                    models.DecimalField(
                        blank=True,
                        decimal_places=1,
                        default=0.0,
                        help_text="Final score for Team B.",
                        max_digits=4,
                        null=True,
                    ),
                ),
                (
                    "total_points",
                    models.DecimalField(
                        blank=True,
                        decimal_places=1,
                        default=0.0,
                        help_text="Total final points for both teams.",
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "over_under_points",
                    models.DecimalField(
                        decimal_places=1,
                        default=0.0,
                        help_text="Over/ Under points for both teams.",
                        max_digits=5,
                    ),
                ),
                (
                    "is_finished",
                    models.BooleanField(
                        default=False, help_text="Indicates if the game is finished."
                    ),
                ),
            ],
            options={"unique_together": {("game_date", "team_a", "team_b")},},
        ),
        migrations.CreateModel(
            name="SingleBet",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "single_bet_type",
                    models.CharField(
                        choices=[("WINNER", "Winner"), ("OVER-UNDER", "Over-Under")],
                        max_length=20,
                    ),
                ),
                (
                    "selected_team",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "is_over",
                    models.BooleanField(
                        blank=True,
                        help_text="True for 'Over' bets, False for 'Under' bets.",
                        null=True,
                    ),
                ),
                (
                    "game",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="single_bets",
                        to="my_book.game",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Parlay4",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("bet_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "payout",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parlay4_bets",
                        to="my_book.player",
                    ),
                ),
                (
                    "single_bet1",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parlay4_single_bet1",
                        to="my_book.singlebet",
                    ),
                ),
                (
                    "single_bet2",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parlay4_single_bet2",
                        to="my_book.singlebet",
                    ),
                ),
                (
                    "single_bet3",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parlay4_single_bet3",
                        to="my_book.singlebet",
                    ),
                ),
                (
                    "single_bet4",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parlay4_single_bet4",
                        to="my_book.singlebet",
                    ),
                ),
            ],
            options={"abstract": False,},
        ),
        migrations.CreateModel(
            name="Parlay3",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("bet_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "payout",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parlay3_bets",
                        to="my_book.player",
                    ),
                ),
                (
                    "single_bet1",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parlay3_single_bet1",
                        to="my_book.singlebet",
                    ),
                ),
                (
                    "single_bet2",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parlay3_single_bet2",
                        to="my_book.singlebet",
                    ),
                ),
                (
                    "single_bet3",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parlay3_single_bet3",
                        to="my_book.singlebet",
                    ),
                ),
            ],
            options={"abstract": False,},
        ),
        migrations.CreateModel(
            name="Action",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("bet_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "payout",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="action_bets",
                        to="my_book.player",
                    ),
                ),
                (
                    "single_bet1",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="action_single_bet1",
                        to="my_book.singlebet",
                    ),
                ),
                (
                    "single_bet2",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="action_single_bet2",
                        to="my_book.singlebet",
                    ),
                ),
            ],
            options={"abstract": False,},
        ),
        migrations.CreateModel(
            name="Straight",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("bet_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "payout",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="straight_bets",
                        to="my_book.player",
                    ),
                ),
                (
                    "single_bet1",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="straight_bets",
                        to="my_book.singlebet",
                    ),
                ),
            ],
            options={"abstract": False,},
        ),
    ]

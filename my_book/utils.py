import plotly.graph_objs as go
import plotly.offline as opy
from django.db.models import Sum
from .models import Straight, Action, Parlay3, Parlay4


def generate_bet_type_comparison_graph():
    """
    This pie chart compares the number of each bet type
    """
    # Query the number of bets for each type
    straight_count = Straight.objects.count()
    action_count = Action.objects.count()
    parlay3_count = Parlay3.objects.count()
    parlay4_count = Parlay4.objects.count()
    total_count = straight_count + action_count + parlay3_count + parlay4_count

    # Prepare data for the pie chart
    labels = ["Straight", "Action", "Parlay3", "Parlay4"]
    values = [straight_count, action_count, parlay3_count, parlay4_count]

    # Create the pie chart
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                marker=dict(colors=["#636EFA", "#EF553B", "#00CC96", "#AB63FA"]),
                hole=0.3,  # Adds a hole in the middle to make it a donut chart
                textinfo="label+percent",  # Show percentage and label
            )
        ]
    )

    graph_title = f"Distribution of Bets by Type (Total Bets = {total_count})"

    fig.update_layout(
        title=graph_title,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black"),
    )

    # Render the graph as an HTML div
    graph_div = opy.plot(fig, auto_open=False, output_type="div")
    return graph_div


def generate_money_payout_comparison_graph():
    """
    this produces a bar graph showing the comparison between
    bet_amount and payout for each bet type
    """
    # Bet data grouped by type
    bet_data = {
        "Straight": Straight.objects.aggregate(
            total_amount=Sum("bet_amount"), total_payout=Sum("payout")
        ),
        "Action": Action.objects.aggregate(
            total_amount=Sum("bet_amount"), total_payout=Sum("payout")
        ),
        "Parlay3": Parlay3.objects.aggregate(
            total_amount=Sum("bet_amount"), total_payout=Sum("payout")
        ),
        "Parlay4": Parlay4.objects.aggregate(
            total_amount=Sum("bet_amount"), total_payout=Sum("payout")
        ),
    }

    total_bet_amount = sum([data["total_amount"] or 0 for data in bet_data.values()])
    total_payout = sum([data["total_payout"] or 0 for data in bet_data.values()])

    # Prepare data for the bar chart
    bet_types = list(bet_data.keys())
    bet_amounts = [data["total_amount"] or 0 for data in bet_data.values()]
    payouts = [data["total_payout"] or 0 for data in bet_data.values()]

    # Add "All Bet Types" data
    bet_types.append("All Bet Types")
    bet_amounts.append(total_bet_amount)
    payouts.append(total_payout)

    # Create the bar chart
    fig = go.Figure(
        data=[
            go.Bar(
                x=bet_types,
                y=bet_amounts,
                name="Bet Amount",
                marker=dict(color="#969297"),
                text=bet_amounts,  # Display values on bars
                textposition="outside",
            ),
            go.Bar(
                x=bet_types,
                y=payouts,
                name="Payout",
                marker=dict(color="#1DB954"),
                text=payouts,  # Display values on bars
                textposition="outside",
            ),
        ]
    )

    # Update layout for the bar chart
    fig.update_layout(
        title="Bet Amount vs Payout for Each Bet Type",
        barmode="group",
        xaxis_title="Bet Type",
        yaxis_title="Amount ($)",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black"),
        showlegend=True,
    )

    # Render graph
    graph_div = opy.plot(fig, auto_open=False, output_type="div")

    return graph_div

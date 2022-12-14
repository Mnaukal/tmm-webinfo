from collections import defaultdict
from typing import List
from flask import Blueprint
from sqlalchemy import func

from db_model import Puzzle, Team, TeamArrived, TeamSolved, TeamUsedHint, Hint, TeamSubmittedCode, Puzzlehunt
from helpers import render, admin_required, format_time

progress_table = Blueprint('progress_table', __name__, template_folder='templates', static_folder='static')


@progress_table.route('/progress')
@admin_required
def progress():
    puzzles = Puzzle.query.filter_by(id_puzzlehunt=Puzzlehunt.get_current_id()).order_by(Puzzle.order).all()
    teams = Team.query.filter_by(id_puzzlehunt=Puzzlehunt.get_current_id()).order_by(Team.name).all()
    team_ids = Team.query.filter_by(id_puzzlehunt=Puzzlehunt.get_current_id()).with_entities(Team.id_team)

    arrivals: List[TeamArrived] = TeamArrived.query\
        .filter(TeamArrived.id_team.in_(team_ids)).all()
    solves: List[TeamSolved] = TeamSolved.query\
        .filter(TeamSolved.id_team.in_(team_ids)).all()

    hints_used: List[int] = TeamUsedHint.query\
        .filter(TeamUsedHint.id_team.in_(team_ids))\
        .join(Hint)\
        .with_entities(TeamUsedHint.id_team, Hint.id_puzzle, func.count(Hint.id_hint))\
        .group_by(TeamUsedHint.id_team, Hint.id_puzzle)\
        .all()

    arrival_times = defaultdict(dict)
    for arrival in arrivals:
        arrival_times[arrival.id_team][arrival.id_puzzle] = format_time(arrival.timestamp)

    solve_times = defaultdict(dict)
    for solve in solves:
        solve_times[solve.id_team][solve.id_puzzle] = format_time(solve.timestamp)

    hints = defaultdict(lambda: defaultdict(int))
    for id_team, id_puzzle, hint_count in hints_used:
        hints[id_team][id_puzzle] = hint_count
        hints[id_team]["sum"] += hint_count

    puzzlehunt_settings = Puzzlehunt.get_current().get_settings()
    finish_times = {}
    if "finish_code" in puzzlehunt_settings:
        try:
            finish_code = int(puzzlehunt_settings["finish_code"].value)
            for finish in TeamSubmittedCode.query\
                    .filter_by(id_code=finish_code)\
                    .filter(TeamSubmittedCode.id_team.in_(team_ids)):
                finish_times[finish.id_team] = format_time(finish.timestamp)
        except ValueError:  # ignore if "finish_code" is not an int
            pass
    start_times = {}
    if "start_code" in puzzlehunt_settings:
        try:
            start_code = int(puzzlehunt_settings["start_code"].value)
            for start in TeamSubmittedCode.query \
                    .filter_by(id_code=start_code) \
                    .filter(TeamSubmittedCode.id_team.in_(team_ids)):
                start_times[start.id_team] = format_time(start.timestamp)
        except ValueError:  # ignore if "start_code" is not an int
            pass

    return render("progress_table.html", fluid=True, puzzles=puzzles, teams=teams,
                  arrival_times=arrival_times, solve_times=solve_times, hints=hints,
                  finish_times=finish_times, start_times=start_times)

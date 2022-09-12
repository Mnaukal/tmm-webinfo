from typing import List
from flask import request, redirect, Blueprint, flash
from flask_login import login_required, current_user

from db_model import Puzzle, TeamSolved, TeamArrived, ArrivalCode, SolutionCode, db, PuzzlePrerequisite
from helpers import render, get_current_puzzlehunt

journey = Blueprint('journey', __name__, template_folder='templates', static_folder='static')


@journey.route('/')
@login_required
def index():
    if current_user.is_admin:
        return redirect("/puzzlehunts")  # TODO: different page?

    team_solves_with_arrivals = TeamSolved.query\
        .filter_by(id_team=current_user.id_team)\
        .join(Puzzle)\
        .join(TeamArrived,
              (TeamSolved.id_puzzle == TeamArrived.id_puzzle) & (TeamSolved.id_team == TeamArrived.id_team))\
        .with_entities(TeamSolved, TeamArrived)\
        .all()
    team_arrivals = TeamArrived.query\
        .filter_by(id_team=current_user.id_team)\
        .join(Puzzle)\
        .filter(Puzzle.id_puzzle.not_in(
            TeamSolved.query
                .filter_by(id_team=current_user.id_team)
                .with_entities(TeamSolved.id_puzzle)))\
        .all()

    return render("index.html", solves=team_solves_with_arrivals, arrivals=team_arrivals)


@journey.route("/submit", methods=("POST",))
@login_required
def submit_code():
    code = request.form["code"]
    id_team = current_user.id_team

    solved_puzzles_ids_query = TeamSolved.query\
        .filter_by(id_team=id_team)\
        .with_entities(TeamSolved.id_puzzle)
    open_puzzles_ids_query = TeamArrived.query\
        .filter_by(id_team=id_team)\
        .filter(TeamArrived.id_puzzle.not_in(solved_puzzles_ids_query))\
        .with_entities(TeamArrived.id_puzzle)

    # check solutions for open puzzles
    open_puzzles_solution_codes: List[SolutionCode] = SolutionCode.query\
        .filter(SolutionCode.id_puzzle.in_(open_puzzles_ids_query))\
        .all()
    for solution in open_puzzles_solution_codes:
        if solution.code == code:
            team_solved = TeamSolved(id_team, solution.id_puzzle, solution.id_solution_code)
            db.session.add(team_solved)
            db.session.commit()
            flash(f'Řešení "{solution.code}" je správně.', "success")
            return redirect("/")

    # check arrival codes for not open puzzles
    not_open_puzzles_ids_query = Puzzle.query\
        .filter_by(id_puzzlehunt=get_current_puzzlehunt())\
        .filter(Puzzle.id_puzzle.not_in(open_puzzles_ids_query))\
        .filter(Puzzle.id_puzzle.not_in(solved_puzzles_ids_query))\
        .with_entities(Puzzle.id_puzzle)
    not_open_puzzles_codes: List[ArrivalCode] = ArrivalCode.query\
        .filter(ArrivalCode.id_puzzle.in_(not_open_puzzles_ids_query))\
        .all()
    for arrival in not_open_puzzles_codes:
        if arrival.code == code:
            prerequisites = PuzzlePrerequisite.query\
                .filter_by(id_new_puzzle=arrival.id_puzzle)\
                .with_entities(PuzzlePrerequisite.id_previous_puzzle)
            fulfilled_prerequisites = TeamSolved.query\
                .filter_by(id_team=id_team)\
                .filter(TeamSolved.id_puzzle.in_(prerequisites))
            if fulfilled_prerequisites.count() < prerequisites.count():
                flash(f'Nejdřív musíte vyřešit předchozí šifry.', "danger")
                return redirect("/")

            team_arrived = TeamArrived(id_team, arrival.id_puzzle, arrival.id_arrival_code)
            db.session.add(team_arrived)
            db.session.commit()
            flash(f'Kód stanoviště "{arrival.code}" je správný.', "success")
            return redirect("/")

    # TODO: check puzzlehunt global codes

    flash(f'Kód "{code}" není správný (nebo už byl zadán).', "danger")
    return redirect("/")

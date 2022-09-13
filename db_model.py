from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, backref

from abstract import Abstract

db = SQLAlchemy()
bcrypt = Bcrypt()


class Settings(db.Model):

    __tablename__ = "settings"

    key = db.Column(db.String(256), primary_key=True)
    value = db.Column(db.Text)

    def __init__(self, key):
        self.key = key


class Puzzlehunt(db.Model):

    __tablename__ = "puzzlehunts"

    id_puzzlehunt = db.Column(db.Integer, primary_key=True)
    puzzlehunt = db.Column(db.String(256))

    def __init__(self, puzzlehunt):
        self.puzzlehunt = puzzlehunt


class User(UserMixin, Abstract):

    __required_attributes__ = ["name"]

    @property
    def is_admin(self):
        return False

    @property
    def id(self):
        return


class Admin(User):

    @property
    def is_admin(self):
        return True

    @property
    def id(self):
        return -1

    name = "admin"


class Team(db.Model, User):

    __tablename__ = "teams"

    id_team = db.Column(db.Integer, primary_key=True)
    id_puzzlehunt = db.Column(db.Integer, db.ForeignKey(Puzzlehunt.id_puzzlehunt, ondelete='RESTRICT'))
    name = db.Column(db.String(256), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(256), nullable=True)
    note = db.Column(db.Text, nullable=True)

    @property
    def id(self):
        return self.id_team

    def __init__(self, current_puzzlehunt, name, password_plain, phone, note):
        self.id_puzzlehunt = current_puzzlehunt
        self.name = name
        self.set_password(password_plain)
        self.phone = phone
        self.note = note

    def set_password(self, password_plain):
        self.password = bcrypt.generate_password_hash(password_plain)


class Puzzle(db.Model):

    __tablename__ = "puzzles"

    id_puzzle = db.Column(db.Integer, primary_key=True)
    id_puzzlehunt = db.Column(db.Integer, db.ForeignKey(Puzzlehunt.id_puzzlehunt, ondelete='RESTRICT'))
    puzzle = db.Column(db.String(256))
    assignment = db.Column(db.Text)
    order = db.Column(db.Integer)

    def __init__(self, current_puzzlehunt, puzzle, assignment, order):
        self.id_puzzlehunt = current_puzzlehunt
        self.puzzle = puzzle
        self.assignment = assignment
        self.order = order

    def get_prerequisites(self):
        p = Puzzle.query.join(PuzzlePrerequisite, Puzzle.id_puzzle == PuzzlePrerequisite.id_previous_puzzle)\
            .filter_by(id_new_puzzle=self.id_puzzle).all()
        return p


class PuzzlePrerequisite(db.Model):

    __tablename__ = "puzzle_prerequisites"

    id_previous_puzzle = db.Column(db.Integer, db.ForeignKey(Puzzle.id_puzzle, ondelete='RESTRICT'), primary_key=True)
    id_new_puzzle = db.Column(db.Integer, db.ForeignKey(Puzzle.id_puzzle, ondelete='RESTRICT'), primary_key=True)

    def __init__(self, id_previous_puzzle, id_new_puzzle):
        self.id_previous_puzzle = id_previous_puzzle
        self.id_new_puzzle = id_new_puzzle


class Code(db.Model):

    __tablename__ = "codes"

    id_code = db.Column(db.Integer, primary_key=True)
    id_puzzlehunt = db.Column(db.Integer, db.ForeignKey(Puzzlehunt.id_puzzlehunt, ondelete='RESTRICT'))
    code = db.Column(db.String(256))
    message = db.Column(db.Text)

    def __init__(self, current_puzzlehunt, code, message):
        self.id_puzzlehunt = current_puzzlehunt
        self.code = code
        self.message = message


class ArrivalCode(db.Model):

    __tablename__ = "arrival_codes"

    id_arrival_code = db.Column(db.Integer, primary_key=True)
    id_puzzle = db.Column(db.Integer, db.ForeignKey(Puzzle.id_puzzle, ondelete='RESTRICT'))
    code = db.Column(db.String(256))
    message = db.Column(db.Text)

    puzzle = relationship("Puzzle", backref=backref("arrival_codes", uselist=False))

    def __init__(self, puzzle, code, message):
        self.id_puzzle = puzzle
        self.code = code
        self.message = message


class SolutionCode(db.Model):

    __tablename__ = "solution_codes"

    id_solution_code = db.Column(db.Integer, primary_key=True)
    id_puzzle = db.Column(db.Integer, db.ForeignKey(Puzzle.id_puzzle, ondelete='RESTRICT'))
    code = db.Column(db.String(256))
    message = db.Column(db.Text)

    puzzle = relationship("Puzzle", backref=backref("solution_codes", uselist=False))

    def __init__(self, puzzle, code, message):
        self.id_puzzle = puzzle
        self.code = code
        self.message = message


class HistoryEntry(Abstract):

    __required_attributes__ = ["icon_html", "history_entry_html", "edit_url"]


class TeamArrived(db.Model, HistoryEntry):

    __tablename__ = "team_arrivals"

    id_team = db.Column(db.Integer, db.ForeignKey(Team.id_team, ondelete='RESTRICT'), primary_key=True)
    id_puzzle = db.Column(db.Integer, db.ForeignKey(Puzzle.id_puzzle, ondelete='RESTRICT'), primary_key=True)
    id_arrival_code = db.Column(db.Integer, db.ForeignKey(ArrivalCode.id_arrival_code, ondelete='RESTRICT'))
    timestamp = db.Column(db.DateTime)

    puzzle = relationship("Puzzle", backref=backref("team_arrivals", uselist=False))
    arrival_code = relationship("ArrivalCode", backref=backref("team_arrivals", uselist=False))
    team = relationship("Team", backref=backref("team_arrivals", uselist=False))

    def __init__(self, id_team, id_puzzle, id_arrival_code):
        self.id_team = id_team
        self.id_puzzle = id_puzzle
        self.id_arrival_code = id_arrival_code
        self.timestamp = datetime.now()

    @property
    def icon_html(self):
        return '<i class="bi bi-file-earmark-richtext-fill text-info"></i>'

    @property
    def history_entry_html(self):
        return f'Příchod: {self.puzzle.puzzle}'

    @property
    def edit_url(self):
        return f'/history/{self.id_team}/arrival/{self.id_puzzle}'


class TeamSolved(db.Model, HistoryEntry):

    __tablename__ = "team_solves"

    id_team = db.Column(db.Integer, db.ForeignKey(Team.id_team, ondelete='RESTRICT'), primary_key=True)
    id_puzzle = db.Column(db.Integer, db.ForeignKey(Puzzle.id_puzzle, ondelete='RESTRICT'), primary_key=True)
    id_solution_code = db.Column(db.Integer, db.ForeignKey(SolutionCode.id_solution_code, ondelete='RESTRICT'))
    timestamp = db.Column(db.DateTime)

    puzzle = relationship("Puzzle", backref=backref("team_solves", uselist=False))
    solution_code = relationship("SolutionCode", backref=backref("team_solves", uselist=False))
    team = relationship("Team", backref=backref("team_solves", uselist=False))

    def __init__(self, id_team, id_puzzle, id_solution_code):
        self.id_team = id_team
        self.id_puzzle = id_puzzle
        self.id_solution_code = id_solution_code
        self.timestamp = datetime.now()

    @property
    def icon_html(self):
        return '<i class="bi bi-check-circle-fill text-success"></i>'

    @property
    def history_entry_html(self):
        return f'Vyřešeno: {self.puzzle.puzzle}'

    @property
    def edit_url(self):
        return f'/history/{self.id_team}/solve/{self.id_puzzle}'


class TeamSubmittedCode(db.Model, HistoryEntry):

    __tablename__ = "team_submitted_codes"

    id_team = db.Column(db.Integer, db.ForeignKey(Team.id_team, ondelete='RESTRICT'), primary_key=True)
    id_code = db.Column(db.Integer, db.ForeignKey(Code.id_code, ondelete='RESTRICT'), primary_key=True)
    timestamp = db.Column(db.DateTime)

    code = relationship("Code", backref=backref("team_submitted_codes", uselist=False))
    team = relationship("Team", backref=backref("team_submitted_codes", uselist=False))

    def __init__(self, id_team, id_code):
        self.id_team = id_team
        self.id_code = id_code
        self.timestamp = datetime.now()

    @property
    def icon_html(self):
        return '<i class="bi bi-file-earmark-code-fill text-primary"></i>'

    @property
    def history_entry_html(self):
        return f'Zadán kód: "{self.code.code}"'

    @property
    def edit_url(self):
        return f'/history/{self.id_team}/code/{self.id_code}'


class Hint(db.Model):

    __tablename__ = "hints"

    id_hint = db.Column(db.Integer, primary_key=True)
    id_puzzle = db.Column(db.Integer, db.ForeignKey(Puzzle.id_puzzle, ondelete='RESTRICT'))
    order = db.Column(db.Integer)
    minutes_to_open = db.Column(db.Integer)
    hint = db.Column(db.Text)

    puzzle = relationship("Puzzle", backref=backref("hints", uselist=False))

    def __init__(self, id_puzzle, order, minutes_to_open, hint):
        self.id_puzzle = id_puzzle
        self.order = order
        self.minutes_to_open = minutes_to_open
        self.hint = hint

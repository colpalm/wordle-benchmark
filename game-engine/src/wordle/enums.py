from enum import Enum


class LetterStatus(str, Enum):
    CORRECT = "correct"
    PRESENT = "present"
    ABSENT = "absent"


class GameStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"

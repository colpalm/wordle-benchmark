from enum import Enum


class LetterStatus(Enum):
    CORRECT = "correct"
    PRESENT = "present"
    ABSENT = "absent"

class GameStatus(Enum):
    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"
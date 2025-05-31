# Valid Word List Generation

## Overview

This project uses the SCOWL (Spell Checker Oriented Word Lists) public domain word list for Wordle validation, filtered to 5-letter words suitable for gameplay.
- SCOWL wordlist repo: https://github.com/en-wl/wordlist/tree/v2#

## Generate the Word List

### Prerequisites
- Clone the SCOWL repo: https://github.com/en-wl/wordlist/
- SCOWLv2 requires Python 3 and SQLite

### Steps
1. Build SCOWL database
    ```shell
    cd /path/to/wordlist
    make
    ``` 
2. Extract filtered words from a database
    ```shell
    ./scowl word-list scowl.db --size 90 --deaccent --apostrophe False --dot strip --spellings A --regions US > wl.txt 
    ```
3. Filter to valid 5-letter words
    ```shell
    ./python valid_word_generation.py
    ```
   - This generates a file called `wordle-valid-words.txt` which is used to check valid guesses in the game.
   - It also compares our generated SCOWL valid words to the NYT valid words and achieves ~75% coverage.
     - Note: NYT valid words not included in this repo.

### Configuration Choices
- Size 90: Includes common + semi-common + some uncommon words for robust coverage
- US English: American spellings only
- No apostrophes/accents: Clean alphabetic words only
- 5-letter filter: Wordle-specific requirement

## Legal Note
SCOWL is public domain, making it safe for personal/commercial use. This avoids potential copyright issues with proprietary word lists.
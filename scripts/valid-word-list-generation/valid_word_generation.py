
def filter_custom_wordle_words(input_file: str) -> set:
    """Filter SCOWL words for Wordle criteria - length == 5 and is alphabetical"""
    valid_words = set()

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip().upper()

                # Basic Wordle criteria
                if len(word) == 5 and word.isalpha():
                    valid_words.add(word)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        return set()

    print(f"Filtered {len(valid_words)} valid 5-letter words.")
    return valid_words

def write_custom_valid_words_to_file(valid_guesses: set, output_file: str) -> None:
    """Write valid SCOWL words to a file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for word in sorted(valid_guesses):
            f.write(word + '\n')

    print(f"Wrote {len(valid_guesses)} valid words to '{output_file}'.")


def inspect_wordle_words(valid_custom_wordle_words_file: str, nyt_valid_words: str, missing_words_output_file: str):
    """Compare our filtered words against NYT's official list"""

    try:
        # Load the custom SCOWL-filtered word list
        with open(valid_custom_wordle_words_file, 'r', encoding='utf-8') as f:
            wordle_scowl_words = set(word.strip() for word in f)

        # Load NYT List
        with open(nyt_valid_words, 'r', encoding='utf-8') as f:
            nyt_words = set(word.strip() for word in f)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    # Find words in the NYT list but not in the custom SCOWL filtered list
    missing_words = nyt_words - wordle_scowl_words

    # Find words in the custom SCOWL filtered list but not in the NYT list
    extra_words = wordle_scowl_words - nyt_words

    print(f"Our SCOWL-based words: {len(wordle_scowl_words)}")
    print(f"NYT official words: {len(nyt_words)}")
    print(f"Words in NYT but missing from ours: {len(missing_words)}")
    print(f"Words in ours but not in NYT: {len(extra_words)}")
    print(f"Overlap: {len(wordle_scowl_words & nyt_words)} words")

    write_missing_words_to_file(missing_words, extra_words, missing_words_output_file)

def write_missing_words_to_file(missing_nyt_words: set, extra_custom_words, output_file: str) -> None:
    """Write missing and extra words to a file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Words in NYT list but missing from our SCOWL-based filtered list:\n")
        for word in sorted(missing_nyt_words):
            f.write(word + '\n')

        f.write("\n# Words in our list but not in NYT:\n")
        for word in sorted(extra_custom_words):
            f.write(word + '\n')



if __name__ == "__main__":
    raw_scowl_word_list_file = 'wl.txt'
    valid_wordle_words = 'wordle-valid-words.txt'
    nyt_wordle_valid_words = 'nyt-valid-words.txt'

    # Main Logic
    valid_word_set = filter_custom_wordle_words(raw_scowl_word_list_file)
    write_custom_valid_words_to_file(valid_word_set, valid_wordle_words)

    # Compare with the official NYT list
    inspect_wordle_words(valid_wordle_words, nyt_wordle_valid_words, 'valid-word-differences.txt')
import requests
from datetime import datetime

def fetch_wordle_solution(date=None) -> str | None:
    """
    Fetches the Wordle solution for the given date (YYYY-MM-DD).
    If no date is provided, use today’s date.
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    url = f"https://www.nytimes.com/svc/wordle/v2/{date}.json"
    resp = requests.get(url)
    
    if resp.status_code == 200:
        data = resp.json()
        return data.get("solution")
    else:
        raise RuntimeError(f"Failed to fetch ({resp.status_code}): {resp.text}")

if __name__ == "__main__":
    try:
        solution = fetch_wordle_solution()
        print(f"Wordle solution for today ({datetime.now().date()}): {solution}")
    except Exception as e:
        print(f"Error: {e}")


import requests
import os
from pathlib import Path
from dotenv import load_dotenv


class AnimeClassifier:
    def __init__(self):
        self.ANIME_URL = "https://graphql.anilist.co"
        self.query = """
        query ($search: String) {
        Media(search: $search, type: ANIME) {
        id
        }
        }
        """

    def is_anime(self, title: str) -> bool:
        variables = {"search": title}

        response = requests.post(
            self.ANIME_URL,
            json={"query": self.query, "variables": variables},
            timeout=10,
        )

        if response.status_code != 200:
            return False  # network / API issue → fail safe

        data = response.json()

        return data.get("data", {}).get("Media") is not None


if __name__ == "__main__":
    pass

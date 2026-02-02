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


class MovieClassifierTMDb:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        load_dotenv(self.base_dir / ".env")
        self.TMDB_API_KEY = os.getenv("TMDB_API_KEY")
        self.TMDB_BASE = "https://api.themoviedb.org/3"

        if not self.TMDB_API_KEY:
            raise ValueError("TMDB_API_KEY not found in .env file")

        # Use a session for connection pooling and better performance
        self.session = requests.Session()
        # Add a real User-Agent to avoid being blocked by some APIs/firewalls
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )

    def search_movie(self, title: str) -> int | None:
        url = f"{self.TMDB_BASE}/search/movie"
        parms = {"api_key": self.TMDB_API_KEY, "query": title}

        try:
            r = self.session.get(url, params=parms, timeout=10)
            if r.status_code != 200:
                print(f"API Error {r.status_code}: {r.text}")
                return None

            results = r.json().get("results", [])
            return results[0].get("id") if results else None
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def movie_details(self, movie_id: int) -> dict | None:
        url = f"{self.TMDB_BASE}/movie/{movie_id}"
        parms = {
            "api_key": self.TMDB_API_KEY,
        }

        try:
            r = self.session.get(url, params=parms, timeout=10)
            if r.status_code != 200:
                print(f"API Error {r.status_code}: {r.text}")
                return None

            return r.json()
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

    @staticmethod
    def classify_movie(details: dict) -> str:
        countries = [c["iso_3166_1"] for c in details.get("production_countries", [])]

        language = details.get("original_language")

        if "IN" in countries:
            return "bollywood"

        if "US" in countries or language == "en":
            return "hollywood"

        return "other"

    def checker(self, title: str):
        movie_id = self.search_movie(title)
        if movie_id is None:
            return None
        details = self.movie_details(movie_id)
        if details is None:
            return None
        return self.classify_movie(details)


if __name__ == "__main__":
    classifer = MovieClassifierTMDb()
    anime_classifier = AnimeClassifier()
    # print(classifer.checker("Gadar 2"))
    print(anime_classifier.is_anime("Arrival"))

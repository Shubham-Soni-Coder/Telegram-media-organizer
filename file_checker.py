import requests
import os
from pathlib import Path
from dotenv import load_dotenv
import re
from difflib import SequenceMatcher


class AnimeClassifier:
    def __init__(self):
        self.ANIME_URL = "https://graphql.anilist.co"
        self.query = """
        query ($search: String) {
        Media(search: $search, type: ANIME) {
        id
        title {
            romaji
            english
            native
        }
        }
        }
        """

    def is_anime(self, title: str) -> bool:
        variables = {"search": title}

        try:
            response = requests.post(
                self.ANIME_URL,
                json={"query": self.query, "variables": variables},
                timeout=10,
            )

            if response.status_code != 200:
                return False

            data = response.json()
            media = data.get("data", {}).get("Media")

            if not media:
                return False

            # FIX: Verify title similarity
            found_titles = media.get("title", {})
            english = found_titles.get("english") or ""
            romaji = found_titles.get("romaji") or ""

            # Helper to check similarity
            def similar(a, b):
                return SequenceMatcher(None, a.lower(), b.lower()).ratio()

            # Check if either English or Romaji title is at least 40% similar to search
            if similar(title, english) > 0.4 or similar(title, romaji) > 0.4:
                return True

            return False

        except Exception:
            return False


class MovieClassifierTMDb:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        load_dotenv(self.base_dir / ".env")
        self.TMDB_API_KEY = os.getenv("TMDB_API_KEY")
        self.TMDB_BASE = "https://api.themoviedb.org/3"

        if not self.TMDB_API_KEY:
            raise ValueError("TMDB_API_KEY not found in .env file")

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )

    def search_movie(self, title: str) -> int | None:
        url = f"{self.TMDB_BASE}/search/movie"

        # FIX: Separation of Title and Year
        clean_title = title
        year = None

        # Matches "Name 2023" or "Name (2023)"
        match = re.search(r"^(.*?)\s*[\(\[]?(\d{4})[\)\]]?$", title)
        if match:
            clean_title = match.group(1).strip()
            year = match.group(2)

        parms = {"api_key": self.TMDB_API_KEY, "query": clean_title}
        if year:
            parms["year"] = year

        try:
            r = self.session.get(url, params=parms, timeout=10)
            if r.status_code != 200:
                return None

            results = r.json().get("results", [])
            return results[0].get("id") if results else None
        except requests.RequestException:
            return None

    def movie_details(self, movie_id: int) -> dict | None:
        url = f"{self.TMDB_BASE}/movie/{movie_id}"
        parms = {
            "api_key": self.TMDB_API_KEY,
        }

        try:
            r = self.session.get(url, params=parms, timeout=10)
            if r.status_code != 200:
                return None

            return r.json()
        except requests.RequestException:
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
    print(classifer.checker("Gadar 2 2023"))
    # print(anime_classifier.is_anime("Arrival 2023"))

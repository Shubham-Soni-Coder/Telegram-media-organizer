import re
import os
from pathlib import Path
import shutil


class FolderMaker:
    def __init__(self, destination_folder):
        self.destination_folder = Path(destination_folder)

        self.anime_folder = self.destination_folder / "anime" / "video"
        self.anime_movie_folder = self.destination_folder / "anime" / "movie"
        self.movie_folder = self.destination_folder / "movie"
        self.web_series = self.destination_folder / "web_series"

    def detect_media_type(self, title):
        """
        Reuturn : 'Tv' or 'movie'
        """
        tv_patterns = [
            r"S\d+\s*E\d+",  # S01E01
            r"S\d+\s*-\s*\d+",  # S01 - 01
            r"S\d+\s+\d+",  # S1 01  ← YOUR CASE
            r"\bEP?\s*\d+\b",  # EP01 / E01
        ]

        for pattern in tv_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                return "tv"

        return "movie"

    @staticmethod
    def parse_tv_title(title):
        """
        return: show_name, season_number, episode_number
        """

        patterns = [
            # S01E02, S1 E02
            r"^(.*?)[\s._-]*S(\d+)[\s._-]*E(\d+)",
            # E02, EP02 (no season)
            r"^(.*?)[\s._-]*(?:EP|E)(\d+)$",
        ]

        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                show_name = match.group(1).strip()

                if len(match.groups()) == 3:
                    season = int(match.group(2))
                    episode = int(match.group(3))
                else:
                    season = 1  # default season
                    episode = int(match.group(2))

                return show_name, season, episode

        raise ValueError(f"Invalid TV title format: {title}")

    def movie_target_path(self, file_path: Path, title: str):
        movie_dir = self.anime_movie_folder / title
        movie_dir.mkdir(parents=True, exist_ok=True)
        return movie_dir / (title + file_path.suffix)

    def tv_target_path(self, file_path: str, title: str):
        show_name, season_number = self.parse_tv_title(title)
        season_dir = self.anime_folder / show_name / f"Season {season_number}"
        season_dir.mkdir(parents=True, exist_ok=True)
        return season_dir / (title + file_path.suffix)

    @staticmethod
    def safe_move(src: Path, dst: Path):
        counter = 1
        final_dst = dst

        while final_dst.exists():
            final_dst = dst.with_stem(f"{dst.stem}_{counter}")
            counter += 1

        shutil.move(str(src), str(final_dst))
        print(f"[MOVED] {src.name} → {final_dst.name}")


if __name__ == "__main__":
    maker = FolderMaker("D:/")
    Path = Path("D:/downloads/telegrzm download/Monster S1 02.mkv")
    target = maker.tv_target_path(Path, "Monster S1 02.mkv")
    maker.safe_move(Path, target)

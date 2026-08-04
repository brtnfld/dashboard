import os
import pathlib
__all__ = [
    "gh_data_dir",
    "manager",
]


def gh_data_dir():
    """
    Returns the path to the GitHub data directory.
    """
    gh_data_path = os.environ.get("GITHUB_DATA")
    return pathlib.Path(gh_data_path) if gh_data_path else pathlib.Path(os.path.join(os.path.dirname(__file__), "..", "..", "..", "explore", "github-data"))

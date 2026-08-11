import os
import pathlib
from .manager import load_data, load_repo_list, load_input_lists, make_query_manager

__all__ = [
    "gh_data_dir",
    "gh_queries_dir",
    "load_data",
    "load_repo_list",
    "load_input_lists",
    "make_query_manager",
]


def gh_data_dir():
    """Returns the path to the GitHub data directory."""
    gh_data_path = os.environ.get("GITHUB_DATA")
    return pathlib.Path(gh_data_path) if gh_data_path else pathlib.Path(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "explore", "github-data")
    )


def gh_queries_dir():
    """Returns the path to the GQL queries directory."""
    return pathlib.Path(__file__).parent.parent / "queries"

from scraper.github import queryManager as qm
import os


def load_data(data_file: os.PathLike):
    """Load existing JSON data file, or initialize an empty {"data": {}} structure if missing."""
    collector = qm.DataManager(str(data_file), False)
    try:
        collector.fileLoad()
    except FileNotFoundError:
        collector.data = {"data": {}}
    if not isinstance(collector.data, dict) or "data" not in collector.data:
        collector.data = {"data": {}}
    return collector


def load_repo_list(gh_data_dir_path):
    """Return a sorted list of internal repo keys from intReposInfo.json."""
    repo_info = qm.DataManager(os.path.join(str(gh_data_dir_path), "intReposInfo.json"), True)
    print("Getting internal repos ...")
    repolist = sorted(repo_info.data["data"].keys())
    print("Repo list complete. Found %d repos." % len(repolist))
    return repolist


def load_input_lists(path=None):
    """Load and return the input_lists.json DataManager."""
    if path is None:
        path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "input_lists.json")
        )
    return qm.DataManager(path, True)


def make_query_manager(api_token=None):
    """Create and return a GitHubQueryManager."""
    if api_token is not None:
        return qm.GitHubQueryManager(apiToken=api_token)
    return qm.GitHubQueryManager()

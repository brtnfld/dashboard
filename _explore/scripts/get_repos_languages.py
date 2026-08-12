import sys
from gh_collector import gh_data_dir, gh_queries_dir, load_data, load_repo_list, make_query_manager

ghDataDir = gh_data_dir()
datfilepath = ghDataDir / "intRepos_Languages.json"
queryPath = str(gh_queries_dir() / "repo-Languages.gql")

repolist = load_repo_list(ghDataDir)
dataCollector = load_data(datfilepath)
queryMan = make_query_manager()

print("Gathering data across multiple paginated queries...")
failed = 0
for repo in repolist:
    print("\n'%s'" % (repo))

    r = repo.split("/")
    try:
        outObj = queryMan.queryGitHubFromFile(
            queryPath,
            {"ownName": r[0], "repoName": r[1], "numLangs": 25, "pgCursor": None},
            paginate=True,
            cursorVar="pgCursor",
            keysToList=["data", "repository", "languages", "nodes"],
        )
    except Exception as error:
        print("Warning: Could not complete '%s'" % (repo))
        print(error)
        failed += 1
        continue

    dataCollector.data["data"][repo] = outObj["data"]["repository"]

    print("'%s' Done!" % (repo))

print("\nCollective data gathering complete!")

if repolist and failed == len(repolist):
    sys.exit("All queries failed; refusing to overwrite data")

if failed == 0:
    print("Removing data for repos no longer in the list...")
    for repo in list(dataCollector.data["data"].keys()):
        if repo not in repolist:
            dataCollector.data["data"].pop(repo)
            print("Removed '%s'" % repo)

dataCollector.fileSave(newline="\n")

print("\nDone!\n")

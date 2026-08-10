from gh_collector import gh_data_dir, load_data, load_repo_list, make_query_manager

ghDataDir = gh_data_dir()
datfilepath = ghDataDir / "intRepos_Topics.json"
queryPath = "../queries/repo-Topics.gql"

repolist = load_repo_list(ghDataDir)
dataCollector = load_data(datfilepath)
queryMan = make_query_manager()

print("Gathering data across multiple paginated queries...")
for repo in repolist:
    print("\n'%s'" % (repo))

    r = repo.split("/")
    try:
        outObj = queryMan.queryGitHubFromFile(
            queryPath,
            {"ownName": r[0], "repoName": r[1], "numTopics": 25, "pgCursor": None},
            paginate=True,
            cursorVar="pgCursor",
            keysToList=["data", "repository", "repositoryTopics", "nodes"],
        )
    except Exception as error:
        print("Warning: Could not complete '%s'" % (repo))
        print(error)
        continue

    dataCollector.data["data"][repo] = outObj["data"]["repository"]

    print("'%s' Done!" % (repo))

print("\nCollective data gathering complete!")

dataCollector.fileSave(newline="\n")

print("\nDone!\n")

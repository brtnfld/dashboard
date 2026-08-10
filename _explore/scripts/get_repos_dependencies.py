from gh_collector import gh_data_dir, load_data, load_repo_list, make_query_manager

ghDataDir = gh_data_dir()
datfilepath = ghDataDir / "intRepos_Dependencies.json"
queryPath = "../queries/repo-Dependencies.gql"

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
            {
                "ownName": r[0],
                "repoName": r[1],
                "numManifests": 100,
                "numDependents": 100,
                "pgCursor": None,
            },
            paginate=True,
            cursorVar="pgCursor",
            keysToList=["data", "repository", "dependencyGraphManifests", "nodes"],
            headers={"Accept": "application/vnd.github.hawkgirl-preview+json"},
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

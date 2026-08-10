from scraper.github import queryManager as qm
from gh_collector import gh_data_dir, load_data, load_repo_list, make_query_manager

ghDataDir = gh_data_dir()
datfilepath = ghDataDir / "extRepos.json"
queryPath = "../queries/user-Repos.gql"

repolist = load_repo_list(ghDataDir)

# Read internal user data file (to use as member list)
inputLists = qm.DataManager(str(ghDataDir / "intUsers.json"), True)
print("Getting internal members ...")
memberlist = sorted(inputLists.data["data"].keys())
print("Member list complete. Found %d users." % (len(memberlist)))

# Load existing external repo data to preserve repo metadata across runs
dataCollector = load_data(datfilepath)

# Reset contributor lists so re-runs don't accumulate duplicates
for repoKey in dataCollector.data["data"]:
    dataCollector.data["data"][repoKey]["labContributors"] = {"nodes": []}

queryMan = make_query_manager()

print("Gathering data across multiple paginated queries...")
for usr in memberlist:
    print("\n'%s'" % (usr))

    try:
        outObj = queryMan.queryGitHubFromFile(
            queryPath,
            {"userName": usr, "numRepos": 50, "pgCursor": None},
            paginate=True,
            cursorVar="pgCursor",
            keysToList=["data", "user", "repositoriesContributedTo", "nodes"],
        )
    except Exception as error:
        print("Warning: Could not complete '%s'" % (usr))
        print(error)
        continue

    for repo in outObj["data"]["user"]["repositoriesContributedTo"]["nodes"]:
        repoKey = repo["nameWithOwner"]
        if repoKey in repolist:
            continue
        if repoKey not in dataCollector.data["data"]:
            dataCollector.data["data"][repoKey] = repo
            dataCollector.data["data"][repoKey]["labContributors"] = {"nodes": []}
        dataCollector.data["data"][repoKey]["labContributors"]["nodes"].append(usr)
        dataCollector.data["data"][repoKey]["labContributors"]["nodes"].sort()

    print("'%s' Done!" % (usr))

print("\nCollective data gathering complete!")

dataCollector.fileSave(newline="\n")

print("\nDone!\n")

import sys
from scraper.github import queryManager as qm
from gh_collector import gh_data_dir, gh_queries_dir, load_data, load_repo_list, make_query_manager

ghDataDir = gh_data_dir()
datfilepathExt = ghDataDir / "extUsers.json"
datfilepathInt = ghDataDir / "intUsers.json"
queryPath = str(gh_queries_dir() / "repo-Users.gql")

repolist = load_repo_list(ghDataDir)

# Internal users must already exist (written by get_internal_members.py)
dataCollectorInt = qm.DataManager(str(datfilepathInt), True)
memberlist = sorted(dataCollectorInt.data["data"].keys())
print("Member list complete. Found %d users." % (len(memberlist)))

# Load existing external user data to preserve profiles across runs
dataCollectorExt = load_data(datfilepathExt)

# Reset contribution lists so re-runs don't accumulate duplicates
for userKey in dataCollectorInt.data["data"]:
    dataCollectorInt.data["data"][userKey]["contributedLabRepositories"] = {"nodes": []}
for userKey in dataCollectorExt.data["data"]:
    dataCollectorExt.data["data"][userKey]["contributedLabRepositories"] = {"nodes": []}

queryMan = make_query_manager()

print("Gathering data across multiple paginated queries...")
failed = 0
for repo in repolist:
    print("\n'%s'" % (repo))

    r = repo.split("/")
    try:
        outObj = queryMan.queryGitHubFromFile(
            queryPath,
            {"ownName": r[0], "repoName": r[1], "numUsers": 50, "pgCursor": None},
            paginate=True,
            cursorVar="pgCursor",
            keysToList=["data", "repository", "mentionableUsers", "nodes"],
        )
    except Exception as error:
        print("Warning: Could not complete '%s'" % (repo))
        print(error)
        failed += 1
        continue

    for user in outObj["data"]["repository"]["mentionableUsers"]["nodes"]:
        userKey = user["login"]
        if userKey in memberlist:
            dataCollectorInt.data["data"][userKey]["contributedLabRepositories"][
                "nodes"
            ].append(repo)
            dataCollectorInt.data["data"][userKey]["contributedLabRepositories"][
                "nodes"
            ].sort()
        else:
            if userKey not in dataCollectorExt.data["data"]:
                dataCollectorExt.data["data"][userKey] = user
                dataCollectorExt.data["data"][userKey]["contributedLabRepositories"] = {
                    "nodes": []
                }
            dataCollectorExt.data["data"][userKey]["contributedLabRepositories"][
                "nodes"
            ].append(repo)
            dataCollectorExt.data["data"][userKey]["contributedLabRepositories"][
                "nodes"
            ].sort()

    print("'%s' Done!" % (repo))

print("\nCollective data gathering complete!")

if repolist and failed == len(repolist):
    sys.exit("All queries failed; refusing to overwrite data")

dataCollectorExt.fileSave(newline="\n")
dataCollectorInt.fileSave(newline="\n")

print("\nDone!\n")

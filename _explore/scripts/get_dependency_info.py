import sys
from scraper.github import queryManager as qm
from gh_collector import gh_data_dir, gh_queries_dir, load_data, make_query_manager

ghDataDir = gh_data_dir()
datfilepath = ghDataDir / "dependencyInfo.json"
queryPath = str(gh_queries_dir() / "dependency-Info.gql")

# Build repo list from the dependency manifests data file
inputLists = qm.DataManager(str(ghDataDir / "intRepos_Dependencies.json"), True)
print("Getting dependency repos ...")
repolist = []
for repoName in inputLists.data["data"]:
    for node in inputLists.data["data"][repoName]["dependencyGraphManifests"]["nodes"]:
        for repo in node["dependencies"]["nodes"]:
            if (
                repo["repository"] is not None
                and repo["repository"]["nameWithOwner"] is not None
            ):
                repolist.append(repo["repository"]["nameWithOwner"])
repolist = sorted(set(repolist))
print("Repo list complete. Found %d repos." % (len(repolist)))

dataCollector = load_data(datfilepath)
queryMan = make_query_manager()

print("Gathering data across multiple queries...")
failed = 0
for repo in repolist:
    print("\n'%s'" % (repo))

    r = repo.split("/")
    try:
        outObj = queryMan.queryGitHubFromFile(
            queryPath,
            {
                "ownName": r[0],
                "repoName": r[1],
            },
            headers={"Accept": "application/vnd.github.hawkgirl-preview+json"},
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

dataCollector.fileSave(newline="\n")

print("\nDone!\n")

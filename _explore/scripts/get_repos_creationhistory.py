import sys
from scraper.github import queryManager as qm
from gh_collector import gh_data_dir, load_data, load_repo_list, make_query_manager
import re

ghDataDir = gh_data_dir()
datfilepath = ghDataDir / "intRepos_CreationHistory.json"
query_commits_in = "/repos/OWNNAME/REPONAME/commits?until=CREATETIME&per_page=100"
query_commits_in2 = "/repos/OWNNAME/REPONAME/commits?per_page=100"

# Load existing data — history doesn't change, so we only query new or incomplete repos
inputLists = qm.DataManager(str(ghDataDir / "intReposInfo.json"), True)
repolist = load_repo_list(ghDataDir)
dataCollector = load_data(datfilepath)
queryMan = make_query_manager()

print("Gathering data across multiple paginated queries...")
attempted = 0
succeeded = 0
for repo in repolist:
    print("\n'%s'" % (repo))

    if repo in dataCollector.data["data"]:
        if dataCollector.data["data"][repo]["firstCommitAt"]:
            print("Already recorded data for '%s'" % (repo))
            continue

    attempted += 1
    repoData = {}
    r = repo.split("/")

    print("Part 1)  Get creation date...")
    repoData = {"createdAt": inputLists.data["data"][repo]["createdAt"]}

    print("Part 2)  Get pre-GitHub commit timestamps...")

    gitquery2 = re.sub("OWNNAME", r[0], query_commits_in)
    gitquery2 = re.sub("REPONAME", r[1], gitquery2)
    gitquery2 = re.sub("CREATETIME", repoData["createdAt"], gitquery2)

    try:
        outObj2 = queryMan.queryGitHub(gitquery2, rest=True, paginate=True)
    except Exception as error:
        print("Could not complete '%s'" % (repo))
        print(error)

    repoData["commitTimestamps"] = []
    try:
        for commit in outObj2:
            repoData["commitTimestamps"].append(commit["commit"]["committer"]["date"])
    except NameError:
        print("Could not get pre-GitHub commits for '%s'" % (repo))

    if len(repoData["commitTimestamps"]) > 0 and repoData["commitTimestamps"][0]:
        repoData["initBeforeGitHubRepo"] = True
    else:
        repoData["initBeforeGitHubRepo"] = False

        print("Part 3)  No pre-GitHub commits found, getting full history...")

        gitquery3 = re.sub("OWNNAME", r[0], query_commits_in2)
        gitquery3 = re.sub("REPONAME", r[1], gitquery3)

        try:
            outObj3 = queryMan.queryGitHub(gitquery3, rest=True, paginate=True)
        except Exception as error:
            print("Warning: Could not complete '%s'" % (repo))
            print(error)

        try:
            for commit in outObj3:
                repoData["commitTimestamps"].append(
                    commit["commit"]["committer"]["date"]
                )
        except NameError:
            print("Could not get any commits for '%s'." % (repo))
            continue

    repoData["commitTimestamps"].sort()
    firstdate = None
    if len(repoData["commitTimestamps"]) > 0:
        firstdate = repoData["commitTimestamps"][0]
    repoData["firstCommitAt"] = firstdate
    del repoData["commitTimestamps"]

    dataCollector.data["data"][repo] = repoData
    succeeded += 1

    print("'%s' Done!" % (repo))

print("\nCollective data gathering complete!")

if attempted > 0 and succeeded == 0:
    sys.exit("All queries failed; refusing to overwrite data")

# Remove any data for repos no longer in the list
print("Deleting unwanted data (from unlisted repos)...")
for repo in list(dataCollector.data["data"].keys()):
    if repo not in repolist:
        dataCollector.data["data"].pop(repo, None)
        print("Removed '%s'" % (repo))

dataCollector.fileSave(newline="\n")

print("\nDone!\n")

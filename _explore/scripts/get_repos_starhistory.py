import sys
from gh_collector import gh_data_dir, gh_queries_dir, load_data, load_repo_list, make_query_manager
from datetime import date, timedelta

ghDataDir = gh_data_dir()
datfilepath = ghDataDir / "intRepos_StarHistory.json"
queryPath = str(gh_queries_dir() / "repo-Stargazers.gql")

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
            {"ownName": r[0], "repoName": r[1], "numUsers": 100, "pgCursor": None},
            paginate=True,
            cursorVar="pgCursor",
            keysToList=["data", "repository", "stargazers", "edges"],
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


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return d + timedelta(days_ahead)


def toDate(isoStr):
    return next_weekday(date.fromisoformat(isoStr["starredAt"].split("T")[0]), 0)


for repo in dataCollector.data["data"]:
    dateRange = list(
        map(toDate, dataCollector.data["data"][repo]["stargazers"]["edges"])
    )
    dateList = []
    dateElement = {"date": None, "value": None}
    for dateEntry in dateRange:
        if dateElement["date"] is None:
            dateElement["date"] = dateEntry.isoformat()
            dateElement["value"] = 1
        elif dateElement["date"] == dateEntry.isoformat():
            dateElement["value"] += 1
        else:
            dateList.append(dateElement.copy())
            dateElement["date"] = dateEntry.isoformat()
            dateElement["value"] = 1
    dataCollector.data["data"][repo] = dateList

dataCollector.fileSave(newline="\n")

print("\nDone!\n")

from gh_collector import gh_data_dir, load_data, load_repo_list, make_query_manager
import re
from datetime import datetime

ghDataDir = gh_data_dir()
datfilepath = ghDataDir / "intRepos_ActivityCommits.json"
query_in = "/repos/OWNNAME/REPONAME/stats/commit_activity"

repolist = load_repo_list(ghDataDir)
dataCollector = load_data(datfilepath)
queryMan = make_query_manager()

print("Gathering data across multiple queries...")
for repo in repolist:
    print("\n'%s'" % (repo))

    r = repo.split("/")

    gitquery = re.sub("OWNNAME", r[0], query_in)
    gitquery = re.sub("REPONAME", r[1], gitquery)

    try:
        outObj = queryMan.queryGitHub(gitquery, rest=True)
    except Exception as error:
        print("Warning: Could not complete '%s'" % (repo))
        print(error)
        continue

    for item in outObj:
        try:
            del item["days"]
        except KeyError:
            pass
        weekinfo = datetime.utcfromtimestamp(item["week"]).isocalendar()
        weekstring = str(weekinfo[0]) + "-W" + str(weekinfo[1]) + "-1"
        item["week"] = datetime.strptime(weekstring, "%Y-W%W-%w").strftime("%Y-%m-%d")

    dataCollector.data["data"][repo] = outObj

    print("'%s' Done!" % (repo))

print("\nCollective data gathering complete!")

dataCollector.fileSave(newline="\n")

print("\nDone!\n")

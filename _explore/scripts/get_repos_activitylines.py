from gh_collector import gh_data_dir, load_data, load_repo_list, make_query_manager
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta

ghDataDir = gh_data_dir()
datfilepath = ghDataDir / "intRepos_ActivityLines.json"
query_in = "/repos/OWNNAME/REPONAME/stats/code_frequency"

repolist = load_repo_list(ghDataDir)
dataCollector = load_data(datfilepath)
queryMan = make_query_manager()

cutoffStamp = int((datetime.now() - relativedelta(years=1)).timestamp())

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

    outObj = list(filter(lambda x: x[0] > cutoffStamp, outObj))

    for item in outObj:
        weekinfo = datetime.utcfromtimestamp(item[0]).isocalendar()
        weekstring = str(weekinfo[0]) + "-W" + str(weekinfo[1]) + "-1"
        item[0] = datetime.strptime(weekstring, "%Y-W%W-%w").strftime("%Y-%m-%d")

    dataCollector.data["data"][repo] = outObj

    print("'%s' Done!" % (repo))

print("\nCollective data gathering complete!")

dataCollector.fileSave(newline="\n")

print("\nDone!\n")

from scraper.github import queryManager as qm
from os import environ as env
import sys
from gh_collector import gh_data_dir, load_data, load_input_lists

ghDataDir = gh_data_dir()
datfilepath = ghDataDir / "intUsers.json"
queryPath = "../queries/org-Members.gql"

dataCollector = load_data(datfilepath)

inputLists = load_input_lists()
for hostUrl, hostInfo in inputLists.data.items():
    repoType = hostInfo["repoType"]
    # TODO REMOVE CONTINUE once gitlab scraper is ready
    if repoType == "gitlab" or repoType == "bitbucket":
        print("%s: %s support not yet enabled, skipping for now" % (hostUrl, repoType))
        continue
    if repoType != "github":
        print("%s: Invalid repo type %s" % (hostUrl, repoType))
        sys.exit(1)

    orglist = hostInfo["memberOrgs"]

    '''
    TODO we will soon want to do a couple of things:
    1. The type of the "queryMan" object should be determined by the "repoType" string (i.e. GitlabQueryManger)
    2. We will need to pass in "hostUrl" as an eventual constructor argument
    3. Make all functions abstract in the base class for easier typing
    '''
    queryMan = qm.GitHubQueryManager(apiToken=env.get(hostInfo["apiEnvKey"]))

    print("%s: Gathering data across multiple paginated queries..." % (hostUrl))
    for org in orglist:
        print("\n'%s'" % (org))

        try:
            outObj = queryMan.queryGitHubFromFile(
                queryPath,
                {"orgName": org, "numUsers": 50, "pgCursor": None},
                paginate=True,
                cursorVar="pgCursor",
                keysToList=["data", "organization", "membersWithRole", "nodes"],
            )
        except Exception as error:
            print("Warning: Could not complete '%s'" % (org))
            print(error)
            continue

        for user in outObj["data"]["organization"]["membersWithRole"]["nodes"]:
            userKey = user["login"]
            dataCollector.data["data"][userKey] = user

        print("'%s' Done!" % (org))

    print("\n%s: Collective data gathering complete!" % (hostUrl))

dataCollector.fileSave(newline="\n")

print("\nDone!\n")

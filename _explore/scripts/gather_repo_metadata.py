from scraper.github import queryManager as qm
from gh_collector import gh_data_dir

ghDataDir = gh_data_dir()
genDatafile = ghDataDir / "intReposInfo.json"
topicsDatafile = ghDataDir / "intRepos_Topics.json"
writeFile = ghDataDir / "intRepo_Metadata.json"

# initialize data manager and load repo info
genDataCollector = qm.DataManager(str(genDatafile), True)

# initialize data manager and load repo topics
topicsCollector = qm.DataManager(str(topicsDatafile), True)

# initialize data manager to write collected info
infoWriter = qm.DataManager(str(writeFile), False)

print("\nGathering repo metadata...\n")

for repo in genDataCollector.data["data"]:

    repoData = {}

    repoObj = genDataCollector.data["data"][repo]

    repoData["name"] = repo
    repoData["description"] = repoObj.get("description")
    repoData["website"] = repoObj.get("homepageUrl")

    topicRepo = topicsCollector.data["data"].get(repo)
    if repoObj.get("repositoryTopics") and repoObj["repositoryTopics"]["totalCount"] > 0 and topicRepo:
        topics = []
        for topicObj in topicRepo["repositoryTopics"]["nodes"]:
            topics.append(topicObj["topic"]["name"])
        repoData["topics"] = topics
    else:
        repoData["topics"] = None

    infoWriter.data[repo] = repoData

infoWriter.fileSave(newline="\n")

print("\nDone!\n")

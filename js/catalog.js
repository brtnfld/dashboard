/** GLOBALS */
// GiHub Data Directory
var ghDataDir = '../explore/github-data';
// Global chart standards
var stdTotalWidth = 500,
  stdTotalHeight = 400;
var stdMargin = { top: 40, right: 40, bottom: 40, left: 40 },
  stdWidth = stdTotalWidth - stdMargin.left - stdMargin.right,
  stdHeight = stdTotalHeight - stdMargin.top - stdMargin.bottom,
  stdMaxBuffer = 1.07;
var stdDotRadius = 4,
  stdLgndDotRadius = 5,
  stdLgndSpacing = 20;

/** ELEMENTS */

const HIDDEN_CLASS = 'hidden';

const REPO_SECTION_ELEMENT = document.getElementById('repositories');
const ELEMENT_NAV_DESKTOP = document.getElementById('category-nav');
const ELEMENT_NAV_MOBILE = document.getElementById('category-hamburger-nav');
const REPO_HEADER_ELEMENT = document.getElementById('category-header');
const ELEMENT_WELCOME_TEXT = document.getElementById('welcome-text');

const ELEMENT_SEARCH = document.getElementById('searchText');

const ELEMENT_SINGLE_REPO_TARGET = document.getElementById('catalog-repo-single');

const ELEMENTS_ONLY_LIST = document.querySelectorAll('.catalog-list-only');
const ELEMENTS_ONLY_SINGLE_REPO = document.querySelectorAll('.catalog-single-only');

/** STATE VARIABLES */

//let searchTimeout; // TODO uncomment debounce once we have enough data
/**
 * Value of the text field which is visible on the category list view.
 */
let filterText = '';
/**
 * Value of the dropdown which is visible on the category list view.
 *
 * if this starts with a '-', reverse the sort order
 */
let orderProp = 'name';
/**
 * Index of the active category from the catData array, relevant for showing visible repositories on the category list view.
 *
 * This value will also be tracked in the URL, but as the category's "urlParam".
 */
let selectedCategoryIndex = 0;
/**
 * Value of the visible repository. Also gets tracked in the URL.
 *
 * If this is an empty string or nullish - show category list view. Otherwise, show repository detail view
 */
let visibleRepo = '';
/**
 * category data which gets populated from an initial fetch. the first item is a hardcoded value meant to represent no filter
 */
const catData = [
  {
    title: 'ALL SOFTWARE',
    icon: {
      path: '/assets/images/categories/catalog.svg', // don't use baseUrl here, we'll add it in the src of the img tag
      alt: 'All Software',
    },
    description: {
      short: `Browse all ${window.config.labName} open source projects`,
      long: '',
    },
    displayTitle: 'All Software',
    urlParam: 'all',
    topics: [],
  },
];
/**
 * Mapping of repositories to topics
 */
const topicRepos = [];
/**
 * flag which will permanently be set to "true" once user visits category list page
 */
let hasUserVisitedCategoryListPageYet = false;

/////////////////////////////////////////////////////////
//////////// UTIL FUNCTIONS ////////////////////////////
/////////////////////////////////////////////////////////

/**
 *
 * @param {String} str provided string
 * @returns string with first character of each word capitalized
 */
function titleCase(str) {
  return str
    .toLowerCase()
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

//check if repo is tagged as one of the categories
function containsTopics(catTopics, repoTopics) {
  if (!catTopics.length) return true;
  for (let i = 0; i < catTopics.length; i++) {
    if (repoTopics.includes(catTopics[i])) {
      return true;
    }
  }
  return false;
}

//////////////////////////////////////////////////////////
///////////////// REPO DETAIL FUNCTIONS //////////////////
//////////////////////////////////////////////////////////

/**
 * @param {string|null|undefined} queryParam parameter which may have been decoded from URL query parameter (or may not exist)
 */
function renderSingleRepoError(queryParam) {
  ELEMENT_SINGLE_REPO_TARGET.innerHTML = `
    <h2><span class="fa fa-exclamation-circle"></span> Whoops...</h2>
    <p>${
      queryParam ? `The repository ${queryParam} is not in our catalog.` : 'No repository specified in the URL (i.e. "?category=&repo=").'
    }</p>
  `;
}

/**
 * @param {Object} repo repo property from intReposInfo.json
 * @param {number} pulls count of all pull requests (open + closed)
 * @param {number} issues count of all issues (open + closed)
 */
function renderSingleRepoHTML(repo, pulls, issues) {
  ELEMENT_SINGLE_REPO_TARGET.innerHTML = `
    <h2 class="page-header text-center">
      <a class="title" href="${repo.url}" title="View Project on GitHub">${sanitizeHTML(repo.name)}</a>
      <br />
      <a class="subtitle" href="https://github.com/${repo.owner.login}" title="View Owner on GitHub">
        <span class="fa fa-user-circle"></span>${repo.owner.login}
      </a>
      ${
        repo.primaryLanguage
          ? `
        <span class="subtitle" title="Primary Language">
          <span class="fa fa-code"></span>
          ${repo.primaryLanguage.name}
        </span>
      `
          : ''
      }
      ${
        repo.licenseInfo && repo.licenseInfo.spdxId !== 'NOASSERTION'
          ? `
        <a
          class="subtitle"
          href="${repo.licenseInfo.url}"
          title="${repo.licenseInfo.name}"
        >
          <span class="fa fa-balance-scale"></span>
          ${repo.licenseInfo.spdxId}
        </a>
      `
          : ''
      }
    </h2>

    <p class="stats text-center">
      <a href="${repo.url}"> <span class="fa fa-github"></span>GitHub Page </a>

      <a href="${repo.url}/stargazers"> <span class="fa fa-star"></span>Community Interest: ${repo.stargazers.totalCount} stars</a>

      <a href="${repo.url}/network"> <span class="fa fa-code-fork"></span>Forks: ${repo.forks.totalCount} </a>

      ${
        repo.cdash
          ? `
          <a href="${repo.cdash}"> <img src="${window.config.baseUrl}/assets/images/logos/cdash.svg" height="20" width="20" class="cdash-icon"></img>CDash Dashboard </a>
      `
          : ''
      }

      ${
        repo.homepageUrl
          ? `
        <a href="${repo.homepageUrl}"> <span class="fa fa-globe"></span>Project Website </a>
      `
          : ''
      }
    </p>
    ${
      repo.description
        ? `
      <blockquote cite="${repo.url}"> ${sanitizeHTML(repo.description)} </blockquote>
    `
        : ''
    }

    <div class="text-center">
      <h3>Project Activity</h3>
      <svg class="repoActivityChart"></svg>
      <br />
      <h3>Contributors</h3>
      <svg class="pieUsers"></svg>
      <br />
      ${pulls ? '<h3>Pull Requests</h3><svg class="piePulls"></svg><br />' : ''}
      ${issues ? '<h3>Issues</h3><svg class="pieIssues"></svg><br />' : ''}
      <h3>Repository Timeline</h3>
      <svg class="repoCreationHistory"></svg>
      <br />
      ${repo.stargazers.totalCount ? '<h3>Star History</h3><svg class="repoStarHistory"></svg><br />' : ''}
      ${repo.languages.totalCount ? '<h3>Languages Used</h3><svg class="languagePie"></svg><br />' : ''}
      ${repo.repositoryTopics.totalCount ? '<h3>Topics</h3><svg class="topicCloud"></svg>' : ''}

      <div id="metrics-section"></div>
    </div>
  `;
}

/**
 *
 * @param {string} queryParam parameter which was decoded from URL query parameter
 */
function renderSingleRepo(queryParam) {
  fetch(`${window.config.baseUrl}/explore/github-data/intReposInfo.json`)
    .then((res) => res.json())
    .then((infoJson) => {
      const reposObj = infoJson.data;
      if (reposObj.hasOwnProperty(queryParam)) {
        const repo = reposObj[queryParam];
        let pulls = 0;
        let issues = 0;
        const pullCounters = ['pullRequests_Merged', 'pullRequests_Open'];
        const issueCounters = ['issues_Closed', 'issues_Open'];
        pullCounters.forEach(function (c) {
          pulls += repo[c]['totalCount'];
        });
        issueCounters.forEach(function (c) {
          issues += repo[c]['totalCount'];
        });
        renderSingleRepoHTML(repo, pulls, issues);
        draw_line_repoActivity('repoActivityChart', queryParam);
        draw_pie_repoUsers('pieUsers', queryParam);
        draw_line_repoCreationHistory('repoCreationHistory', queryParam);
        draw_pie_languages('languagePie', queryParam);
        draw_cloud_topics('topicCloud', queryParam);
        if (repo.stargazers.totalCount) {
          draw_line_repoStarHistory('repoStarHistory', queryParam);
        }
        if (pulls) {
          draw_pie_repoPulls('piePulls', queryParam);
        }
        if (issues) {
          draw_pie_repoIssues('pieIssues', queryParam);
        }
        // Load and display sustainability metrics
        loadSustainabilityMetrics(queryParam);
      } else {
        renderSingleRepoError(queryParam);
      }
    });
}

/**
 * Load and display sustainability metrics for a repository
 * @param {string} repoName repository name (owner/repo format)
 */
function loadSustainabilityMetrics(repoName) {
  fetch(`${window.config.baseUrl}/explore/github-data/sustainabilityMetrics.json`)
    .then((res) => res.json())
    .then((metricsData) => {
      if (metricsData.hasOwnProperty(repoName)) {
        renderSustainabilityMetrics(metricsData[repoName]);
      } else {
        // No metrics available for this repo
        document.getElementById('metrics-section').innerHTML = '';
      }
    })
    .catch((error) => {
      console.log('Sustainability metrics not available:', error);
      document.getElementById('metrics-section').innerHTML = '';
    });
}

/**
 * Render sustainability metrics HTML
 * @param {Object} metrics metrics data for the repository
 */
function renderSustainabilityMetrics(metrics) {
  const metricsSection = document.getElementById('metrics-section');

  metricsSection.innerHTML = `
    <h3>Sustainability Metrics</h3>
    <div class="sustainability-overview">
      <div class="metric-score-card">
        <h4>Overall Sustainability Score</h4>
        <div class="score-circle">
          <span class="score-value">${metrics.overall_score}/100</span>
        </div>
        <p class="score-label">${getScoreLabel(metrics.overall_score)}</p>
      </div>
    </div>

    <div class="metrics-grid">
      <!-- Impact Metrics -->
      <div class="metric-category">
        <h4><span class="fa fa-graduation-cap"></span> Research Impact</h4>
        <div class="metric-item">
          <span class="metric-label">Citation Score:</span>
          <span class="metric-value">${metrics.impact_metrics.citation_score.toFixed(1)}/100</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">Formal Citations:</span>
          <span class="metric-value">${metrics.impact_metrics.formal_citations.toLocaleString()}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">Paper Mentions:</span>
          <span class="metric-value">${metrics.impact_metrics.informal_mentions.toLocaleString()}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">Dependent Packages:</span>
          <span class="metric-value">${metrics.impact_metrics.dependent_packages.toLocaleString()}</span>
        </div>
        ${metrics.impact_metrics.doi_resolutions > 0 ? `
        <div class="metric-item">
          <span class="metric-label">DOI Resolutions:</span>
          <span class="metric-value">${metrics.impact_metrics.doi_resolutions.toLocaleString()}</span>
        </div>
        ` : ''}
      </div>

      <!-- Community Metrics -->
      <div class="metric-category">
        <h4><span class="fa fa-users"></span> Community Health</h4>
        <div class="metric-item">
          <span class="metric-label">Total Contributors:</span>
          <span class="metric-value">${metrics.community_metrics.total_contributors}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">Active (30 days):</span>
          <span class="metric-value">${metrics.community_metrics.active_contributors_30d}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">Commits/Month:</span>
          <span class="metric-value">${metrics.community_metrics.commit_frequency_per_month.toFixed(1)}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">Avg Issue Response:</span>
          <span class="metric-value">${metrics.community_metrics.avg_issue_response_days.toFixed(1)} days</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">Avg PR Merge Time:</span>
          <span class="metric-value">${metrics.community_metrics.avg_pr_merge_days.toFixed(1)} days</span>
        </div>
      </div>

      <!-- Licensing Metrics -->
      <div class="metric-category">
        <h4><span class="fa fa-balance-scale"></span> Licensing</h4>
        <div class="metric-item">
          <span class="metric-label">License:</span>
          <span class="metric-value">${metrics.licensing_metrics.license}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">Compatibility:</span>
          <span class="metric-value compatibility-${metrics.licensing_metrics.license_compatibility}">${metrics.licensing_metrics.license_compatibility}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">Clarity Score:</span>
          <span class="metric-value">${metrics.licensing_metrics.license_clarity_score}/100</span>
        </div>
        ${metrics.licensing_metrics.outbound_licenses.length > 0 ? `
        <div class="metric-item">
          <span class="metric-label">Dependencies:</span>
          <span class="metric-value">${metrics.licensing_metrics.outbound_licenses.join(', ')}</span>
        </div>
        ` : ''}
      </div>
    </div>

    <p class="metrics-updated">Last updated: ${new Date(metrics.last_updated).toLocaleDateString()}</p>
  `;
}

/**
 * Get descriptive label for sustainability score
 * @param {number} score score value (0-100)
 * @returns {string} descriptive label
 */
function getScoreLabel(score) {
  if (score >= 80) return 'Excellent';
  if (score >= 60) return 'Good';
  if (score >= 40) return 'Fair';
  if (score >= 20) return 'Needs Improvement';
  return 'Limited Data';
}

/////////////////////////////////////////////////////////
//////////// REPO LIST RENDER FUNCTIONS /////////////
/////////////////////////////////////////////////////////

function renderRepoListHeaderHtml() {
  // selectedCategoryIndex will be set to a valid number on initialization
  const category = catData[selectedCategoryIndex];
  REPO_HEADER_ELEMENT.innerHTML = `
    <img
      src="${window.config.baseUrl}${category.icon.path}"
      width="125"
      height="125"
      alt="${category.icon.alt}"
      title="${category.icon.alt}"
      loading="lazy"
    />
    <div class="title-description">
      <h2>${category.title}</h2>
      <p>${category.description.short}${category.description.long}</p>
    </div>
  `;
}

function renderRepoListHtml() {
  const isOrderReversed = orderProp.startsWith('-');
  const resolvedOrderProp = isOrderReversed ? orderProp.slice(1) : orderProp;
  // Safety check: ensure topicRepos array exists for this category
  if (!topicRepos[selectedCategoryIndex] || !Array.isArray(topicRepos[selectedCategoryIndex])) {
    console.error(`topicRepos[${selectedCategoryIndex}] is not valid`, topicRepos[selectedCategoryIndex]);
    REPO_SECTION_ELEMENT.innerHTML = '<p>Error loading repositories for this category.</p>';
    return;
  }
  const items = topicRepos[selectedCategoryIndex]
    .filter((repo) => {
      // Filter out repos that haven't been fully populated yet
      if (!repo.name || !repo.owner) {
        return false;
      }
      // If there's no filter text, include all repos
      if (!filterText) {
        return true;
      }
      // Otherwise, check if any field matches the filter text
      return (
        repo.name.toLowerCase().includes(filterText) ||
        repo.owner.toLowerCase().includes(filterText) ||
        (repo.language && repo.language.toLowerCase().includes(filterText)) ||
        (repo.description && repo.description.toLowerCase().includes(filterText)) ||
        repo.nameWithOwner.toLowerCase().includes(filterText)
      );
    })
    .sort((a, b) => {
      // Use case-insensitive sorting for string properties
      let x = a[resolvedOrderProp];
      let y = b[resolvedOrderProp];
      if (typeof x === 'string') x = x.toLowerCase();
      if (typeof y === 'string') y = y.toLowerCase();
      return x < y ? -1 : x > y ? 1 : 0;
    });
  if (isOrderReversed) {
    items.reverse();
  }
  REPO_SECTION_ELEMENT.innerHTML = items
    .map(
      (repo) => `
  <div class="catalog-grid-item">
    <a class="repoLink">
      <h3 class="text-center">
        <span title="Name">${repo.name}</span>
        <small><span title="Owner">${repo.owner}</span></small>
        <small><span title="Primary Language">${repo.language || '-'}</span></small>
      </h3>
    </a>
    ${repo.description ? `<p>${sanitizeHTML(repo.description)}</p>` : ''}

    <p class="stats text-center">
      <a href="${repo.gitUrl}" title="GitHub Repository">
        <span class="fa fa-github"></span>
      </a>

      <a href="${repo.gitUrl}/stargazers" title="Community Interest">
        <span class="fa fa-star"></span> ${repo.stars}
      </a>

      <a href="${repo.gitUrl}/network" title="Repository Forks">
        <span class="fa fa-code-fork"></span> ${repo.forks}
      </a>
      <a href="/explore/spack-dependencies/?package=${repo.name}" title="View Dependencies">
        <span class="fa fa-pie-chart"></span>
      </a>
      ${
        repo.homepageUrl
          ? `
        <a href="${repo.homepageUrl}" title="Project Website">
          <span class="fa fa-globe"></span>
        </a>
      `
          : ''
      }
      ${
        repo.cdash
          ? `
          <a href="${repo.cdash}" title="CDash Testing Dashboard"><img src="${window.config.baseUrl}/assets/images/logos/cdash.svg" height="20" width="20" alt="CDash"></img></a>
      `
          : ''
      }

    </p>
  </div>
  `,
    )
    .join('');
  const repoLinks = document.getElementsByClassName('repoLink');
  for (let i = 0; i < repoLinks.length; i++) {
    repoLinks[i].addEventListener('click', () => {
      const repo = encodeURIComponent(items[i].nameWithOwner);
      setVisibleRepo(repo);
    });
  }
}

/**
 * Call when the user updates category (either through the UI or through the browser)
 *
 * @param {number} categoryIdx selected index of the category
 */
function onCategoryUpdate(categoryIdx) {
  selectedCategoryIndex = categoryIdx;
  console.log(`Category updated to index ${categoryIdx}, category: ${catData[categoryIdx]?.title}, repos count: ${topicRepos[categoryIdx]?.length}`);
  const categoryButtons = document.getElementsByClassName('tab');
  for (let i = 0; i < categoryButtons.length; i++) {
    const button = categoryButtons[i];
    if (button.id.endsWith(categoryIdx)) {
      button.classList.add('selected-tab');
    } else {
      button.classList.remove('selected-tab');
    }
  }
  // Show welcome text only for "All Software" category (index 0)
  if (ELEMENT_WELCOME_TEXT) {
    if (categoryIdx === 0) {
      ELEMENT_WELCOME_TEXT.classList.remove(HIDDEN_CLASS);
    } else {
      ELEMENT_WELCOME_TEXT.classList.add(HIDDEN_CLASS);
    }
  }
  renderRepoListHeaderHtml();
  renderRepoListHtml();
}

////////////////////////////////////////////////
///////////// MAIN UPDATE FUNCTIONS /////////////
////////////////////////////////////////////////

function showCategoryList() {
  setTimeout(() => window.scrollTo({ top: 0, behavior: 'auto' }), 0);
  ELEMENTS_ONLY_LIST.forEach((ele) => ele.classList.remove(HIDDEN_CLASS));
  ELEMENTS_ONLY_SINGLE_REPO.forEach((ele) => ele.classList.add(HIDDEN_CLASS));
}

function showSingleRepo() {
  setTimeout(() => window.scrollTo({ top: 0, behavior: 'auto' }), 0);
  ELEMENTS_ONLY_SINGLE_REPO.forEach((ele) => ele.classList.remove(HIDDEN_CLASS));
  ELEMENTS_ONLY_LIST.forEach((ele) => ele.classList.add(HIDDEN_CLASS));
}

/**
 *
 * User has selected a visible repository. If user selects empty repository, render category list instead.
 *
 * @param {string} newValue the next repo to change
 * @param {boolean} shouldPushState Set to true the first time the user navigates to the catalog, or navigates from history. 
 *   Leave as false or undefined if the user triggers a click event.
 *
 */
function setVisibleRepo(newValue, shouldPushState) {
  visibleRepo = newValue;
  if (!visibleRepo) {
    if (!hasUserVisitedCategoryListPageYet) {
      hasUserVisitedCategoryListPageYet = true;
      // init
      fetch(`${window.config.baseUrl}/catalog/category_info.json`)
        .then((res) => res.json())
        .then((catInfoJson) => {
          Object.values(catInfoJson.data)
            .map((data) => {
              data['displayTitle'] = titleCase(data.title);
              // this is used both in the URL and the HTML ID
              data['urlParam'] = categoryToUrl(data.title);
              return data;
            })
            .sort((a, b) => {
              const x = a['displayTitle'];
              const y = b['displayTitle'];
              return x < y ? -1 : x > y ? 1 : 0;
            })
            .forEach((category) => catData.push(category));
          // get selected index from URL query param, or default to "all software" if invalid/no param
          const initialCategory = new URLSearchParams(window.location.search).get('category')?.toLowerCase() || 'all';
          for (let c = 0; c < catData.length; c++) {
            if (catData[c].urlParam === initialCategory) {
              selectedCategoryIndex = c;
              break;
            }
          }

          // render category specific HTML
          renderRepoListHeaderHtml();
          ELEMENT_NAV_DESKTOP.innerHTML = catData
            .map(
              (category, idx) => `
            <button id="btn__${idx}" class="tab${idx === selectedCategoryIndex ? ' selected-tab' : ''}">
              <img
                src="${window.config.baseUrl}${category.icon.path}"
                height="40"
                width="40"
                alt="${category.icon.alt}"
                title="${category.icon.alt}"
                loading="lazy"
              />
              <span>
                ${sanitizeHTML(category.displayTitle)}
              </span>
            </button>
          `,
            )
            .join('');
          ELEMENT_NAV_MOBILE.innerHTML = catData
            .map(
              (category, idx) => `
            <button id="nav-btn__${idx}" class="tab${idx === selectedCategoryIndex ? ' selected-tab' : ''}">${sanitizeHTML(
                category.displayTitle,
              )}</button>
          `,
            )
            .join('');
          const tabElements = document.getElementsByClassName('tab');
          for (let i = 0; i < tabElements.length; i++) {
            const ele = tabElements[i];
            const tabIdx = Number(ele.id.split('__')[1]);
            ele.addEventListener('click', () => {
              window.history.pushState(
                { categoryIndex: tabIdx, repo: visibleRepo },
                '',
                `?category=${catData[tabIdx].urlParam}&repo=${visibleRepo}`,
              );
              onCategoryUpdate(tabIdx);
            });
          }

          // map topics to categories - first try CASS explicit mapping, then fall back to topics
          fetch(`${window.config.baseUrl}/catalog/cass_category_mapping.json`)
            .then((res) => res.json())
            .then((cassMapping) => {
              // Initialize category arrays with CASS mapping
              catData.forEach((category) => {
                const catRepos = [];
                const cassRepos = cassMapping.data[category.title] || [];
                // Add repos from CASS explicit mapping
                cassRepos.forEach((repoName) => {
                  catRepos.push({ nameWithOwner: repoName });
                });
                topicRepos.push(catRepos);
              });

              // Return promise to continue chain
              return fetch(`${window.config.baseUrl}/explore/github-data/intRepos_Topics.json`);
            })
            .then((res) => res.json())
            .then((topicJson) => {
              const reposObj = topicJson.data;
              // Add additional repos based on topics (that aren't already in CASS mapping)
              catData.forEach((category, idx) => {
                for (let r in reposObj) {
                  // Check if repo is already in this category from CASS mapping
                  const alreadyAdded = topicRepos[idx].some(existing => existing.nameWithOwner === r);
                  if (!alreadyAdded) {
                    const repo = reposObj[r];
                    const topics = [];
                    repo.repositoryTopics.nodes.forEach((node) => {
                      topics.push(node.topic.name);
                    });
                    if (containsTopics(category.topics, topics)) {
                      topicRepos[idx].push({ nameWithOwner: r });
                    }
                  }
                }
              });

              // Return promise to continue chain
              return fetch(`${window.config.baseUrl}/explore/github-data/intReposInfo.json`);
            })
            .then((res) => res.json())
            .then((infoJson) => {
              const reposInfoObj = infoJson.data;
              for (let repo in reposInfoObj) {
                    //reposInfoObj[repo] is the actual repo object
                    for (let j in topicRepos) {
                      //var category is array of objects
                      const category = topicRepos[j];
                      for (let count in category) {
                        // category[count] is a specific repo within a category
                        //if we find a repo that is included in the category repos, we save more info on it
                        if (category[count].nameWithOwner === reposInfoObj[repo].nameWithOwner) {
                          //save only necessary data fields
                          category[count]['name'] = reposInfoObj[repo].name;
                          category[count]['description'] = reposInfoObj[repo].description;
                          category[count]['ownerAvatar'] = reposInfoObj[repo].owner.avatarUrl;
                          category[count]['owner'] = reposInfoObj[repo].owner.login;
                          category[count]['stars'] = reposInfoObj[repo].stargazers.totalCount;
                          category[count]['gitUrl'] = reposInfoObj[repo].url;
                          category[count]['homepageUrl'] = reposInfoObj[repo].homepageUrl;
                          if (reposInfoObj[repo].primaryLanguage) {
                            category[count]['language'] = reposInfoObj[repo].primaryLanguage.name;
                          } else {
                            category[count]['language'] = '';
                          }
                          category[count]['forks'] = reposInfoObj[repo].forks.totalCount;
                          if (reposInfoObj[repo].cdash) {
                            category[count]['cdash'] = reposInfoObj[repo].cdash
                          }
                        }
                      }
                    }
                  }
                  renderRepoListHtml();
                });
        });
    }
    showCategoryList();
  } else {
    renderSingleRepo(decodeURIComponent(visibleRepo));
    showSingleRepo();
  }
  if (!shouldPushState) {
    window.history.pushState(
      { categoryIndex: selectedCategoryIndex, repo: visibleRepo },
      '',
      `?category=${catData[selectedCategoryIndex].urlParam}&repo=${visibleRepo}`,
    );
  }
}

/////////////////////////////////////////////////////////////////
////////////////////// INIT /////////////////////////////////////
/////////////////////////////////////////////////////////////////

// Sets initial category page
const repoFromUrl = new URLSearchParams(window.location.search).get('repo') || '';
setVisibleRepo(repoFromUrl, true);

////////////////////////////////////////////////////////////////
//////////////////////// EVENT LISTENERS ///////////////////////
////////////////////////////////////////////////////////////////

// searching
document.getElementById('searchText').addEventListener('input', (e) => {
  filterText = e.target.value.toLowerCase();
  renderRepoListHtml();
  // TODO test out debounce when we have a lot of data
  // clearTimeout(searchTimeout);
  // searchTimeout = setTimeout(() => {
  //   filterText = e.target.value.toLowerCase();
  //   renderRepoHtml();
  // }, 1000);
});

// sorting
document.getElementById('orderProp').addEventListener('change', (e) => {
  orderProp = e.target.value;
  renderRepoListHtml();
});

// mobile nav
document.getElementById('category-hamburger-btn').addEventListener('click', () => {
  ELEMENT_NAV_MOBILE.classList.toggle(HIDDEN_CLASS);
});

// back button on category list
document.getElementById('category-list-btn').addEventListener('click', () => {
  setVisibleRepo('');
});

// user presses back/forward buttons on their browser
window.addEventListener('popstate', (e) => {
  const oldRepoState = e.state?.repo;
  const hasOldRepoState = !!oldRepoState;
  if (!hasOldRepoState || oldRepoState !== visibleRepo) {
    setVisibleRepo(hasOldRepoState ? oldRepoState : '', true);
  }

  const oldCategoryState = e.state?.categoryIndex;
  const hasOldCategoryState = typeof oldCategoryState === 'number';
  if (!hasOldCategoryState || oldCategoryState !== selectedCategoryIndex) {
    onCategoryUpdate(hasOldCategoryState ? oldCategoryState : 0);
  }
});

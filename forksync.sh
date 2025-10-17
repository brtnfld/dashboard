#!/bin/sh
git remote add upstream https://github.com/corsa-center/dashboard.git
git fetch upstream
#git merge upstream/develop
git rebase -Xtheirs upstream/main
# git push origin develop --force
#
# git fetch upstream
#git reset --hard upstream/develop

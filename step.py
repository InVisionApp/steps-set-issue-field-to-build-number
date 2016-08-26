#!/bin/python
import os

import urllib2
import urllib
import sys
import json
import subprocess

###########
#Constants#
###########


username=os.environ['jira_username']
password=os.environ['jira_password']
searchJQL=os.environ['jira_search_JQL']
filedUpdate=os.environ['jira_filed_to_update']
host=os.environ['jira_host']
plist=os.environ['jira_plist_path']

testTicket=os.environ.get('jira_test_ticket', None)
ignoreNotCommited=os.environ.get('jira_ignore_not_commited', 'False')
dryRun=os.environ.get('jira_dry_run', 'False')
testTag=os.environ.get('jira_test_tag', None)
tagBranch=os.environ.get('jira_tag_branch', 'False')

searchPath='/rest/api/latest/search'
searchQuery='fields=id,key,%s&maxResults=50' % filedUpdate
updatePath='/rest/api/latest/issue/'

#########
#Methods#
#########


def str2bool(v):
  return v.lower() in ["yes", "true", "t", "1"]

def encodeUserData(user, password):
    return "Basic " + (user + ":" + password).encode("base64").rstrip()

def run(cmd, debug=False, params=None):
    if debug:
        print cmd
    
    items = cmd.split()
    if params is not None:
        items.extend(params)
    process = subprocess.Popen(items, stdout=subprocess.PIPE)
    output = process.communicate()[0]
    
    if debug:
        print output
        
    return output

def requestURL(url, data=None, method=None, decode=True, exitOnFail=True):
    
    if data:
        data = json.dumps(data)
    
    headers = {}
    headers['Content-Type'] = 'application/json'
    headers['Accept'] = 'application/json'
    headers['Authorization'] = encodeUserData(username, password)
    
    req = urllib2.Request(url, data, headers)
    if method:
        req.get_method = lambda: method
        
    try:
        res = urllib2.urlopen(req)
    except urllib2.HTTPError as e:
        if e.code == 401:
            print "  Username/password incorrect"
        else:
            print "  Error: %s" % e
        if exitOnFail:
            sys.exit(1)
        else:
            return False

    if decode:
        results = json.load(res)
    else:
        results = True
    
    return results

def getIssues():
    url='%s%s?jql=%s&%s' %(host, searchPath, urllib.quote(searchJQL), searchQuery)
    results = requestURL(url)
    issues = results['issues']
    return issues

def updateTicketWithTag(ticket, tag):
    data={ "update": { filedUpdate: [ {"add": tag} ] } }
    url='%s%s%s' %(host, updatePath,ticket)
    return requestURL(url, data, 'PUT', False, False)

def main():
    
    gitLog = run('git log --pretty=oneline --abbrev-commit --since=2.weeks')
    gitLog += run('git submodule foreach --quiet', params=["git log --pretty=oneline --abbrev-commit --since=2.weeks --submodule"])
    issues = getIssues()

    if testTag:
        tag = testTag
    else:
        tag = sys.argv[1]
    
    print "  Tag: %s" % tag
    
    keys = []
    alreadyUpdatedKeys = []
    noCommitKeys = []
    
    if ignoreNotCommited:
        print "  Include not commited tickets"
    
    for issue in issues:
        key = issue['key']
        fields = issue.get('fields', None)
        if fields is None:
            continue
        
        tags = fields[filedUpdate]
        
        if testTicket and key != testTicket:
            continue
        
        if tags and tag in tags:
            alreadyUpdatedKeys.append(key)
        elif not ignoreNotCommited and key not in gitLog:
            noCommitKeys.append(key)
        else:
            keys.append(key)
            
    if len(alreadyUpdatedKeys) > 0:
        print "  Already updated tickets:\n    %s" % alreadyUpdatedKeys
    
    if len(noCommitKeys) > 0:
        print "  Not commited tickets:\n     %s" % noCommitKeys
    
    print "  Tickets to be updated:\n     %s" % keys
    
    if dryRun:
        print "  Dry run"
    else:
        for key in keys:
            result = updateTicketWithTag(key, tag)
            if result:
                print "  Updated ticket %s" % key
            else:
                print "  Failed update for ticket %s" % key
                
        if tagBranch:
            oldTags = run("git ls-remote origin refs/tags/%s" % tag)
            if tag in oldTags:
                print "  Already Tagged branch"
            else:
                branch=run("git rev-parse --abbrev-ref HEAD")
                print "  Tagging branch: %s" % branch
                run("git tag %s" % tag)
                run("git push origin %s tag %s" % (branch, tag))

    print "  Done!"
            
ignoreNotCommited = str2bool(ignoreNotCommited)
dryRun = str2bool(dryRun)
tagBranch = str2bool(tagBranch)

main()


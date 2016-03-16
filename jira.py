#!/bin/python

import urllib2
import urllib
import sys
import json
import subprocess

###########
#Constants#
###########
username='petergulyas'
password='NT6iawFeq6xxuJ'
gitDir = '/Users/petergulyas/Documents/InVisionApp/invisionapp-ios'
searchJQL='project=10607 AND status=Merged'
filedUpdate='customfield_11100'
testTicket='SILVER-352'
ignoreNotCommited=True

host='https://invisionapp.atlassian.net'
searchPath='/rest/api/latest/search'
searchQuery='fields=id,key,%s&maxResults=50' % filedUpdate
updatePath='/rest/api/latest/issue/'

#########
#Methods#
#########

# simple wrapper function to encode the username & pass
def encodeUserData(user, password):
    return "Basic " + (user + ":" + password).encode("base64").rstrip()

def run(cmd, debug=False):
    if debug:
        print cmd
    
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    
    if debug:
        print output
        
    return output

def requestURL(url, data=None, method=None, decode=True):
    
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
            print "Username/password incorrect"
        else:
            print "Error: %s" % e
        sys.exit(1)

    if decode:
        results = json.load(res)
    else:
        results = None
    
    return results

def getIssues():
    url='%s%s?jql=%s&%s' %(host, searchPath, urllib.quote(searchJQL), searchQuery)
    results = requestURL(url)
    issues = results['issues']
    return issues

def updateTicketWithTag(ticket, tag):
    data={ "update": { filedUpdate: [ {"add": tag} ] } }
    url='%s%s%s' %(host, updatePath,ticket)
    requestURL(url, data, 'PUT', False)

def main():
    
    gitLog = run('git --git-dir=%s/.git log --pretty=oneline --abbrev-commit --since=2.weeks' % gitDir)
    issues = getIssues()

    
    tag = "THIS_IS_A_TEST_TAG"
    
    keys = []
    alreadyUpdatedKeys = []
    noCommitKeys = []
    for issue in issues:
        key = issue['key']
        tags = issue['fields'][filedUpdate]
        
        if testTicket and key != testTicket:
            continue
        
        if tags and tag in tags:
            alreadyUpdatedKeys.append(key)
        elif not ignoreNotCommited and key not in gitLog:
            noCommitKeys.append(key)
        else:
            keys.append(key)
            
    if len(alreadyUpdatedKeys) > 0:
        print "Already updated tickets:\n%s" % alreadyUpdatedKeys
    
    if len(noCommitKeys) > 0:
        print "Not commited tickets:\n%s" % noCommitKeys
    
    print "Tickets to be updated:\n%s" % keys
    
    for key in keys:
        updateTicketWithTag(key, tag)
    
main()

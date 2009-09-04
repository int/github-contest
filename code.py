#!/usr/bin/python

import psyco
psyco.full()

cocount = {} # co-occurrence repo pair count
sortedco = {} # sorted co-occurences
user = {} # users info
repo = {} # repo info
popular = [] # popularity
own = {} # repos owned by named user
lang = {} # repos in specific language

class User(object):
    def __init__(self):
        self.watch = [] # repos s/he watches

class Repo(object):
    def __init__(self):
        self.wcount = 0
        self.owner = None
        self.parent = None
        self.lang = []
        self.watcher = [] # who watches this repo

def loaddata():
    '''load data.txt'''
    print 'loading data.txt...'
    f = open('data.txt')
    for x in f:
        u, r = x.strip().split(':')
        if r not in repo:
            repo[r] = Repo()
        repo[r].wcount += 1
        repo[r].watcher.append(u)
        if u not in user:
            user[u] = User()
        user[u].watch.append(r)

def loadrepo():
    '''load repos.txt'''
    print 'loading repos.txt...'
    f = open('repos.txt')
    for x in f:
        r, info = x.strip().split(':')
        if r not in repo:
            repo[r] = Repo()
        owner, s = info.split('/')
        repo[r].owner = owner
        if owner not in own:
            own[owner] = []
        own[owner].append(r)
        a = s.split(',')
        if len(a) == 3:
            repo[r].parent = a[2]

def loadlang():
    '''load lang.txt'''
    print 'loading lang.txt...'
    f = open('lang.txt')
    for x in f:
        r, info = x.strip().split(':')
        if r not in repo:
            repo[r] = Repo()
        v = repo[r].lang
        for s in info.split(','):
            a, b = s.split(';')
            v.append((a, int(b)))
            if a not in lang:
                lang[a] = []
            lang[a].append(r)

def getco():
    '''get co-occurence counting'''
    print 'build co-occurence count...'

    def add(a, b):
        '''helper function, add (a,b) pair to co-coccurence counting'''
        cocount.setdefault(a, {})
        cocount[a].setdefault(b, 0)
        cocount[a][b] += 1

    for u in user:
        r = user[u].watch
        print '   for user ' + u + ' with ' + str(len(r)) + ' repos'
        for i in xrange(len(r)):
            a = r[i]
            for j in xrange(i + 1, len(r)):
                b = r[j]
                add(a, b)
                add(b, a)

def sortco():
    '''sort co-occurences'''
    print 'sort out co-occurence...'
    for a in cocount:
        s = cocount[a]
        b = [x for x in s]
        b.sort(key = lambda x: -s[x])
        sortedco[a] = b

def dumpco():
    '''dump sorted co-occurence to disk file'''
    out = open('sortedco.txt', 'w')
    for r in sortedco:
        out.write(r + ':')
        s = sortedco[r]
        for x in xrange(len(s) - 1):
            out.write(s[x] + ',')
        if len(s) > 0:
            out.write(s[-1] + '\n')
        else:
            out.write('\n')

def loadco():
    '''load sorted co-occurences from dumped file'''
    print 'loading sorted co-occurences info...'
    f = open('sortedco.txt')
    for x in f:
        u, rs = x.strip().split(':')
        sortedco[u] = rs.split(',')

def getpop():
    '''get popularity'''
    print 'get repos popularity...'
    global popular
    popular = [x for x in repo]
    popular.sort(key = lambda a: -repo[a].wcount)
    # sort each lang by popularity
    for x in lang:
        lang[x].sort(key = lambda a: -repo[a].wcount)

def bytree(u, result):
    '''get unwatched repos from most popular family tree'''
    got = len(result)
    if got >= 10:
        return

    rs = user[u].watch
    w = {} # weight of watched family
    for r in rs:
        if r not in repo:
            continue
        # walk up the tree
        x = r
        while x != None:
            if x not in w:
                w[x] = 1
            else:
                w[x] += 1
            x = repo[x].parent

    candi = [x for x in w]
    candi.sort(key = lambda a: -w[a])
    for x in candi:
        if x in rs or x in result: # already watched
            continue
        result.append(x)
        got += 1
        if got >= 10:
            break

def bylang(u, result):
    '''get unwatched repos by his/her language preference'''
    got = len(result)
    if got >= 10:
        return
    rs = user[u].watch
    prefer = {}
    for r in rs:
        for a, b in repo[r].lang:
            if a not in prefer:
                prefer[a] = 0
            prefer[a] += b # weighted by code length
    candi = [x for x in prefer]
    candi.sort(key = lambda a: -prefer[a])
    for x in candi:
        for a in lang[x]:
            if a in rs or a in result:
                continue
            result.append(a)
            got += 1
            if got >= 10:
                return

def byown(u, result):
    '''get unwatched repos from your watched repos' owners'''
    got = len(result)
    if got >= 10:
        return
    rs = user[u].watch
    who = set([]) # watched repos' owners (by user name)
    for r in rs:
        if r not in repo:
            continue
        owner = repo[r].owner
        if owner == None:
            continue
        if owner not in who:
            who.add(owner)
    candi = [y for x in who for y in own[x]]
    candi.sort(key = lambda a: -repo[a].wcount)
    for x in candi:
        if x in rs or x in result: # already watched
            continue
        result.append(x)
        got += 1
        if got >= 10:
            break

def bywatch(u, result):
    '''get unwatched repos from your watched repos' watchers'''
    got = len(result)
    if got >= 10:
        return
    print u, got, 'hit bywatch'
    rs = user[u].watch
    who = set([]) # watched repos' watchers (by uid)
    for r in rs:
        if r not in repo:
            continue
        for w in repo[r].watcher:
            if w not in who:
                who.add(w)
    candi = [y for x in who for y in user[x].watch]
    candi.sort(key = lambda a: -repo[a].wcount)
    for x in candi:
        if x in rs or x in result: # already watched
            continue
        result.append(x)
        got += 1
        if got >= 10:
            break

def byco(u, result):
    '''choose top most co-occurences'''
    got = len(result)
    if got >= 10:
        return
    rs = user[u].watch
    cur = [0] * len(rs)

    def biggest():
        '''return next biggest or -1 if there's no one.'''
        # kinda like mergesort
        best = -1
        idx = -1
        for x in xrange(len(rs)):
            r = rs[x]
            if r not in sortedco:
                continue
            s = sortedco[r]
            a = -1 # init
            while cur[x] < len(s):
                a = s[cur[x]]
                if a not in rs and a not in result: # got one
                    break
                cur[x] += 1
            if a > best:
                best = a
                idx = x
        if idx != -1:
            cur[idx] += 1
        return best

    while got < 10:
        x = biggest()
        if x == -1:
            break
        result.append(x)
        got += 1

def bypop(u, result):
    got = len(result)
    if got >= 10:
        return
    rs = user[u].watch
    for x in popular:
        if x in rs or x in result: # watched already
            continue
        result.append(x)
        got += 1
        if got >= 10:
            break

def doit():
    '''lets do it'''
    print 'try guessing...'
    f = open('test.txt')
    out = open('results.txt', 'w')
    for x in f:
        u = x.strip()
        #print '    for user ' + u + '...'
        if u not in user:
            user[u] = User()
        result = []

        # rules in order
        bytree(u, result)
        byco(u, result)
        byown(u, result)
        bywatch(u, result)
        bylang(u, result)
        bypop(u, result)

        # write
        out.write(u + ':')
        for x in xrange(10):
            c = ','
            if x == 9:
                c = '\n'
            out.write(result[x] + c)


loaddata()
loadrepo()
loadlang()
getpop()

'''
getco()
sortco()
dumpco()
'''

loadco()
doit()

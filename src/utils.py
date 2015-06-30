# -*- coding: UTF-8 -*-
import cherrypy,settings,threading,random
from collections import defaultdict

EACH_RANK_DOMAIN_COUNT = 5

lock = threading.Lock()

def threadLock(f):
  def _decor(*args,**kwargs):
    lock.acquire()
    try:
      ret = f(*args,**kwargs)
    finally:
      lock.release()
    return ret
  return _decor


# Simple RBAC decorator
def role(roleNameList): # roleNameList: "*" | ["roleName"]
  def _decor(f):
    def _roleChecker(*args,**kwargs):
      username = cherrypy.request.login
      role = settings.USERS[username]['role']
      if role not in roleNameList:
        status = "403 Forbidden Role:" + role
        cherrypy.response.status = status
        return "<h1>" + status + "</h1>"
      return f(*args,**kwargs)

    if roleNameList == '*':
      return f
    else:
      return _roleChecker
  return _decor

# Content-Type decorator
def mimetype(type):
    def decorate(func):
        def wrapper(*args, **kwargs):
            cherrypy.response.headers['Content-Type'] = type
            return func(*args, **kwargs)
        return wrapper
    return decorate



"""
Return [(Rank,Domain)]
"""
def rankDomains(domains):
  if not domains:
    return []

  domains = map(lambda d:(d.split('.',1)[1],d),domains)
  random.shuffle(domains)
  grouped = defaultdict(list)
  for provider,domain in domains:
    grouped[provider].append(domain)

  domains = filter(None,sum(map(None,*grouped.values()+[[None]]),tuple()))
  rank = 0
  i = 0
  ranked = []
  for d in domains:
    ranked.append( (rank,d) )
    i += 1
    if i >= EACH_RANK_DOMAIN_COUNT:
      rank += 1
      i = 0

  if i > 0 and i < EACH_RANK_DOMAIN_COUNT and rank > 0: # last rank is not fulfilled,merge it with previous rank
    while i > 0:
      ranked[-i] = (ranked[-i][0]-1,ranked[-i][1])
      i -= 1

  return ranked






















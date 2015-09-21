# -*- coding: UTF-8 -*-
import cherrypy,settings,threading,random
from collections import defaultdict

# Default public rank only have three available domains
PUBLIC_RANK_DOMAIN_COUNT = 3
# Rank 0 has 3, Rank 1 has 4,Rank 2 has 5....
RANK_INCREASE_RATE = 1

# Special reserved rank
RESERVED_RANK = 9
# 30 reserved domains in rank 9
RESERVED_RANK_COUNT = 30

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
        cherrypy.response.headers['Content-Type'] = 'text/html'
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


def _splitDomainSuffix(d):
  try:
    return (d.split('.',1)[1],d)
  except IndexError:
    raise Exception("Domain '%s' format is not valid, dot separator expected!" % d)

"""
Return [(Rank,Domain)]
"""
def rankDomains(domains):
  domains = map(_splitDomainSuffix,domains)

  grouped = defaultdict(list)
  for provider,domain in domains:
    grouped[provider].append(domain)

  # intersperse domains in different provider
  domains = filter(None,sum(map(None,*grouped.values() + [[None]]),tuple()))

  ranked = []
  if len(domains) > RESERVED_RANK_COUNT + PUBLIC_RANK_DOMAIN_COUNT:
    reserved = domains[0:RESERVED_RANK_COUNT]
    domains = domains[RESERVED_RANK_COUNT:-1]
    ranked += map(lambda d:(RESERVED_RANK,d),reserved)

  rank = 0 ; i = 0 ;
  rank_count = PUBLIC_RANK_DOMAIN_COUNT
  for d in domains:
    ranked.append( (rank,d) )
    i += 1
    if i >= rank_count:
      rank += 1 ; i = 0
      rank_count += RANK_INCREASE_RATE

  return ranked






















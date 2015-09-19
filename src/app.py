#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import cherrypy,settings,json,os,re,sqlite3,random
from cherrypy.lib import auth_basic
from cherrypy import expose,HTTPError
from utils import *
import os.path


rank_zero_append_domains = []


class Domains():
  exposed = True
  def __init__(self):
    self._init_database()
    self._debug = True
    if settings.environment == 'production':
      self._debug = False

  def _init_database(self):
    db = sqlite3.connect(settings.DB_FILE_PATH)
    cursor = db.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS MirrorDomain (
      domain TEXT PRIMARY KEY NOT NULL,
      site TEXT NOT NULL,
      rank INTEGER NOT NULL DEFAULT 0,
      blocked BOOLEAN NOT NULL DEFAULT false,
      cdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cursor.execute('CREATE INDEX IF NOT EXISTS query_index ON MirrorDomain(site,blocked,rank)')
    db.commit()
    db.close()


  """
  GET site domains by rank and status
  GET /domains/$site/?status=up&rank=0
    Params:
      site: The site id, required
      status: The accessible status, default is up,i.e. not blocked.
              Enum(up|down|all)
      rank: The domain rank, default is 0, i.e. public. use rank=all to get all domains
      format: The output format, default is 'plain', means output plain text, domains seperated by line feed
              Enum(plain|json|detail)
                Format 'detail' will output each JSON with each domain's detail information: [DomainObject]
                [{domain:"up.a.com",blocked:true,rank:1}]


  Output:
    Domain list seperated by line feed char
  """
  @mimetype('text/plain')
  def GET(self,site=None,status='up',rank='0',format='plain',*args,**kwargs):
    if format not in ('plain','json','detail'):
      raise HTTPError(400,"Output format must be either plain or json.")
    if site is None:
      return self._list_all_sites(format)
    if status not in ('up','down','all'):
      raise HTTPError(400,"Status must be either up or down or all.")

    if rank != 'all':
      try:
        rank = int(rank)
      except ValueError:
        raise HTTPError(400,"Rank must be integer.")

    if rank != 0 :
      cb = lambda *args,**kwargs: self._fetch(*args,**kwargs)
      return role(['admin','mandator','vip'])(cb)(site,status,rank,format)
    else:
      return self._fetch(site,status,rank,format)

  def _fetch(self,site,status,rank,format):
    db = sqlite3.connect(settings.DB_FILE_PATH)
    cursor = db.cursor()

    if rank == 0:
      order = 'ASC'
      if status == 'down':
        order = 'DESC'
      cursor.execute('SELECT domain,blocked,rank FROM MirrorDomain WHERE site=? AND rank=0 ORDER BY blocked ' + order + ' LIMIT 3',(site,))
    else:
      condSQL = ''
      condValue = (site,)

      if rank != 'all':
        condSQL += ' AND rank=?'
        condValue += (rank,)

      if status != 'all':
        condSQL += ' AND blocked=?'
        condValue += (status=='down',)

      cursor.execute('SELECT domain,blocked,rank FROM MirrorDomain WHERE site=? '+condSQL,condValue)

    domains = cursor.fetchall()
    db.close()

    if rank==0:
      random.shuffle(rank_zero_append_domains)
      domains = domains + rank_zero_append_domains[0:5]

    if format == 'detail':
      domains = map(lambda t:{"domain":t[0],"blocked":t[1],"rank":t[2]},domains)
    else:
      domains = map(lambda t:t[0],domains)

    if format == 'plain':
      return "\n".join(domains) + "\n"
    elif format == 'json' or format == 'detail':
      return json.dumps(domains)

  def _list_all_sites(self,format):
    db = sqlite3.connect(settings.DB_FILE_PATH)
    cursor = db.cursor()
    cursor.execute('SELECT DISTINCT site FROM MirrorDomain')
    sites = map(lambda t:t[0],cursor.fetchall())
    db.close()
    if format == 'plain':
      return "\n".join(sites) + "\n"
    elif format  == 'json':
      return json.dumps(dict(siteIdList=sites))


  """
  POST /domains/$site/
    Body:up=a.example.com,b.example.com&down=x.example.com
    Params:
      site: The site ID
      up: up domain split by comma or space
      down: down domain split by comma or space
  """
  @role(['admin','mandator'])
  @mimetype('text/plain')
  def POST(self,site,up,down,*args,**kwargs):
    db = sqlite3.connect(settings.DB_FILE_PATH)
    cursor = db.cursor()

    up_domains = set(filter(None,re.split('[,\s]+',up.strip())))
    down_domains = set(filter(None,re.split('[,\s]+',down.strip())))

    if down_domains:
      cursor.execute('DELETE FROM MirrorDomain WHERE site=:site AND blocked=1',{"site":site})
      updates = map(lambda (domain):(domain,site,True),down_domains)
      cursor.executemany('INSERT OR REPLACE INTO MirrorDomain(domain,site,blocked) values(?,?,?)',updates)

    if up_domains:
      # mark old up domains to down only when new up domains are available
      cursor.execute('UPDATE MirrorDomain SET blocked=1 WHERE site=:site',{"site":site})

      ranked_up_domains = rankDomains(up_domains) # :: [(Rank,Domain)]
      blocked = False
      updates = map(lambda (rank,domain):(domain,site,blocked,rank),ranked_up_domains)
      cursor.executemany('INSERT OR REPLACE INTO MirrorDomain(domain,site,blocked,rank) values(?,?,?,?)',updates)

    db.commit()
    db.close()
    return "OK\n"


  @role(['admin','mandator'])
  @mimetype('text/plain')
  def DELETE(self):
    sql = "DELETE FROM MirrorDomain WHERE cdate <= DATETIME('now','-1 day')"
    db = sqlite3.connect(settings.DB_FILE_PATH)
    cursor = db.cursor()
    cursor.execute(sql)
    db.commit()
    db.close()
    return "DELETED\n"


class SubmitForm():
  exposed = True

  @role(['admin','mandator'])
  def GET(self):
    return '''
    <form action="/domains/" method="POST" style="width:50em;margin:4em auto;">
      <p><label>Site ID: <input type="text" name="site"/></label></p>
      <p><label>Up Domains split by comma or newline: </br><textarea name="up" style="width:40em;height:10em;"></textarea></label></p>
      <p><label>Down Domains split by comma or newline: </br><textarea name="down" style="width:40em;height:10em;"></textarea></label></p>
      <p><input type="submit"  value="Submit"/></p>
    </form>

    '''


def validate_password(realm,username, password):
  if username in settings.USERS and settings.USERS[username]['password'] == password:
     return True
  return False

def read_rank_zero_other_domains():
  other_domains_file = settings.RANK_ZERO_APPEND_FILE
  if os.path.isfile(other_domains_file):
    other_domains = filter(None,re.split('[,\s]+',open(other_domains_file).read().strip()))
    for domain in other_domains:
      rank_zero_append_domains.append((domain,0,0))


if __name__ == '__main__':
  read_rank_zero_other_domains()

  conf = {
    '/': {
      'tools.auth_basic.on': True,
      'tools.auth_basic.realm': 'localhost',
      'tools.auth_basic.checkpassword': validate_password,
      'request.dispatch': cherrypy.dispatch.MethodDispatcher()
    }
  }
  cherrypy.config.update({
    'server.ssl_module':'builtin',
    'server.ssl_certificate':settings.ssl_certificate,
    'server.ssl_private_key':settings.ssl_private_key,
    'server.socket_host': settings.host,
    'server.socket_port': settings.port,
    'environment': settings.environment
  })
  cherrypy.tree.mount(Domains(), '/domains/',conf)
  cherrypy.tree.mount(SubmitForm(), '/domain-submit-form/',conf)
  cherrypy.engine.start()
  cherrypy.engine.block()




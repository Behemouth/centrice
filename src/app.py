#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import cherrypy,settings,json,os,re,sqlite3
from cherrypy.lib import auth_basic
from cherrypy import expose,HTTPError
from utils import *


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
              Enum(up|down)
      rank: The domain rank, default is 0, i.e. public.
      format: The output format, default is 'plain', means output plain text, domains seperated by line feed
              Enum(plain|json)

  Output:
    Domain list seperated by line feed char
  """
  @mimetype('text/plain')
  def GET(self,site=None,status='up',rank='0',format='plain',*args,**kwargs):

    if format not in ('plain','json'):
      raise HTTPError(400,"Output format must be either plain or json.")
    if site is None:
      return self._list_all_sites(format)
    if status not in ('up','down'):
      raise HTTPError(400,"Status must be either up or down.")


    try:
      rank = int(rank)
    except ValueError:
      raise HTTPError(400,"Rank must be integer.")

    blocked = status == 'down'
    if rank != 0:
      return role(['admin','mandator'])(lambda *args,**kwargs:self._fetch(*args,**kwargs))(site,blocked,rank,format)
    else:
      return self._fetch(site,blocked,rank,format)

  def _fetch(self,site,blocked,rank,format):
    db = sqlite3.connect(settings.DB_FILE_PATH)
    cursor = db.cursor()
    cursor.execute('SELECT domain FROM MirrorDomain WHERE site=? AND rank=? AND blocked=?',(site,rank,blocked))
    domains = map(lambda t:t[0],cursor.fetchall())
    db.close()
    if format == 'plain':
      return "\n".join(domains) + "\n"
    elif format == 'json':
      return json.dumps(domains)

  def _list_all_sites(self,format):
    db = sqlite3.connect(settings.DB_FILE_PATH)
    cursor = db.cursor()
    cursor.execute('SELECT DISTINCT site FROM MirrorDomain')
    sites = map(lambda t:t[0],cursor.fetchall())
    db.close()
    if format == 'plain':
      return "Site id list:\n" + "\n".join(sites) + "\n"
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

    up_domains = set(filter(None,set(re.split('[,\s]+',up))))
    down_domains = set(filter(None,set(re.split('[,\s]+',down))))

    cursor.execute('DELETE FROM MirrorDomain WHERE site=:site AND blocked=1',{"site":site})

    if up_domains:
      # delete old up domains only when new up domains are available
      cursor.execute('DELETE FROM MirrorDomain WHERE site=:site AND blocked=0',{"site":site})

      ranked_up_domains = rankDomains(up_domains) # :: [(Rank,Domain)]
      blocked = False
      updates = map(lambda (rank,domain):(domain,site,blocked,rank),ranked_up_domains)
      cursor.executemany('INSERT OR REPLACE INTO MirrorDomain(domain,site,blocked,rank) values(?,?,?,?)',updates)

    if down_domains:
      ranked_down_domains = rankDomains(down_domains)
      blocked = True
      updates = map(lambda (rank,domain):(domain,site,blocked,rank),ranked_down_domains)
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


if __name__ == '__main__':
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




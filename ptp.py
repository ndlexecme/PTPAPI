import requests
from bs4 import BeautifulSoup
import re
import json
import os
import pickle
import copy
import tabulate
import quickjs

ctx = quickjs.Context()


def execJS(script):
    ctx.eval(script)
    return ctx.get('coverViewJsonData')

class PTP:
  baseURL = "https://passthepopcorn.me"
  resultsPerPage = 50

  def __init__(self, ApiUser, ApiKey, appdir, logger=None):
    if logger != None:
      self.LOG = logger
    else:
      self.LOG = None

    self._appdir = appdir
    self._getImplemented()
    self._creds = {'ApiUser': ApiUser, 'ApiKey': ApiKey}
    self.headers = {"User-Agent": "Wget/1.13.4"}
    self.cached = {}
    self._auth()

  def _getImplemented(self):
      cmds = json.load(open(os.path.join(self._appdir, "ptp-commands.json"), "r"))

      self.IMPLEMENTED = cmds.get("subparsers", [])
    
  def _auth(self):
    self.LOG.info("Creating session.")

    self.session = requests.Session()
    self.session.headers.update(self._creds)
    self.session.headers.update(self.headers)

    cookiefile = os.path.join(self._appdir, '.ptp_cookies')

    if os.path.isfile(cookiefile):
        self.LOG.info("Loading previously-saved session cookies from '{}'".format(".ptp_cookies"))
        with open(cookiefile, "rb") as f:
            self.session.cookies.update(pickle.load(f))
    else:
        self.LOG.info("Testing login")
        self.get("/index.php")
        with open(cookiefile, "wb") as f:
            self.LOG.info("Saving session cookies to '{}'".format(".ptp_cookies"))
            pickle.dump(self.session.cookies, f)

  def get(self, page, params={}, useCache=True):
    if useCache and self.cached.get('page', '') == page:
      self.LOG.info("Retrieving cached contents for page '{}'".format(page))
      return self.cached.get('contents')
    else:
      self.LOG.info("Retrieving contents for page '{}'".format(page))
      res = self.session.get(PTP.baseURL + page, params=params)
      self.LOG.info("Status code: {}".format(res.status_code))
      if res.status_code != 200:
        raise ConnectionError()

      html = BeautifulSoup(res.text, 'html.parser')
      self.cached.update({'page': page, 'contents': html})
      return html

  def getJSON(self, page, params={}, useCache=True):
    if useCache and self.cached.get('page', '') == page:
      self.LOG.info("Retrieving cached contents for page '{}'".format(page))
      return self.cached.get('contents')
    else:
      requestParams = {
        "json": "noredirect"
      }
      requestParams.update(params)

      self.LOG.info("Retrieving JSON contents for page '{}'".format(page))
      res = self.session.get(PTP.baseURL + page, params=requestParams)
      self.LOG.info("Status code: {}".format(res.status_code))
      if res.status_code != 200:
        raise ConnectionError()
      
      self.cached.update({"page": page, "contents": res.json()})
      return res.json()

  def getCoverJSON(self, page, params={}, useCache=True):
      html = self.get(page, params=params, useCache=useCache)

      total = int(html.find('div', {"class": "pagination"}).text.split('|')[-2].strip().split('-')[-1])

      script = html.find(id='wrapper').find_all('script')[-1].string

      splitted = script.split('\n\t')
      splitted.pop(0)
      splitted.pop(0)
      splitted.pop(0)
      splitted.pop(0)
      splitted.pop(0)
      splitted.pop(0)
      script = '\n\t'.join(splitted[0:2])


      result = execJS(script)

      coverData = json.loads(result.json())[0]

      coverData["total"] = total

      return coverData

  def ratio(self):
    html = self.get("/index.php")
    li = html.find("li", attrs={"id": "stats_ratio"})
    title = li.find("a", class_="user-info-bar__link").attrs.get('title')
    matches = re.findall(r"Ratio: ([\d.]+)", title)
    ratio = float(matches.pop(0))
    return ratio

  def buffer(self):
    html = self.get("/index.php")
    li = html.find("li", attrs={"id": "stats_ratio"})
    title = li.find("a", class_="user-info-bar__link").attrs.get('title')
    matches = re.findall(r"Buffer: ([\d.]+ [A-Za-z]+)", title)
    buffer = matches.pop(0)
    return buffer

  def bonus(self):
    html = self.get("/index.php")
    li = html.find("li", attrs={"id": "nav_bonus"})
    bonustext = li.find("a").text
    bonus = re.search(r'(?<=Bonus [(])(\d{1,3}[,]?)+', bonustext).group()
    return bonus

  def bonus_rate(self):
    html = self.get("/index.php")
    li = html.find("li", attrs={"id": "nav_bonus"})
    bonustext = li.find("a")['title']
    bprate = re.search(r'(?<=Bp/h[:] )(\d{1,3}[,]?)+', bonustext).group()
    return bprate

  def uploaded(self):
    html = self.get("/index.php")
    uploaded = html.find("li", attrs={"id": "stats_seeding"})
    text = uploaded.find("a").get('title')
    return text

  def downloaded(self):
    html = self.get("/index.php")
    downloaded = html.find("li", attrs={"id": "stats_leeching"})
    text = downloaded.find("a").get('title')
    return text

  def hnrs(self):
    html = self.get("/index.php")
    downloaded = html.find("li", attrs={"id": "stats_hnrs"})
    text = downloaded.find("span").text
    return text

  def user(self):
      results = {
          "userid": 118661
      }

      return results

  def seeding(self):
      params = {
          "type": "seeding",
          "userid": self.user().get('userid', 0)
      }

      data = self.getCoverJSON("/torrents.php", params=params)

      movies = data.get('Movies')

      total = data.get('total')

      pages = total // 51

      for i in range(1, pages+1):
        params['page'] = i+1
        data = self.getCoverJSON("/torrents.php", params=params, useCache=False)
        movies.extend(data.get('Movies'))

      return {'total': total, 'movies': movies}

  def search(self, query=None, params={}, limit=-1, filters=None):
      useCache = False
      current = 1
      numRetrieved = 0

      if query is not None:
          params["searchstr"] = query

      params["page"] = current

      data = self.getJSON("/torrents.php", params=params, useCache=useCache)
      total = int(data.get('TotalResults', 0))
      yield {"total": total}
      numMovies = 0
      remaining = limit

      while numMovies < total:
        if limit != -1 and limit - numMovies <= 0:
          break

        if current != 1:
            params["page"] = current
            data = self.getJSON("/torrents.php", params=params, useCache=useCache)

        movies = data.get('Movies')

        numMovies += len(movies)

        if filters is not None:
            newmovies = []
            for m in movies:
                torrents = m['Torrents']
                for f, v in filters.items():
                    if v is not None:
                        if isinstance(v, str):
                            filtered = list(filter(lambda t: t.get(f).lower() == v.lower(), torrents))
                        else:
                            filtered = list(filter(lambda t: t.get(f) == v, torrents))

                        if params.get("freetorrent", None) is not None:
                            torrents = list(filter(lambda t: t.get("FreeleechType", None) is not None, filtered))
                        else:
                            torrents = copy.copy(filtered)

                m['Torrents'] = torrents
                if len(m['Torrents']) != 0:
                    newmovies.append(m)

            movies = copy.copy(newmovies)

        current += 1

        if limit != -1:
            if remaining >= len(movies):
                finalMovies = movies
                remaining -= len(movies)
            else:
                finalMovies = movies[:remaining]
                remaining -= remaining
        else:
            finalMovies = movies

        yield {"page": current - 1, "movies": finalMovies}

  def fl(self, limit=-1, filters=None):
      params = {
        "freetorrent": "1"
      }

      return self.search(params=params, limit=limit, filters=filters)

  def summary(self, limit=-1, filters=None, filterGoldens=False):
      results = {}

      results['ratio'] = self.ratio()
      results['bonus'] = self.bonus()
      results['bprate'] = self.bonus_rate()
      results['up'] = self.uploaded()
      results['down'] = self.downloaded()
      results['buffer'] = self.buffer()
      results['seeding'] = self.seeding().get('total', 0)
      results['hnrs'] = self.hnrs()

      if filters is not None and filterGoldens:
          goldenFilters = copy.copy(filters)
      else:
          goldenFilters = {}

      goldenFilters['GoldenPopcorn'] = True

      goldenGen = self.fl(limit=limit, filters=goldenFilters)
      flTotal = next(goldenGen).get('total', 0)

      results['fl'] = {
          'total': flTotal,
          'golden': [],
      }

      if filters is not None:
          results['fl']['movies'] = []

          commonGen = self.fl(limit=limit, filters=filters)
          next(commonGen)

          for m in commonGen:
              results['fl']['movies'].extend(m['movies'])

      for m in goldenGen:
          results['fl']['golden'].extend(m['movies'])

      return results

def _fmtMovies(movies, printFL=True, detailed=True):
    i = 1
    msg = ""
    for m in movies:
        if len(m['Torrents']) == 0:
            continue
        msg += "[{1}] {0[Title]} - {0[Year]}".format(m, i)
        if detailed:
            msg += "\n\t Tags: {}".format(', '.join(m["Tags"]))

            for t in m['Torrents']:
                msg += "\n\t {0[Codec]}/{0[Container]}/{0[Source]}/{0[Resolution]}\t [ {0[Seeders]} | {0[Leechers]} ]\t Golden? {1}".format(t, "Y" if t["GoldenPopcorn"] else "N")
                if printFL:
                    msg += "\t Freeleech? {}".format("Y" if t.get("FreeleechType") is not None else "N")
            msg += "\n\t {0[Cover]}".format(m)
            msg += "\n"

        i += 1
        if i != len(movies) + 1:
            msg += "\n"

    return msg

def parse_ptp(ptp, args, returnJson=False):
    msg = ""
    if args.action == "freeleech" or args.action == "fl":
        if args.limit:
            limit = args.limit
        else:
            limit = -1

        filters = {
            "Resolution": args.resolution,
            "Codec": args.codec,
            "Container": args.container,
            "Source": args.source,
            "GoldenPopcorn": args.golden,
        }

        ptpresults = ptp.fl(limit=limit, filters=filters)
        total = next(ptpresults).get('total', 0)
        if returnJson:
            results = {"total": total, "movies": []}
            for r in ptpresults:
                flMovies = []
                for m in r.get('movies', []):
                    m['Torrents'] = list(filter(lambda t: t.get('FreeleechType', False) is not False, m['Torrents']))
                    flMovies.append(m)
                results['movies'] += flMovies

            results['returned'] = len(results['movies'])

            return results
        else:
            msg += "Currently freeleech ({}):\n".format(total)
            for r in ptpresults:
                flMovies = []
                for m in r.get('movies', []):
                    m['Torrents'] = list(filter(lambda t: t.get('FreeleechType', False) is not False, m['Torrents']))
                    flMovies.append(m)

                msg += _fmtMovies(flMovies, printFL=False)
    elif args.action == "ratio" or args.action == "r":
        results = ptp.ratio()
        if returnJson:
            return {"ratio": results}
        else:
            msg += "Ratio: {}\n".format(results)
    elif args.action == "bonus" or args.action == "bp":
        results = ptp.bonus()
        if returnJson:
            return {"bonus": results}
        else:
            msg += "Bonus: {}\n".format(results)
    elif args.action == "bonus-rate" or args.action == "bprate":
        results = ptp.bonus_rate()
        if returnJson:
            return {"bprate": results}
        else:
            msg += "Bp/h: {}\n".format(results)
    elif args.action == "uploaded" or args.action == "up":
        results = ptp.uploaded()
        if returnJson:
            return {"uploaded": results}
        else:
            msg += "Uploaded: {}\n".format(results)
    elif args.action == "downloaded" or args.action == "down":
        results = ptp.downloaded()
        if returnJson:
            return {"downloaded": results}
        else:
            msg += "Downloaded: {}\n".format(results)
    elif args.action == "hnrs":
        results = ptp.hnrs()
        if returnJson:
            return {"hnrs": results}
        else:
            msg += "HnRs: {}\n".format(results)
    elif args.action == "search" or args.action == "s":
        query = args.query

        if args.limit:
            limit = args.limit
        else:
            limit = 50

        if limit == -1:
            limit = 50

        filters = {
            "Resolution": args.resolution,
            "Codec": args.codec,
            "Container": args.container,
            "Source": args.source,
            "GoldenPopcorn": args.golden
        }

        ptpresults = ptp.search(query=query, limit=limit, filters=filters)
        total = next(ptpresults).get('total', 0)
        if returnJson:
            results = {"total": total, "movies": []}
            for r in ptpresults:
                results['movies'] += r.get('movies', [])

            results['returned'] = len(results['movies'])

            return results
        else:
            msg += "Movies ({}):\n".format(total)
            i = 0
            for r in ptpresults:
                msg += _fmtMovies(r.get('movies', []))
    elif args.action == "summary" or args.action == "sum":
        if args.limit:
            limit = args.limit
        else:
            limit = -1

        filters = {
            "Resolution": args.resolution,
            "Codec": args.codec,
            "Container": args.container,
            "Source": args.source,
        }

        ptpresults = ptp.summary(limit=limit, filters=filters, filterGoldens=args.golden)
        if returnJson:
            return ptpresults
        else:
            msg += "Current PTP Information\n\n"

            headers = [
                ["Ratio", "Up", "Down", "Buffer", "Seeding"],
                ["Bonus", "BPRate", "HNRs"]
            ]

            for h in headers:
                table = [[ptpresults.get(x.lower()) for x in h]]
                msg += tabulate.tabulate(table, h, tablefmt="pretty")
                msg += "\n\n"

            fl = ptpresults.get('fl', {})
            msg += "Currently freeleech ({}|{}):\n".format(len(fl.get('movies', [])), fl.get('total', 0))
            msg += _fmtMovies(fl.get('movies', []), printFL=True, detailed=args.detailed)
            msg += "\n\n"
            msg += "Currently golden freeleech ({}):\n".format(len(fl.get('golden', [])))
            msg += _fmtMovies(fl.get('golden', []))

    else:
        msg += "Action '{}' is not implemented yet!".format(args.action)

    return msg

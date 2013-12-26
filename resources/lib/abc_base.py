import abc
import re
from BeautifulSoup import BeautifulSoup
from BeautifulSoup import BeautifulStoneSoup
import resources.lib.util as util


class BaseForum(object):
    __metaclass__ = abc.ABCMeta

    short_name = 'base'
    long_name = 'Base Forum'
    local_thumb = ''
    base_url = ''

###############################################

    def get_show_menu(self, language):
        ''' Get list of shows for selected country'''

        url = '{base}{lang}season1/config/config.xml'.format(
            base=self.base_url, lang=language)

        print 'Get shows menu: {url}'.format(url=url)

        data = util.get_remote_data(url)
        soup = BeautifulStoneSoup(data, convertEntities=BeautifulSoup.XML_ENTITIES)

        items = []

        for item in soup.seasons.findAll('season'):
            t = item['text']
            r = re.compile('\d+').findall(t)
            pk = r[0]

            url = '{base}{lang}season{season}'.format(
                base=self.base_url, lang=language, season=pk)

            items.append({
                'label': t,
                'url': url,
                'pk': pk
            })

            print  t.encode('utf-8')


        print '------------------'
        print 'items from scraper'
        print items
        print '------------------'

        return items

    def get_season_menu(self, base_url):
        ''' Get list of entries for selected season'''

        url = '{base}/config/menu-main.xml'.format(
            base=base_url)

        print 'Get seasons menu: {url}'.format(url=url)

        data = util.get_remote_data(url)
        soup = BeautifulStoneSoup(data, convertEntities=BeautifulSoup.XML_ENTITIES)

        items = []

        for item in soup.menu_item_sub.findAll('sub_item'):
            t = item['text']
            l = item['url']
            pk = item['id']

            r = re.compile('\d+').findall(t)
            if r:
                pk = r[0]

            lnk = '{base}/{page}'.format(
                base=base_url, page=l)

            items.append({
                'label': t,
                'url': lnk,
                'pk': pk
            })
        return items

    def get_episode_menu(self, base_url, url):
        ''' Get list of entries for selected episode'''

        print 'Get episode menu: {url}'.format(url=url)

        data = util.get_remote_data(url)
        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.ALL_ENTITIES)

        items = []

        vidlist = soup.find('div', attrs={'class': 'vidlistcon'})
        for item in vidlist.ul.findAll('li'):
            pk = item.a['name']
            txt = ''.join(item.a.findAll(text=True))

            lnk = item.a['rel']
            r = re.compile('(.+?)\?').findall(lnk)
            if r:
                lnk = r[0]

            tb = item.a.span.img['src']

            thumb = '{base}/{img}'.format(base=base_url, img=tb)

            desc = ''
            icontainer = soup.find('ul', {'class': 'songInfo'})
            info = icontainer.find('li', {'class': pk})
            if info.p:
                desc = info.p.contents[0].encode('utf-8', 'ignore')

            items.append({
                'label': txt,
                'url': lnk,
                'thumb': thumb,
                'pk': pk,
                'plot': desc,
            })

        return items

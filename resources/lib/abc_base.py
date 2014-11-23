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

    # used to build config file link
    # pk site removed previous seasons and has different link
    default_season = 1

###############################################
    def get_season_config_file(self, language):
        ''' Get config file for selected country '''
        url = '{base}{lang}season{default_season}/config/config.xml'.format(
            base=self.base_url, lang=language, default_season=self.default_season)

        print 'Get config file: {url}'.format(url=url)

        return url

    def get_season_menu(self, siteid, language):
        ''' Get list of seasons for selected country'''
        url = self.get_season_config_file(language)

        print 'Get season menu: {url}'.format(url=url)

        data = util.get_remote_data(url)
        soup = BeautifulStoneSoup(data, convertEntities=BeautifulSoup.XML_ENTITIES)

        items = []

        if soup.seasons is None:
            items.append({
                'label': 'Season {default_season}'.format(
                    default_season=self.default_season),
                'url': '{base}{lang}season{season}'.format(
                    base=self.base_url, lang=language, season=self.default_season),
                'pk': self.default_season
                })
        else:
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

        return items

    def get_show_config_file(self, language):
        ''' Get config file for selected country '''
        url = '{base}{lang}season{default_season}/config/menu-main.xml'.format(
            base=self.base_url, lang=language, default_season=self.default_season)

        print 'Get main menu file: {url}'.format(url=url)

        return url

    def get_show_menu(self, language, base_url):
        ''' Get list of shows for selected season'''

        url = self.get_show_config_file(language)

        print 'Get show menu: {url}'.format(url=url)

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
            if icontainer:
                info = icontainer.find('li', {'class': pk})
                if info.p:
                    desc = info.text.encode('utf-8', 'ignore')

            items.append({
                'label': txt,
                'url': lnk,
                'thumb': thumb,
                'pk': pk,
                'plot': desc,
            })

        return items

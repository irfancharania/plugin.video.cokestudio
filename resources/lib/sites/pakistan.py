from resources.lib.abc_base import BaseForum
import re
from BeautifulSoup import BeautifulSoup
import resources.lib.util as util


class PakistanApi(BaseForum):
    short_name = 'pk'
    long_name = 'Pakistan'
    local_thumb = 'thumb_pakistan.png'

    base_url = 'http://www.cokestudio.com.pk/'
    default_season = 7

###############################################

    def get_episode_menu(self, base_url, url):
        ''' Get list of entries for selected episode'''

        print 'Get episode menu: {url}'.format(url=url)

        data = util.get_remote_data(url)
        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.ALL_ENTITIES)

        items = []

        vidlist = soup.find('div', attrs={'class': 'thumbnails scroll-pane'})
        for item in vidlist.ul.findAll('li'):
            pk = item.a['href']
            txt = ''.join(item.a.findAll(text=True)).strip()

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

from xbmcswift2 import Plugin, xbmcgui
from resources.lib.abc_base import BaseForum
from resources.lib.sites import *
import resources.lib.util as util
from operator import itemgetter


bookmark_storage = 'my_bookmarks'
temp_storage = 'temp_storage'

plugin = Plugin()

LANG = {
    'me': plugin.get_setting(
        'lang_me', choices=('en_ME/', 'ar_ME/')),
    'ke': plugin.get_setting(
        'lang_ke', choices=('en_KE/', 'fr_KE/', 'sw_KE/')),
    'ng': plugin.get_setting(
        'lang_ng', choices=('en_NG/', 'fr_NG/')),
    'tz': plugin.get_setting(
        'lang_tz', choices=('en_TZ/', 'sw_TZ/')),
    'ug': plugin.get_setting(
        'lang_ug', choices=('en_UG/', 'sw_UG/')),
}

STRINGS = {
    'url_resolver_settings': 30100,
    'try_again': 30050,
    'site_unavailable': 30051,
    'is_unavailable': 30052,
    'try_again_later': 30053,
    'no_seasons': 30056,
    'no_episodes': 30056,
    'no_valid_links': 30057,
    'cannot_play': 30058,
    'bookmarks': 30110,
    'add_bookmark': 30111,
    'remove_bookmark': 30112,
    'no_bookmarks': 30113,
    'bookmark_success': 30114,
    'bookmark_storage_fail': 30115,
    'bookmark_error': 30116,
    'bookmark_remove_question': 30117,
}


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id


###############################################


@plugin.route('/')
def index():
    items = [{
        'label': sc.long_name,
        'path': plugin.url_for(
            'get_show_menu', siteid=index,
            cls=sc.__name__),
        'thumbnail': util.get_image_path(sc.local_thumb),
        'icon': util.get_image_path(sc.local_thumb),
        } for index, sc in enumerate(BaseForum.__subclasses__())]

    by_label = itemgetter('label')
    items = sorted(items, key=by_label)

    # insert bookmarks at top
    items.insert(0, {
        'label': '[B]{txt}[/B]'.format(txt=_('bookmarks')),
        'path': plugin.url_for('show_bookmarks'),
        'thumbnail': util.get_image_path('bookmark.png')})

    # add url resolver settings at bottom
    thumb = util.get_image_path('settings.png')
    items.append({
        'label': '[COLOR white]{txt}[/COLOR]'.format(
            txt=_('url_resolver_settings')),
        'path': plugin.url_for('get_urlresolver_settings'),
        'thumbnail': thumb,
        'icon': thumb
        })
    return items


###############################################


@plugin.route('/bookmarks/')
def show_bookmarks():
    def context_menu(item_path):
        context_menu = [(
            _('remove_bookmark'),
            'XBMC.RunPlugin(%s)' % plugin.url_for('remove_bookmark',
                                                  item_path=item_path,
                                                  refresh=True),
        )]
        return context_menu

    bookmarks = plugin.get_storage(bookmark_storage)
    items = bookmarks.values()

    for item in items:
        item['context_menu'] = context_menu(item['path'])
    if not items:
        items = [{
            'label': _('no_bookmarks'),
            'path': plugin.url_for('show_bookmarks'),
        }]

    return sorted(items, key=lambda x: x['label'].partition('-')[2])


@plugin.route('/bookmarks/add/<item_path>')
def add_bookmark(item_path):
    bookmarks = plugin.get_storage(bookmark_storage)

    if bookmarks is not None:
        if not item_path in bookmarks:
            temp = plugin.get_storage(temp_storage)
            item = temp[item_path]

            groupname = plugin.request.args['groupname'][0]
            if groupname:
                item['label'] = groupname + ' - ' + item['label']

            bookmarks[item_path] = item
        else:
            item = bookmarks[item_path]

        dialog = xbmcgui.Dialog()
        dialog.ok(_('add_bookmark'),
                  _('bookmark_success'),
                  '{label}'.format(label=item['label']))
    else:
        msg = [_('bookmark_storage_fail'), _('try_again')]
        plugin.log.error(msg[0])
        dialog = xbmcgui.Dialog()
        dialog.ok(_('bookmark_error'), *msg)


@plugin.route('/bookmarks/remove/<item_path>')
def remove_bookmark(item_path):
    bookmarks = plugin.get_storage(bookmark_storage)
    label = bookmarks[item_path]['label']

    dialog = xbmcgui.Dialog()
    if dialog.yesno(_('remove_bookmark'),
                    _('bookmark_remove_question'),
                    '{label}'.format(label=label)):

        plugin.log.debug('remove bookmark: {label}'.format(label=label))

        if item_path in bookmarks:
            del bookmarks[item_path]
            bookmarks.sync()
            xbmc.executebuiltin("Container.Refresh")


###############################################


def __add_listitem(items, groupname=''):
    '''
    Redirect all entries through here
    to add bookmark option in context menu and
    to add item info to temp storage
    '''
    def context_menu(item_path, groupname):
        context_menu = [(
            _('add_bookmark'),
            'XBMC.RunPlugin(%s)' % plugin.url_for(
                endpoint='add_bookmark',
                item_path=item_path,
                groupname=groupname
            ),
        )]
        return context_menu

    temp = plugin.get_storage(temp_storage)
    temp.clear()
    for item in items:
        temp[item['path']] = item
        item['context_menu'] = context_menu(item['path'], groupname)
    temp.sync()
    return items


def get_cached(func, *args, **kwargs):
    '''Return the result of func with the given args and kwargs
    from cache or execute it if needed'''
    @plugin.cached(kwargs.pop('TTL', 1440))
    def wrap(func_name, *args, **kwargs):
        return func(*args, **kwargs)
    return wrap(func.__name__, *args, **kwargs)


###############################################


@plugin.route('/urlresolver/')
def get_urlresolver_settings():
    import urlresolver
    urlresolver.display_settings()
    return


@plugin.route('/sites/<siteid>-<cls>/')
def get_show_menu(siteid, cls):
    siteid = int(siteid)
    api = BaseForum.__subclasses__()[siteid]()
    lang = LANG.get(api.short_name, '')

    plugin.log.debug('browse site: {site}'.format(site=cls))

    # check if site is available
    if api.base_url:
        available = util.is_site_available(api.base_url)

        if available:
            items = []

            # get list of seasons
            data = get_cached(api.get_show_menu, lang)

            if data:
                items = [{
                    'label': item['label'].encode('utf-8'),
                    'path': plugin.url_for(
                        'get_season_menu', siteid=siteid, cls=cls,
                        seasonid=item['pk'], url=item['url'])
                } for item in data]

                return __add_listitem(groupname=api.short_name, items=items)

            else:
                msg = '[B][COLOR red]{txt}[/COLOR][/B]'.format(
                    txt=_('no_seasons'))
                plugin.log.error(msg)
                dialog = xbmcgui.Dialog()
                dialog.ok(api.long_name, msg)

        else:
            msg = [
                '[B][COLOR red]{txt}[/COLOR][/B]'.format(
                    txt=_('site_unavailable')),
                '{site} {txt}'.format(
                    site=api.long_name, txt=_('is_unavailable')),
                _('try_again_later')]
            plugin.log.error(msg[1])

            dialog = xbmcgui.Dialog()
            dialog.ok(api.long_name, *msg)
    else:
        msg = 'Base url not implemented'
        plugin.log.error(msg)
        raise Exception(msg)


@plugin.route('/sites/<siteid>-<cls>/<seasonid>/')
def get_season_menu(siteid, cls, seasonid):
    siteid = int(siteid)
    base_url = plugin.request.args['url'][0]
    api = BaseForum.__subclasses__()[siteid]()
    # lang = LANG.get(api.short_name, '')

    plugin.log.debug('browse season: {season}'.format(season=seasonid))

    items = []

    data = get_cached(api.get_season_menu, base_url)

    if data:
        items = [{
            'label': item['label'],
            'path': plugin.url_for(
                'get_episode_menu', siteid=siteid, cls=cls,
                seasonid=seasonid, episodeid=item['pk'],
                base_url=base_url, url=item['url'])
        } for item in data]

        grouping = api.short_name + ' - s' + seasonid + ' '
        return __add_listitem(groupname=grouping, items=items)
    else:
        msg = '[B][COLOR red]{txt}[/COLOR][/B]'.format(
            txt=_('no_episodes'))
        plugin.log.error(msg)
        dialog = xbmcgui.Dialog()
        dialog.ok(api.long_name, msg)


@plugin.route('/sites/<siteid>-<cls>/<seasonid>/ep<episodeid>/')
def get_episode_menu(siteid, cls, seasonid, episodeid):
    siteid = int(siteid)
    base_url = plugin.request.args['base_url'][0]
    url = plugin.request.args['url'][0]
    api = BaseForum.__subclasses__()[siteid]()
    # lang = LANG.get(api.short_name, '')

    plugin.log.debug('browse episode: {episode}'.format(episode=url))

    items = []

    data = api.get_episode_menu(base_url, url)

    if data:
        items = [{
            'label': item['label'],
            'thumbnail': item['thumb'],
            'icon': item['thumb'],
            'info': {
                'plot': item['plot']
            },
            'path': plugin.url_for(
                'play_video', siteid=siteid, cls=cls,
                seasonid=seasonid, episodeid=episodeid,
                videoid=item.get('pk', 0), url=item['url']),
            'is_playable': True
        } for item in data]

        # Add continuous play to top
        # if more than 1 item
        if len(items) > 1:
            # save post data to temp
            temp = plugin.get_storage(temp_storage)
            temp.clear()
            temp['items'] = data

            items.insert(0, {
                'label': '[B][COLOR white]Continuous Play[/COLOR][/B]',
                'path': plugin.url_for(
                    'play_video_continuous', siteid=siteid, cls=cls,
                    seasonid=seasonid, episodeid=episodeid,
                    videoid=item.get('pk', 0), url=item['url']),
                'is_playable': True
            })

        return items
    else:
        msg = '[B][COLOR red]{txt}[/COLOR][/B]'.format(
            txt=_('no_valid_links'))
        plugin.log.error(msg)
        dialog = xbmcgui.Dialog()
        dialog.ok(api.long_name, msg)


@plugin.route('/sites/<siteid>-<cls>/<seasonid>/ep<episodeid>/all')
def play_video_continuous(siteid, cls, seasonid, episodeid):
    siteid = int(siteid)
    # api = BaseForum.__subclasses__()[siteid]()

    temp = plugin.get_storage(temp_storage)
    data = temp['items']

    items = []

    for video in data:
        url = __resolve_item(video['url'], video['label'])
        plugin.log.debug('play video: {url}'.format(url=url))

        items.append({
            'label': 'Continuous Play: {label}'.format(label=video['label']),
            'thumbnail': video['thumb'],
            'icon': video['thumb'],
            'info': {
                'plot': video['plot']
            },
            'path': url
            })

    xbmc.PlayList(xbmc.PLAYLIST_VIDEO).clear()
    plugin.add_to_playlist(items)

    # Setting resolved url for first item
    # otherwise playlist seems to skip it
    plugin.set_resolved_url(items[0])


@plugin.route('/sites/<siteid>-<cls>/<seasonid>/ep<episodeid>/<videoid>')
def play_video(siteid, cls, seasonid, episodeid, videoid):
    siteid = int(siteid)
    url = plugin.request.args['url'][0]
    api = BaseForum.__subclasses__()[siteid]()

    # print 'resolve video: {url}'.format(url=url)
    plugin.log.debug('resolve video: {url}'.format(url=url))
    media = __resolve_item(url, videoid)

    # print 'resolved to: {url}'.format(url=media)

    if media:
        plugin.set_resolved_url(media)
    else:
        msg = [_('cannot_play')]
        plugin.log.error(msg[0])
        dialog = xbmcgui.Dialog()
        dialog.ok(api.long_name, *msg)


def __resolve_item(url, title):
    import urlresolver
    media = urlresolver.HostedMediaFile(
        url=url, title=title)
    return media.resolve()

###############################################


if __name__ == '__main__':
    try:
        plugin.run()
    except Exception, e:
        plugin.log.error(e)
        plugin.notify(msg=e)

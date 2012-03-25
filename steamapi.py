from datetime import datetime
from urllib import urlopen, urlencode
from simplejson import loads
import re, sys

API_HOST = 'http://api.steampowered.com'
APP_IDS = {
    'tf2':  440,
    'tf2beta':  520,
    'portal2':  620,
    }

class SteamAPIClient:
    
    def __init__(self, api_key, lang=None):
        self.api_key = api_key
        self.language = lang
        self.base_schemas = {}
        
    def send_request(self, path, params):
        params.update({
            'key': self.api_key,
            'format': 'json',
        })
        url = API_HOST + path + '?' + urlencode(params)
        rsp = urlopen(url)
        data = loads(rsp.read())
        data['last-modified'] = datetime.strptime(rsp.headers['last-modified'],
            '%a, %d %b %Y %H:%M:%S %Z')
        return data

    def get_schema(self, app_id, lang=None):
        path = '/IEconItems_%s/GetSchema/v0001/' % app_id
        params = {
            'language': lang or self.language,
            }
        return self.send_request(path, params)

    def get_player_items(self, app_id, steam_id):
        path = '/IEconItems_%s/GetPlayerItems/v0001/' % app_id
        params = {
            'steamid': steam_id,
            }
        return self.send_request(path, params)

    def get_asset_prices(self, app_id, lang=None):
        path = '/ISteamEconomy/GetAssetPrices/v0001/'
        params = {
            'appid': app_id,
            'language': lang or self.language,
            }
        return self.send_request(path, params)

    def get_asset_class_info(self, app_id, class_ids, lang=None):
        path = '/ISteamEconomy/GetAssetClassInfo/v0001/'
        params = {
            'appid': app_id,
            'language': lang or self.language,
            'class_count': len(class_ids),
            }
        for i, class_id in enumerate(class_ids):
            params['classid%s' % i] = class_id
        return self.send_request(path, params)

    def resolve_vanity_url(self, custom_name):
        path = '/ISteamUser/ResolveVanityURL/v0001/'
        params = {
            'vanityurl': custom_name,
            }
        return self.send_request(path, params)

    def get_news_for_app(self, app_id, count=20, length=255):
        path = '/ISteamNews/GetNewsForApp/v0002'
        params = {
            'appid': app_id,
            'count': count,
            'length': length,
            }
        return self.send_request(path, params)

    def get_global_achievement_percentages_for_app(self, game_id):
        path = '/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002'
        params = {
            'gameid': game_id,
            }
        return self.send_request(path, params)

    def get_player_summaries(self, steam_ids):
        path = '/ISteamUser/GetPlayerSummaries/v0002/'
        params = {
            'steamids': ','.join([str(x) for x in steam_ids]),
            }
        return self.send_request(path, params)

    def get_friend_list(self, steam_id, relationship='all'):
        path = '/ISteamUser/GetFriendList/v1'
        params = {
            'steamid': steam_id,
            'relationship': relationship,
            }
        return self.send_request(path, params)

    def get_server_schema(self, app_id):
        schema = self.get_schema(app_id)['result']
        url = schema['items_game_url']
        rsp = urlopen(url)
        schema = parse_schema(rsp)
        return schema

    def get_translation(self, app_id, lang='en_US'):
        if not self.base_schemas.get(app_id):
            self.base_schemas[app_id] = self.get_schema(app_id, None)
        translations = {}
        tokens = extract_tokens(self.base_schemas[app_id])
        schema = client.get_schema(app_id, lang)
        for path,token in tokens:
            trans = extract_token_by_path(schema, path)
            translations[token] = trans
        return translations

def extract_tokens(data, path=[]):
    tokens = []
    if type(data) == dict:
        gen = data.items()
    elif type(data) == list:
        gen = enumerate(data)
    else:
        raise Exception('non dict/list passed to extract_tokens')

    for k,v in gen:
        if type(v) in [dict,list]:
            tokens.extend(extract_tokens(v, path + [k]))
        elif isinstance(v, basestring):
            if v.startswith('#'):
                tokens.append( (path + [k], v) )
    return tokens
    
def extract_token_by_path(schema, path):
    obj = schema
    for node in path:
        if type(node) == int:
            obj = obj[node]
        elif isinstance(node, basestring):
            obj = obj.get(node)
    return obj.encode('utf8')

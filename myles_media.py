"""Owner-only media discovery and persistent, observed browser playback.

No account secrets are read by this module. Authentication stays inside the
browser's native profile. Preferences are an allowlist, never model memory.
"""
from __future__ import annotations
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, urlencode

SERVICES = {'paramount+': 'https://www.paramountplus.com/',
            'south park studios': 'https://www.southparkstudios.com/',
            'disney+': 'https://www.disneyplus.com/', 'hulu': 'https://www.hulu.com/',
            'netflix': 'https://www.netflix.com/', 'youtube': 'https://www.youtube.com/',
            'tubi': 'https://tubitv.com/', 'pluto tv': 'https://pluto.tv/'}
DOMAINS = tuple(urlsplit(u).hostname.removeprefix('www.') for u in SERVICES.values()) + ('southparkstudios.nu',)
TEST_VIDEO = 'https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4'

def safe_url(url):
    p = urlsplit(str(url))
    host = p.hostname or ''
    if p.scheme != 'https' or p.username or p.password or p.port not in (None, 443):
        return ''
    if not any(host == d or host.endswith('.'+d) for d in DOMAINS) and url != TEST_VIDEO:
        return ''
    # No session-bearing queries are persisted or returned in chat.
    return urlunsplit((p.scheme, p.netloc, p.path, '', ''))

def media_request(text):
    value = re.sub(r'(?i)^(?:myles[, ]+|please\s+)', '', str(text).strip()).strip(' .?!')
    lower = value.casefold()
    controls = {'pause': 'pause', 'pause the video': 'pause', 'pause playback': 'pause',
                'resume': 'resume', 'resume playback': 'resume', 'resume the video': 'resume',
                'play the video': 'resume', 'mute': 'mute', 'mute the video': 'mute',
                'unmute': 'unmute', 'unmute the video': 'unmute', 'stop playback': 'stop',
                'stop the video': 'stop', 'make it fullscreen': 'fullscreen',
                'fullscreen': 'fullscreen', 'enter fullscreen': 'fullscreen'}
    if lower in controls: return {'kind': 'control', 'action': controls[lower]}
    volume = re.fullmatch(r'(?:set |change )?(?:the )?volume (?:to )?(\d{1,3})\s*%?', lower)
    if volume: return {'kind': 'control', 'action': 'volume', 'volume': min(100,int(volume[1]))/100}
    if lower in {'media preferences', 'my streaming services', 'media status'}:
        return {'kind': 'preferences' if lower != 'media status' else 'control', 'action': 'status'}
    pref = re.fullmatch(r'(?:my streaming services are|prefer streaming services) (.+)', lower)
    if pref: return {'kind': 'preferences', 'services': pref[1]}
    region = re.fullmatch(r'set media region (US|GB|CA|AU|DE|FR|MX)', value, re.I)
    if region: return {'kind': 'preferences', 'region': region[1].upper()}
    browser = re.fullmatch(r'use (edge|chrome) for media', lower)
    if browser: return {'kind': 'preferences', 'browser': 'msedge' if browser[1]=='edge' else 'chrome'}
    if lower == 'play the test video': return {'kind':'test', 'play':True}
    follow = re.fullmatch(r'(?:play|start) (?:the )?(first|latest|next|\d+)(?: episode)?', lower)
    if follow: return {'kind':'discover', 'follow':True, 'episode': follow[1], 'play':True}
    if lower == 'find a free legal episode':
        return {'kind':'discover', 'follow':True, 'free':True, 'play':False}
    service = next((s for s in SERVICES if lower.startswith('open '+s)), None)
    if service: return {'kind':'service','service':service,'play': 'continue' in lower}
    youtube = re.fullmatch(r'(?:find|play|search for) (?:a )?youtube video (?:about |explaining )?(.+)', value, re.I)
    if youtube: return {'kind':'youtube','title':youtube[1], 'play': lower.startswith('play')}
    find = re.fullmatch(r'(find|play|watch|start)\s+(.+)', value, re.I)
    if not find: return None
    title = find[2]
    # Only media-shaped finds; leave general file/project requests to existing tools.
    if find[1].lower() == 'find' and not re.search(r'(?i)movie|film|episode|show|south park|night at the museum|\band (?:play|start)',title):
        return None
    season = re.search(r'(?i)season\s+(\d+)', title)
    episode = re.search(r'(?i)(?:episode\s+(\d+)|(first|latest|next)\s+(?:south park\s+)?episode)', title)
    title = re.sub(r'(?i)\s+and\s+(?:play|start).*$', '', title)
    title = re.sub(r'(?i)\b(?:the latest|latest|first|season\s+\d+|episode\s+\d+|episode|movie|film|show)\b', '', title).strip(' .')
    return {'kind':'discover','title':title,'season':int(season[1]) if season else None,
            'episode':(episode[1] or episode[2]) if episode else None,
            'free':'free legal' in lower,'play':find[1].lower() in {'play','watch','start'} or bool(re.search(r'(?i)\band (play|start)',value))}

class MediaAssistant:
    def __init__(self, directory):
        self.directory=Path(directory)
        self.lock=threading.RLock()
        self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='myles-media-browser')
        self.pending=None; self.browser=None; self.page=None; self.pw=None
        self.playing_until=0
        self.context=self._load('media_context.json',{})
        self.preferences=self._load('media_preferences.json',{})
        self.preferences={k:v for k,v in self.preferences.items() if k in {'region','services','browser'}}
        self.preferences.setdefault('region','US');self.preferences.setdefault('services',[]);self.preferences.setdefault('browser','msedge')

    def _load(self,name,default):
        try: return json.loads((self.directory/name).read_text(encoding='utf-8'))
        except (ValueError,OSError): return default

    def _save(self,name,data):
        self.directory.mkdir(parents=True,exist_ok=True)
        path=self.directory/name;tmp=path.with_suffix('.tmp')
        tmp.write_text(json.dumps(data),encoding='utf-8');tmp.replace(path)

    def active(self): return self.playing_until > time.monotonic()

    def _call(self,command):
        with self.lock:
            if self.pending and not self.pending.done():
                return {'ok':False,'reply':'The media browser is finishing its previous bounded action. Try the control again shortly; it was not queued or executed twice.'}
            self.pending=self.pool.submit(self._browser_command,command)
            future=self.pending
        try:return future.result(timeout=35)
        except TimeoutError:
            future.cancel()
            return {'ok':False,'reply':'Media control timed out. Playback is unconfirmed; no automatic retry was sent.'}
        except Exception as exc:
            # Playwright exceptions can contain URLs. Do not return cookies/query strings.
            return {'ok':False,'reply':f'Media browser failed ({type(exc).__name__}). Check the controlled browser; no playback was verified.'}

    def handle(self,request):
        kind=request['kind']
        if kind=='preferences':
            with self.lock:
                if 'services' in request:
                    self.preferences['services']=[s for s in SERVICES if s in request['services'].lower()]
                for key in ('region','browser'):
                    if key in request:self.preferences[key]=request[key]
                self._save('media_preferences.json',self.preferences)
                return {'ok':True,'reply':f"Media region: {self.preferences['region']}. Preferred services: {', '.join(self.preferences['services']) or 'none saved'}. Browser: {self.preferences['browser']}. These preferences do not prove you are signed in. Sign in directly in Myles' media browser; passwords and cookies stay out of chat."}
        if kind=='control':return self._call(request)
        if kind=='test':return self._call({**request,'url':TEST_VIDEO})
        if kind=='service':return self._call({**request,'url':SERVICES[request['service']]})
        if kind=='youtube':
            return self._call({**request,'url':'https://www.youtube.com/results?'+urlencode({'search_query':request['title']})})
        with self.lock:
            context=dict(self.context)
        if request.get('follow'):
            if not context.get('title'):
                return {'ok':False,'reply':'Which movie or show should I use? No media title has been selected yet.'}
            request={**request,'title':context['title']}
        title=request.get('title','').strip()
        if not title:return {'ok':False,'reply':'Which movie or show should I find?'}
        from myles_quick import web_search
        # Always refresh current official evidence; never infer access from preferences.
        domains=' OR '.join('site:'+d for d in DOMAINS if d!='youtube.com')
        query=f'"{title}" watch full episodes movie {self.preferences["region"]} ({domains})'
        if 'south park' in title.lower():
            query='South Park full episodes (site:paramountplus.com OR site:southparkstudios.com) '+self.preferences['region']
        evidence=web_search(query,max_results=8)
        urls=list(dict.fromkeys(u for raw in evidence.source_urls if (u:=safe_url(raw))))
        if request.get('free'):
            urls=[u for u in urls if any(d in urlsplit(u).hostname for d in ('southparkstudios.com','tubitv.com','pluto.tv'))]
        urls.sort(key=lambda u: not any(urlsplit(SERVICES[s]).hostname in urlsplit(u).hostname for s in self.preferences['services']))
        if not urls:
            return {'ok':False,'reply':f'I could not verify a current official source for {title} in {self.preferences["region"]}. '+('No official free episode was verified.' if request.get('free') else evidence.error or 'The search returned no supported official catalog link.')}
        with self.lock:
            self.context={'title':title,'urls':urls[:8],'checked_at':time.time(),'region':self.preferences['region']}
            self._save('media_context.json',self.context)
        if not request.get('play'):
            return {'ok':True,'reply':f'Found official catalog results for {title} ({self.preferences["region"]}; playback and account access not yet verified):\n'+'\n'.join(urls[:3])+"\nSay ‘play the first episode’ or ‘play the latest episode’."}
        return self._call({**request,'url':urls[0]})

    def _ensure_browser(self):
        if self.page and not self.page.is_closed():return
        from playwright.sync_api import sync_playwright
        if not self.pw:self.pw=sync_playwright().start()
        # Reuse only this controlled profile, never copy/export another browser's cookies.
        profile=str(self.directory/'media_browser_profile')
        try:
            self.browser=self.pw.chromium.launch_persistent_context(profile,
                channel=self.preferences['browser'],headless=False,viewport=None,
                args=['--autoplay-policy=no-user-gesture-required'])
        except Exception:
            # A managed Edge/Chrome channel may be absent on a clean tower. The
            # bundled Playwright browser is still a controlled, isolated profile.
            self.browser=self.pw.chromium.launch_persistent_context(profile,
                headless=False,viewport=None,args=['--autoplay-policy=no-user-gesture-required'])
        self.page=self.browser.pages[0] if self.browser.pages else self.browser.new_page()
        self.page.set_default_timeout(3000)
        self.page.set_default_navigation_timeout(12000)

    def _observe(self):
        observations=[]
        for frame in self.page.frames:
            try:
                rows=frame.locator('video, audio').evaluate_all("els => els.map(v=>({paused:v.paused,time:v.currentTime,ready:v.readyState,muted:v.muted,volume:v.volume,ended:v.ended,error:v.error?.code||null}))")
                observations.extend((frame,index,row) for index,row in enumerate(rows))
            except Exception:continue
        return observations

    def _verify_playing(self):
        before=self._observe();self.page.wait_for_timeout(900);after=self._observe()
        playing=any(not b['paused'] and not b['ended'] and b['ready']>=2 and b['time']>a['time']+.1 for (_,_,a),(_,_,b) in zip(before,after))
        self.playing_until=time.monotonic()+45 if playing else 0
        return playing

    def _browser_command(self,command):
        action=command.get('action');kind=command['kind']
        if kind=='control' and (not self.page or self.page.is_closed()):
            self.playing_until=0
            return {'ok':False,'reply':'No controlled media player is open. Ask me to find a movie or play a video first.'}
        self._ensure_browser()
        if kind!='control':
            url=command['url']
            # YouTube searches are built locally; all other navigation must be official.
            if not safe_url(url):return {'ok':False,'reply':'The media address is not a supported official provider.'}
            try:self.page.goto(url,wait_until='domcontentloaded',timeout=12000)
            except Exception as exc:
                return {'ok':False,'reply':f'The official page did not finish loading ({type(exc).__name__}). The browser remains available for another request; playback is unconfirmed.'}
            if not safe_url(self.page.url):return {'ok':False,'reply':'The provider redirected outside supported official sites. Owner review is required; no playback action was sent.'}
            if kind=='youtube':
                link=self.page.locator('a#video-title').first
                if not command.get('play'):return {'ok':True,'reply':'Opened YouTube search results in the media browser. No video is claimed playing.'}
                if link.count():link.click(timeout=3000)
            if command.get('play'):
                episode=command.get('episode');season=command.get('season')
                if episode or season:
                    if season:
                        select=self.page.locator('select').first
                        if select.count():
                            try:select.select_option(label=f'Season {season}',timeout=2000)
                            except Exception:pass
                    links=self.page.locator('a').evaluate_all("els=>els.map(a=>({text:a.innerText,url:a.href})).filter(a=>a.text&&a.url)")
                    candidates=[]
                    for link in links:
                        match=re.search(r'\bS(\d+)\s*(?:\(Season \d+\))?\s*E(\d+)\b',link['text'],re.I)
                        if match and safe_url(link['url']):candidates.append((int(match[1]),int(match[2]),link['url']))
                    if season:candidates=[c for c in candidates if c[0]==int(season)]
                    if episode and str(episode).isdigit():candidates=[c for c in candidates if c[1]==int(episode)]
                    if candidates:
                        chosen=sorted(candidates,reverse=episode=='latest')[0]
                        self.page.goto(chosen[2],wait_until='domcontentloaded',timeout=12000)
                    elif episode:
                        return {'ok':False,'reply':'Opened the official catalog, but could not identify the requested episode from its actual links. No arbitrary episode was started.'}
                # Only playback buttons. Never click purchase, subscription, login, MFA or consent controls.
                button=self.page.get_by_role('button',name=re.compile(r'^(play|play now|watch now|resume|continue watching)$',re.I)).first
                if button.count() and button.is_visible():
                    try:button.click(timeout=3000)
                    except Exception:pass
                for frame,index,row in self._observe():
                    try:frame.locator('video, audio').nth(index).evaluate('v=>v.play().catch(()=>null)')
                    except Exception:pass
                if self._verify_playing():return {'ok':True,'reply':'Playback started. The player time is advancing.','media_state':'playing'}
            text=self.page.locator('body').inner_text(timeout=3000)[:18000].lower()
            blockers=[label for pattern,label in [(r'captcha|verify you are human','CAPTCHA requires owner interaction'),(r'not available in your (?:country|region)|geo.?restricted','regional availability restriction'),(r'sign in to watch|log in to watch|sign in to continue','sign-in required'),(r'subscribe to watch|start your free trial|choose a plan|subscription','subscription or account access required'),(r'drm|protected content|unsupported browser','protected playback or browser limitation')] if re.search(pattern,text)]
            reason='; '.join(blockers) or 'No supported player was verified. Sign-in, service navigation or protected playback may require owner interaction in the media browser.'
            return {'ok':not command.get('play'),'reply':'Opened the official website. Playback was not verified. '+reason,'media_state':'blocked' if command.get('play') else 'opened'}
        if action=='status':
            playing=self._verify_playing()
            return {'ok':True,'reply':'The controlled player is playing.' if playing else 'No advancing playback was observed.','media_state':'playing' if playing else 'paused'}
        players=self._observe()
        if not players:return {'ok':False,'reply':'No supported video or audio player was found in the controlled page. No other application was changed.'}
        frame,index,row=next((v for v in players if not v[2]['paused']),players[0]);player=frame.locator('video, audio').nth(index)
        if action=='fullscreen':
            try:
                player.click(timeout=2000)
                player.evaluate('v=>v.requestFullscreen()')
                verified=frame.evaluate('!!document.fullscreenElement')
            except Exception:verified=False
            return {'ok':verified,'reply':'Fullscreen verified.' if verified else 'The browser did not grant fullscreen. Use the player fullscreen button in the controlled browser.'}
        scripts={'pause':'v=>v.pause()','stop':'v=>{v.pause();v.currentTime=0}',
                 'resume':'v=>v.play()','mute':'v=>v.muted=true','unmute':'v=>v.muted=false',
                 'volume':'(v,n)=>v.volume=n'}
        if action not in scripts:return {'ok':False,'reply':'Unsupported media control.'}
        try:player.evaluate(scripts[action],command.get('volume'))
        except Exception:return {'ok':False,'reply':'The player rejected this control. Playback was not verified.'}
        observed=player.evaluate('v=>({paused:v.paused,muted:v.muted,volume:v.volume,time:v.currentTime})')
        verified=self._verify_playing() if action=='resume' else observed['paused'] if action=='pause' else observed['paused'] and observed['time']<1 if action=='stop' else observed['muted']==(action=='mute') if action in {'mute','unmute'} else abs(observed['volume']-command['volume'])<.01
        if action in {'pause','stop'}:self.playing_until=0
        return {'ok':verified,'reply':f'{action.capitalize()} verified.' if verified else f'The player did not verify {action}.','media_state':action}

_assistant=None
def assistant():
    global _assistant
    if _assistant is None:
        from myles_common import DATA
        _assistant=MediaAssistant(DATA)
    return _assistant

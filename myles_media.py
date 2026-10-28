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
from urllib.parse import urlsplit, urlunsplit, urlencode, quote_plus

SERVICES = {'paramount+': 'https://www.paramountplus.com/',
            'south park studios': 'https://www.southparkstudios.com/',
            'disney+': 'https://www.disneyplus.com/', 'hulu': 'https://www.hulu.com/',
            'netflix': 'https://www.netflix.com/', 'youtube': 'https://www.youtube.com/',
            'tubi': 'https://tubitv.com/', 'pluto tv': 'https://pluto.tv/'}
MEDIA_BROWSER_CHANNEL = 'chrome'
SEARCH_URLS = {
    'youtube': 'https://www.youtube.com/results?search_query=',
    'hulu': 'https://www.hulu.com/search?q=',
    'netflix': 'https://www.netflix.com/search?q=',
    'disney+': 'https://www.disneyplus.com/search?q=',
    'paramount+': 'https://www.paramountplus.com/search/?q=',
}
WEB_SEARCH_HOSTS = ('google.com', 'bing.com', 'duckduckgo.com')
DOMAINS = tuple(urlsplit(u).hostname.removeprefix('www.') for u in SERVICES.values()) + ('southparkstudios.nu',)
TEST_VIDEO = 'https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4'
OFFICIAL_CATALOGS = {
    'south park': (
        'https://www.paramountplus.com/shows/south-park/',
        'https://www.southparkstudios.com/episodes',
    ),
    'night at the museum': (
        'https://www.disneyplus.com/browse/entity-29c89abf-b956-4893-add2-804ce0dbe5d7',
    ),
}

def safe_url(url):
    p = urlsplit(str(url))
    host = p.hostname or ''
    if p.scheme != 'https' or p.username or p.password or p.port not in (None, 443):
        return ''
    if not (any(host == d or host.endswith('.'+d) for d in DOMAINS)
            or any(host == d or host.endswith('.'+d) for d in WEB_SEARCH_HOSTS)) and url != TEST_VIDEO:
        return ''
    # No session-bearing queries are persisted or returned in chat.
    return urlunsplit((p.scheme, p.netloc, p.path, '', ''))


def _clean_youtube_title(title: str) -> str:
    """Normalize conversational newest/latest YouTube requests into a search title."""
    cleaned = re.sub(r'(?i)\b(?:latest|newest|most recent)\b', ' ', str(title))
    cleaned = re.sub(r'(?i)\b(?:youtube|video|videos)\b', ' ', cleaned)
    cleaned = re.sub(r'(?i)^\s*(?:the\s+)?(?:video\s+)?(?:from|by)\s+', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip(' .?!-')
    return cleaned or str(title).strip(' .?!')

def media_request(text):
    value = re.sub(r'(?i)^(?:myles[, ]+|please\s+)', '', str(text).strip()).strip(' .?!')
    lower = value.casefold()
    controls = {'pause': 'pause', 'pause video': 'pause', 'pause the video': 'pause',
                'pause playback': 'pause', 'pause the playback': 'pause',
                'resume': 'resume', 'resume video': 'resume', 'resume the video': 'resume',
                'resume playback': 'resume', 'resume the playback': 'resume',
                'play': 'resume', 'play video': 'resume', 'play the video': 'resume',
                'playback': 'status', 'check playback': 'status',
                'mute': 'mute', 'mute video': 'mute', 'mute the video': 'mute',
                'unmute': 'unmute', 'unmute video': 'unmute', 'unmute the video': 'unmute',
                'stop playback': 'stop', 'stop the playback': 'stop',
                'stop video': 'stop', 'stop the video': 'stop',
                'make it fullscreen': 'fullscreen',
                'make it full screen': 'fullscreen', 'fullscreen': 'fullscreen',
                'full screen': 'fullscreen', 'go fullscreen': 'fullscreen',
                'go full screen': 'fullscreen', 'go to full screen': 'fullscreen',
                'go to fullscreen': 'fullscreen', 'enter fullscreen': 'fullscreen',
                'enter full screen': 'fullscreen', 'put it in fullscreen': 'fullscreen',
                'put it in full screen': 'fullscreen',
                'exit fullscreen': 'exit_fullscreen', 'exit full screen': 'exit_fullscreen',
                'leave fullscreen': 'exit_fullscreen', 'leave full screen': 'exit_fullscreen',
                'take it out of fullscreen': 'exit_fullscreen',
                'take it out of full screen': 'exit_fullscreen',
                'turn off fullscreen': 'exit_fullscreen',
                'turn off full screen': 'exit_fullscreen'}
    if lower in controls: return {'kind': 'control', 'action': controls[lower]}
    if lower in {"it's still playing", 'it is still playing', 'is it still playing',
                 'did it pause', 'did it stop', 'what is playing', "what's playing"}:
        return {'kind': 'control', 'action': 'status'}
    if re.fullmatch(r'(?:make|put|switch)\s+(?:the\s+)?(?:video\s+)?(?:it\s+)?full\s*screen', lower):
        return {'kind': 'control', 'action': 'fullscreen'}
    if re.fullmatch(r'(?:skip|dismiss)\s+(?:(?:the|this|current|an?)\s+)?(?:ad|ads|advert|advertisement|advertisements)', lower):
        return {'kind': 'control', 'action': 'skip_ad'}
    volume = re.fullmatch(r'(?:set |change )?(?:the )?volume (?:to )?(\d{1,3})\s*%?', lower)
    if volume: return {'kind': 'control', 'action': 'volume', 'volume': min(100,int(volume[1]))/100}
    if lower in {'media preferences', 'my streaming services', 'media status'}:
        return {'kind': 'preferences' if lower != 'media status' else 'control', 'action': 'status'}
    pref = re.fullmatch(r'(?:my streaming services are|prefer streaming services) (.+)', lower)
    if pref: return {'kind': 'preferences', 'services': pref[1]}
    region = re.fullmatch(r'set media region (US|GB|CA|AU|DE|FR|MX)', value, re.I)
    if region: return {'kind': 'preferences', 'region': region[1].upper()}
    browser = re.fullmatch(r'use (edge|chrome|google chrome) for media', lower)
    if browser: return {'kind': 'preferences', 'browser': MEDIA_BROWSER_CHANNEL}
    if lower == 'play the test video': return {'kind':'test', 'play':True}
    if lower in {'play the song', 'play it', 'play that', 'play this', 'play the first result', 'play the first video'}:
        return {'kind':'youtube_follow', 'selection':'first', 'play':True}
    follow = re.fullmatch(r'(?:play|start) (?:the )?(first|latest|next|\d+)(?: episode)?', lower)
    if follow: return {'kind':'discover', 'follow':True, 'episode': follow[1], 'play':True}
    if lower == 'find a free legal episode':
        return {'kind':'discover', 'follow':True, 'free':True, 'play':False}
    # Preserve the title in natural requests such as "Open YouTube and play
    # a video called ...". The old service-prefix branch discarded the title.
    multi = re.fullmatch(
        r'open\s+(youtube|hulu|netflix|disney(?:\+| plus)|paramount\+?)\s+and\s+'
        r'(?:play|watch|find|search(?:\s+for)?)\s+(?:a\s+)?'
        r'(?:video|song|movie|show|episode|article)?\s*'
        r'(?:called|titled|about|on|for)?\s*(.+)', value, re.I)
    if multi:
        service = multi[1].casefold().replace('disney plus', 'disney+')
        if service not in SERVICES and service.rstrip('+') + '+' in SERVICES:
            service = service.rstrip('+') + '+'
        title = multi[2].strip(' .?!')
        if service == 'youtube':
            selection = 'latest' if re.search(r'(?i)\b(?:latest|newest|most recent)\b', title) else None
            title = _clean_youtube_title(title)
            result = {'kind':'youtube','title':title,'play':True}
            if selection: result['selection'] = selection
            return result
        if service in SERVICES and title:
            return {'kind':'service_search','service':service,'title':title,'play':True}
    on_service = re.fullmatch(
        r'(?:open|watch|play|find|search for)\s+(?:a\s+)?(?:movie|show|episode|video)?\s*(.+?)\s+on\s+'
        r'(youtube|hulu|netflix|disney(?:\+| plus)|paramount\+?)', value, re.I)
    if on_service:
        service = on_service[2].casefold().replace('disney plus', 'disney+')
        if service not in SERVICES and service.rstrip('+') + '+' in SERVICES:
            service = service.rstrip('+') + '+'
        title = on_service[1].strip(' .?!')
        if service == 'youtube':
            selection = 'latest' if re.search(r'(?i)\b(?:latest|newest|most recent)\b', title) else None
            title = _clean_youtube_title(title)
            result = {'kind':'youtube','title':title,'play':True}
            if selection: result['selection'] = selection
            return result
        if service in SERVICES:
            return {'kind':'service_search','service':service,'title':title,'play':True}
    article = re.fullmatch(
        r'(?:find|search for|look up|show me|open)\s+(?:an?\s+)?'
        r'(?:article|story|news|web page|page)\s+(?:about|on|for)?\s*(.+)', value, re.I)
    if article and article[1].strip():
        return {'kind':'web_search','title':article[1].strip(' .?!')}
    service = next((s for s in SERVICES if lower == 'open '+s), None)
    if service: return {'kind':'service','service':service,'play':False}
    youtube = re.fullmatch(r'(?:find|play|open|search for) (?:a )?youtube video (?:about |explaining )?(.+)', value, re.I)
    if youtube:
        title = youtube[1].strip(' .?!')
        selection = 'latest' if re.search(r'(?i)\b(?:latest|newest|most recent)\b', title) else None
        title = _clean_youtube_title(title)
        result = {'kind':'youtube','title':title, 'play': lower.startswith(('play','open'))}
        if selection: result['selection'] = selection
        return result
    find = re.fullmatch(r'(find|play|watch|start)\s+(.+)', value, re.I)
    if not find:
        general_search = re.fullmatch(r'(?:search for|look up)\s+(.+)', value, re.I)
        if general_search and general_search[1].strip():
            return {'kind':'web_search','title':general_search[1].strip(' .?!')}
        return None
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
        self.preferences.setdefault('region','US');self.preferences.setdefault('services',[])
        # Media automation is intentionally pinned to the owner's preferred
        # browser. Do not resurrect a stale Edge preference from an older
        # installation or let a model request switch the controlled browser.
        self.preferences['browser']=MEDIA_BROWSER_CHANNEL

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
                for key in ('region',):
                    if key in request:self.preferences[key]=request[key]
                self.preferences['browser']=MEDIA_BROWSER_CHANNEL
                self._save('media_preferences.json',self.preferences)
                return {'ok':True,'reply':f"Media region: {self.preferences['region']}. Preferred services: {', '.join(self.preferences['services']) or 'none saved'}. Browser: Google Chrome. These preferences do not prove you are signed in. Sign in directly in Myles' media browser; passwords and cookies stay out of chat."}
        if kind=='control':return self._call(request)
        if kind=='test':return self._call({**request,'url':TEST_VIDEO})
        if kind=='service':return self._call({**request,'url':SERVICES[request['service']]})
        if kind=='youtube':
            params={'search_query':request['title']}
            if request.get('selection') == 'latest':
                # YouTube's upload-date sort is exposed as this stable search
                # filter. The result is still clicked and playback-verified.
                params['sp']='CAI%3D'
            command={**request,'url':'https://www.youtube.com/results?'+urlencode(params)}
            result=self._call(command)
            if result.get('ok') and not request.get('play'):
                with self.lock:
                    self.context={'kind':'youtube','title':request['title'],'url':'https://www.youtube.com/results','checked_at':time.time()}
                    self._save('media_context.json',self.context)
            return result
        if kind=='service_search':
            service=request.get('service','')
            if service not in SEARCH_URLS:
                return {'ok':False,'reply':'That streaming service is not supported by the controlled browser.'}
            result=self._call({**request,'url':SEARCH_URLS[service]+quote_plus(request.get('title',''))})
            if result.get('ok'):
                with self.lock:
                    self.context={'kind':'service_search','service':service,'title':request.get('title',''),'url':SEARCH_URLS[service],'checked_at':time.time()}
                    self._save('media_context.json',self.context)
            return result
        if kind=='web_search':
            return self._call({**request,'url':'https://www.google.com/search?q='+quote_plus(request.get('title',''))})
        if kind=='youtube_follow':
            with self.lock:
                context=dict(self.context)
            if context.get('kind') != 'youtube' or not context.get('title'):
                return {'ok':False,'reply':'There is no earlier YouTube search in this conversation. Ask me to find a YouTube video first.'}
            return self._call({'kind':'youtube_follow','title':context['title'],'selection':request.get('selection','first'),'play':True})
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
        # Search engines can return consent or anti-bot shells. For named
        # examples, retain only the canonical official catalog pages we have
        # explicitly allowlisted; access and playback remain unverified.
        if not urls:
            urls=list(OFFICIAL_CATALOGS.get(title.casefold(), ()))
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
        # Keep Chrome's controlled profile separate from the old Edge profile.
        # This prevents Edge-only locks/extensions from poisoning the Chrome
        # player while keeping any legacy profile recoverable.
        profile=str(self.directory/'media_browser_profile_chrome')
        try:
            self.browser=self.pw.chromium.launch_persistent_context(profile,
                channel=MEDIA_BROWSER_CHANNEL,headless=False,viewport=None,
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

    def _click_visible(self, frame, selectors, role_name=None, timeout=3000):
        """Click one visible, semantic control and report whether it was sent."""
        for selector in selectors:
            try:
                controls = frame.locator(selector)
                for index in range(min(controls.count(), 8)):
                    control = controls.nth(index)
                    if control.is_visible():
                        control.click(timeout=timeout)
                        return True
            except Exception:
                continue
        if role_name:
            try:
                control = frame.get_by_role('button', name=re.compile(role_name, re.I)).first
                if control.count() and control.is_visible():
                    control.click(timeout=timeout)
                    return True
            except Exception:
                pass
        return False

    def _fullscreen_verified(self, player):
        try:
            if bool(self.page.evaluate('!!document.fullscreenElement')):
                return True
        except Exception:
            pass
        try:
            return bool(player.evaluate("v => !!(document.fullscreenElement || v.webkitDisplayingFullscreen === true)"))
        except Exception:
            return False

    def _enter_fullscreen(self, frame, player):
        """Use the provider's real fullscreen button, with keyboard fallback."""
        try:
            player.hover(timeout=1500)
        except Exception:
            pass
        self.page.wait_for_timeout(250)
        clicked = self._click_visible(
            frame,
            ('.ytp-fullscreen-button', '.vjs-fullscreen-control',
             '.plyr__control[data-plyr="fullscreen"]',
             'button[aria-label*="Full screen"]',
             'button[aria-label*="Fullscreen"]',
             'button[title*="Full screen"]',
             'button[title*="Fullscreen"]',
             '[data-testid*="fullscreen"]'),
            role_name=r'full\s*screen',
        )
        if clicked:
            self.page.wait_for_timeout(700)
            if self._fullscreen_verified(player):
                return True
        # Some HTML5 players expose only the standard keyboard shortcut after
        # the player receives focus. This remains a real browser input event.
        try:
            player.click(timeout=2000)
            player.press('f', timeout=2000)
            self.page.wait_for_timeout(700)
        except Exception:
            pass
        return self._fullscreen_verified(player)

    def _exit_fullscreen(self, frame, player):
        """Exit provider fullscreen with its toggle, then a normal Escape key."""
        if not self._fullscreen_verified(player):
            return True
        try:
            player.hover(timeout=1500)
        except Exception:
            pass
        self.page.wait_for_timeout(200)
        clicked = self._click_visible(
            frame,
            ('.ytp-fullscreen-button', 'button[aria-label*="Exit full screen"]',
             'button[aria-label*="Exit fullscreen"]',
             'button[title*="Exit full screen"]',
             'button[title*="Exit fullscreen"]'),
            role_name=r'exit\s+full\s*screen',
            timeout=2500,
        )
        if clicked:
            self.page.wait_for_timeout(500)
            if not self._fullscreen_verified(player):
                return True
        try:
            self.page.keyboard.press('Escape')
            self.page.wait_for_timeout(500)
        except Exception:
            pass
        return not self._fullscreen_verified(player)

    def _skip_visible_ad(self):
        """Click only a provider-exposed Skip ad control; never bypass an ad."""
        selectors = ('.ytp-ad-skip-button-modern', '.ytp-ad-skip-button',
                     'button[aria-label="Skip ad"]',
                     'button[aria-label*="Skip ad"]',
                     'button[title*="Skip ad"]')
        for frame in self.page.frames:
            if self._click_visible(frame, selectors, role_name=r'skip\s+ad'):
                self.page.wait_for_timeout(700)
                # A successful skip removes the control. If it lingers while
                # the player transitions, give the page a short bounded wait.
                deadline = time.monotonic() + 2.0
                while time.monotonic() < deadline:
                    visible = False
                    for selector in selectors:
                        try:
                            loc = frame.locator(selector)
                            visible = any(loc.nth(i).is_visible() for i in range(min(loc.count(), 4)))
                        except Exception:
                            continue
                        if visible:
                            break
                    if not visible:
                        return {'ok': True, 'reply': 'Skipped the visible ad.', 'media_state': 'playing'}
                    self.page.wait_for_timeout(250)
                return {'ok': False, 'reply': 'The Skip ad control was clicked, but the ad transition was not verified.'}
        return {'ok': False, 'reply': 'No visible Skip ad control was found. The current ad may be non-skippable, or no ad is playing.'}

    def _youtube_first_result(self):
        """Return the first real watch link across desktop/mobile YouTube DOMs."""
        try:
            self.page.wait_for_selector('a#video-title, a[href*="/watch?v="]', timeout=7000)
        except Exception:
            pass
        selectors = ('a#video-title', 'ytd-video-renderer a[href*="/watch?v="]',
                     'a[href*="/watch?v="]')
        for selector in selectors:
            try:
                links = self.page.locator(selector)
                for index in range(min(links.count(), 8)):
                    link = links.nth(index)
                    href = str(link.get_attribute('href') or '')
                    title = (link.inner_text(timeout=1500) or '').strip()
                    if '/watch' in href and title:
                        return link, title
            except Exception:
                continue
        return None, ''

    def _play_youtube_first(self, selection='first'):
        link, selected = self._youtube_first_result()
        if link is None:
            return {'ok':False,'reply':'YouTube search loaded, but no playable video result was exposed. No subscription check was involved and no video was started.'}
        try:
            link.click(timeout=5000)
            self.page.wait_for_timeout(900)
            video=self.page.locator('video').first
            if not video.count():
                return {'ok':False,'reply':'YouTube opened the selected result, but no video player appeared. Playback was not verified.'}
            video.evaluate('v=>v.play().catch(()=>null)')
            before=video.evaluate('v=>({paused:v.paused,time:v.currentTime,ready:v.readyState})')
            self.page.wait_for_timeout(1100)
            after=video.evaluate('v=>({paused:v.paused,time:v.currentTime,ready:v.readyState})')
            if not after['paused'] and after['ready'] >= 2 and after['time'] > before['time'] + .1:
                self.playing_until=time.monotonic()+45
                label = 'latest' if selection == 'latest' else 'first'
                return {'ok':True,'reply':f"Started the {label} YouTube result: {selected[:180]}",'media_state':'playing'}
            return {'ok':False,'reply':'YouTube opened the selected result, but playback did not advance. The browser may need one visible click; no subscription was assumed.'}
        except Exception as exc:
            return {'ok':False,'reply':f'YouTube result selection failed ({type(exc).__name__}); no subscription check was involved and playback was not verified.'}

    def _browser_command(self,command):
        action=command.get('action');kind=command['kind']
        if kind=='control' and (not self.page or self.page.is_closed()):
            self.playing_until=0
            return {'ok':False,'reply':'No controlled media player is open. Ask me to find a movie or play a video first.'}
        self._ensure_browser()
        if kind=='youtube_follow':
            host=(urlsplit(self.page.url).hostname or '').removeprefix('www.')
            if host != 'youtube.com' or '/results' not in (urlsplit(self.page.url).path or ''):
                return {'ok':False,'reply':'The previous YouTube results page is no longer open. Ask me to find the video again; no unrelated page was changed.'}
            return self._play_youtube_first(command.get('selection','first'))
        if kind!='control':
            url=command['url']
            # YouTube searches are built locally; all other navigation must be official.
            if not safe_url(url):return {'ok':False,'reply':'The media address is not a supported official provider.'}
            try:self.page.goto(url,wait_until='domcontentloaded',timeout=12000)
            except Exception as exc:
                return {'ok':False,'reply':f'The official page did not finish loading ({type(exc).__name__}). The browser remains available for another request; playback is unconfirmed.'}
            if not safe_url(self.page.url):return {'ok':False,'reply':'The provider redirected outside supported official sites. Owner review is required; no playback action was sent.'}
            if kind=='youtube':
                if not command.get('play'):return {'ok':True,'reply':'Opened YouTube search results in the media browser. No video is claimed playing.'}
                return self._play_youtube_first(command.get('selection','first'))
            if kind=='service_search':
                return {'ok':True,'reply':f"Opened {command.get('service','the service')} search results for {command.get('title','the requested title')}. Playback was not claimed; the service may require sign-in or owner selection.",'media_state':'opened'}
            if kind=='web_search':
                return {'ok':True,'reply':f"Opened web search results for {command.get('title','the requested topic')}.",'media_state':'opened'}
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
        if action=='skip_ad':
            return self._skip_visible_ad()
        players=self._observe()
        if not players:return {'ok':False,'reply':'No supported video or audio player was found in the controlled page. No other application was changed.'}
        frame,index,row=next((v for v in players if not v[2]['paused']),players[0]);player=frame.locator('video, audio').nth(index)
        if action=='fullscreen':
            verified=self._enter_fullscreen(frame,player)
            return {'ok':verified,'reply':'Fullscreen verified.' if verified else 'The player did not expose a working fullscreen control. No other window was changed.'}
        if action=='exit_fullscreen':
            verified=self._exit_fullscreen(frame,player)
            return {'ok':verified,'reply':'Fullscreen exited and verified.' if verified else 'The player remained fullscreen; its exit control did not verify.'}
        scripts={'pause':'v=>v.pause()','stop':'v=>{v.pause();v.currentTime=0}',
                 'resume':'v=>v.play()','mute':'v=>v.muted=true','unmute':'v=>v.muted=false',
                 'volume':'(v,n)=>v.volume=n'}
        if action not in scripts:return {'ok':False,'reply':'Unsupported media control.'}
        try:
            if action in {'pause', 'resume'}:
                try: player.hover(timeout=1500)
                except Exception: pass
                button_selectors = {
                    'pause': ('.ytp-pause-button', 'button[aria-label*="Pause"]', 'button[title*="Pause"]'),
                    'resume': ('.ytp-play-button', 'button[aria-label*="Play"]', 'button[title*="Play"]'),
                }[action]
                clicked = self._click_visible(frame, button_selectors, role_name=action, timeout=2500)
                if not clicked:
                    player.evaluate(scripts[action],command.get('volume'))
            else:
                player.evaluate(scripts[action],command.get('volume'))
            self.page.wait_for_timeout(350)
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

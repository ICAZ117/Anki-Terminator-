# Copyright (C) Shigeyuki <http://patreon.com/Shigeyuki>
# License: GNU AGPL version 3 or later <http://www.gnu.org/licenses/agpl.html>

import os
import time
import typing

try:
    from PyQt6.QtWebEngineCore import (
        QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo,
        QWebEnginePage, QWebEngineProfile)
except Exception as e:
    print(f"Error: {e}")
    from aqt.qt import (
        QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo,
        QWebEnginePage, QWebEngineProfile,
        )

from .path_manager import ADDON_NAME

if typing.TYPE_CHECKING:
    from adblock import BlockerResult

# https://easylist.to/index.html
# https://help.adblockplus.org/adblock-plus-help-center/how-to-write-filters

# https://github.com/bupd/dotfiles/blob/main/guide-to-qutebrowser-adblock.md

# https://github.com/qutebrowser/qutebrowser
# https://github.com/search?q=repo%3Aqutebrowser%2Fqutebrowser%20adblock&type=code

# https://doc.qt.io/qt-6/qwebengineurlrequestinfo.html

# https://github.com/brave/brave-browser

easylist_path = os.path.join(os.path.dirname(__file__), "easylist.txt")


#MARK:extraBlock
extra_block_domain_list = [
    "https://www.googletagmanager.com/",
    "https://static.cloudflareinsights.com/",
    "https://maps.forvo.com/osm_tiles/",
]

#MARK:extraAllow
extra_allow_domain_list = [
]

#MARK:disable adblock
disabled_on_sites = [
    # "youtube.com",

]


#MARK:load_easylist
# old ver
def load_ad_domains_from_easylist(path=easylist_path):
    block_domains = set()
    allow_domains = set()

    with open(path, encoding="utf8") as f:
        for line in f:
            line = line.strip()

            # ｺﾒﾝﾄ
            if not line or line.startswith("!"):
                continue # ｺﾒﾝﾄを無視

            # white list
            if line.startswith("@@||"):
                raw_rule = line[4:].split("$")[0]
                domain = raw_rule.split("^")[0]
                if domain:
                    allow_domains.add(domain)

            # block list
            elif line.startswith("||"):
                raw_rule = line[2:].split("$")[0]
                domain = raw_rule.split("^")[0]
                if domain:
                    block_domains.add(domain)


    # extra
    for domain in extra_block_domain_list:
        block_domains.add(domain)
    for domain in extra_allow_domain_list:
        allow_domains.add(domain)


    return list(block_domains), list(allow_domains)


QT_RESOURCE_TYPES = {
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeMainFrame: "main_frame",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeSubFrame: "sub_frame",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeStylesheet: "stylesheet",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeScript: "script",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeImage: "image",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeFontResource: "font",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeSubResource: "other",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeObject: "object",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeMedia: "media",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeWorker: "other",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeSharedWorker: "other",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypePrefetch: "other",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeFavicon: "image",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeXhr: "xmlhttprequest",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypePing: "ping",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeServiceWorker: "other",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeCspReport: "csp_report",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypePluginResource: "other",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeNavigationPreloadMainFrame: "main_frame",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeNavigationPreloadSubFrame: "sub_frame",
    QWebEngineUrlRequestInfo.ResourceType.ResourceTypeWebSocket: "websocket",
}



#MARK:AdBlocker
class AdBlocker(QWebEngineUrlRequestInterceptor):
    block_domains, allow_domains = load_ad_domains_from_easylist()

    def __init__(self, parent=None):
        super().__init__(parent)

        try:
            print(f"[{ADDON_NAME}] make adblock...")
            start = time.time()

            from .wheel_downloader import make_adblock_engine
            self.adblock_engine = make_adblock_engine()

            print(f"[{ADDON_NAME}] make adblock {time.time() - start:.2f} sec")
        except Exception as e:
            print(f"[{ADDON_NAME}] Erorr: {e} ")



    def interceptRequest(self, info:"QWebEngineUrlRequestInfo"):
        try:
            url = info.requestUrl().toString()
            first_party_url = info.firstPartyUrl().toString()

            #  disable website list
            if any(site in first_party_url for site in disabled_on_sites):
                return

            # white list
            if any(allowed in url for allowed in self.allow_domains):
                return

            if self.adblock_engine:
                resource_type = QT_RESOURCE_TYPES.get(info.resourceType(), "other")

                result = self.adblock_engine.check_network_urls(
                    url=url,
                    source_url=first_party_url,
                    request_type=resource_type
                ) # type:BlockerResult

                if result.matched:
                    # print(f"[{ADDON_NAME}] engine Blocked ad: {url}")
                    info.block(True)

            else:
                # block list
                if any(domain in url for domain in self.block_domains):
                    # print(f"[{ADDON_NAME}] Blocked ad: {url}")
                    info.block(True)

                # else:
                #     print(f"[{ADDON_NAME}] Allowed url: {url}")

        except Exception as e:
            print(f"[{ADDON_NAME}] Erorr: {e} ")


#MARK:loadTimeCheker
def load_time_checker(qt_web_page:QWebEnginePage):
    try:
        def log_resource_time(result):
            if result:
                print("")
                print(f"[{ADDON_NAME}] ===== load time checker (start) =====")

                sorted_entries = sorted(
                    result, key=lambda entry: entry.get("duration", 0), reverse=True)

                for entry in sorted_entries[:50]:
                    name = entry.get("name", "None")
                    duration = entry.get("duration", 0)
                    seconds = duration / 1000
                    print(f"[{ADDON_NAME}] {seconds}sec {name}")

                print(f"[{ADDON_NAME}] ===== load time checker (end) =====")
                print("")

        qt_web_page.runJavaScript("""
            (function() {
                var entries = performance.getEntriesByType('resource');
                return entries.map(function(entry) {
                    return {
                        name: entry.name,
                        duration: entry.duration
                    };
                });
            })();
        """, log_resource_time)

    except Exception as e:
        print(f"[{ADDON_NAME}] Erorr: {e} ")


#MARK:set_add_blocekr
def set_add_blocekr(qt_web_profle:QWebEngineProfile):

    try:
        adblocker = AdBlocker(qt_web_profle)
        qt_web_profle.setUrlRequestInterceptor(adblocker)

    except Exception as e:
        print(f"[{ADDON_NAME}] Erorr: {e} ")


#MARK:load time checker
def adblock_load_time_checker(qt_web_page:QWebEnginePage):
    return
    try:
        # ﾍﾟｰｼﾞの読み込みにかかる時間を調べる

        from .debug_mode import check_debug_mode

        # debug only
        if check_debug_mode():
            def handle_load_finished(success):
                print(">>> handle_load_finished")
                if success:
                    load_time_checker(qt_web_page)

            qt_web_page.loadFinished.connect(handle_load_finished)

    except Exception as e:
        print(f"[{ADDON_NAME}] Erorr: {e} ")



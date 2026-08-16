# Copyright (C) Shigeyuki <http://patreon.com/Shigeyuki>
# License: GNU AGPL version 3 or later <http://www.gnu.org/licenses/agpl.html>

import os

from aqt import mw, gui_hooks
from aqt.utils import tooltip
from aqt.toolbar import Toolbar

from .dock_web_view import Web_view
from .path_manager import (
                            ADDON_NAME,
                            CHAT_GPT, GOOGLE_BARD, BING_CHAT, CUSTOM_AI,
                            CHAT_GPT_LOGO, GOOGLE_BARD_LOGO, BING_CHAT_LOGO, CUSTOM_LOGO,
                            LABEL_TEXT, LABEL_ID,LABEL_PYCMD, LABEL_INDEX,
                            DEEP_SEEK, DEEP_SEEK_URL, DEEP_SEEK_LOGO,
                            PERPLEXITY, PERPLEXITY_URL, PERPLEXITY_LOGO,
                            CLAUDE, CLAUDE_URL, CLAUDE_LOGO,
                            IMAGE_FX, IMAGE_FX_URL, IMAGE_FX_LOGO,
                            GROK_AI, GROK_AI_URL, GROK_LOGO,
                            DUCK_AI, DUCK_AI_URL, DUCK_AI_LOGO,
                            GOOGLE_AI_MODE, GOOGLE_AI_MODE_URL, GOOGLE_AI_MODE_LOGO,
                            )

from .shige_patch_onigiri import check_onigiri_enable


#MARK:get logo
def get_logo_and_html_label(now_AI_type):

    if now_AI_type == CHAT_GPT:
        logo_png = CHAT_GPT_LOGO
    elif now_AI_type == GOOGLE_BARD:
        logo_png = GOOGLE_BARD_LOGO
    elif now_AI_type == BING_CHAT:
        logo_png = BING_CHAT_LOGO
    elif now_AI_type == DEEP_SEEK:
        logo_png = DEEP_SEEK_LOGO
    elif now_AI_type == PERPLEXITY:
        logo_png = PERPLEXITY_LOGO
    elif now_AI_type == CLAUDE:
        logo_png = CLAUDE_LOGO
    elif now_AI_type == IMAGE_FX:
        logo_png = IMAGE_FX_LOGO
    elif now_AI_type == GROK_AI:
        logo_png = GROK_LOGO
    elif now_AI_type == DUCK_AI:
        logo_png = DUCK_AI_LOGO
    elif now_AI_type == GOOGLE_AI_MODE:
        logo_png = GOOGLE_AI_MODE_LOGO

    else:
        logo_png = LABEL_TEXT

    if logo_png == LABEL_TEXT:
        html_label = LABEL_TEXT
    else:
        mw.addonManager.setWebExports(__name__, r".*")
        addon_package = mw.addonManager.addonFromModule(__name__)
        mediafolder = f"/_addons/{addon_package}/{logo_png}"
        # ﾀﾞﾌﾞﾙｸｫｰﾃｰｼｮﾝにするとﾊﾞｸﾞる, ｼﾝｸﾞﾙならｷﾞﾘいける
        # html_label = f"<img src='{mediafolder}' alt='{LABEL_TEXT}' style='height: 1em;'>"
        html_label = f"<img src='{mediafolder}' alt='{LABEL_TEXT}' style='height: 1em; min-width: 1em;'>"

    return logo_png, html_label


#MARK:open url
def ChatGPT_URL_open():
    config = mw.addonManager.getConfig(__name__)
    now_AI_type = config["now_AI_type"]

    is_need_update_config = False

    try:
        chappie_old_url = "https://chat.openai.com/chat/"
        chappie_new_url = "https://chatgpt.com/"
        if config["ChatGPT_URL"].get(CHAT_GPT) == chappie_old_url:
            config["ChatGPT_URL"][CHAT_GPT] = chappie_new_url
            is_need_update_config = True
    except Exception as e:
        print(f"[{ADDON_NAME}] Error: {e} ")

    if (DEEP_SEEK not in config["ChatGPT_URL"]
        or PERPLEXITY not in config["ChatGPT_URL"]
        or CLAUDE not in config["ChatGPT_URL"]
        or IMAGE_FX not in config["ChatGPT_URL"]
        ):
        config["ChatGPT_URL"][DEEP_SEEK] = DEEP_SEEK_URL
        config["ChatGPT_URL"][PERPLEXITY] = PERPLEXITY_URL
        config["ChatGPT_URL"][CLAUDE] = CLAUDE_URL
        config["ChatGPT_URL"][IMAGE_FX] = IMAGE_FX_URL
        is_need_update_config = True

    if (GROK_AI not in config["ChatGPT_URL"]
        ):
        config["ChatGPT_URL"][GROK_AI] = GROK_AI_URL
        is_need_update_config = True

    if (DUCK_AI not in config["ChatGPT_URL"]
        ):
        config["ChatGPT_URL"][DUCK_AI] = DUCK_AI_URL
        is_need_update_config = True

    if (GOOGLE_AI_MODE not in config["ChatGPT_URL"]
        ):
        config["ChatGPT_URL"][GOOGLE_AI_MODE] = GOOGLE_AI_MODE_URL
        is_need_update_config = True





    if is_need_update_config:
        mw.addonManager.writeConfig(__name__, config)


    if now_AI_type in config["ChatGPT_URL"]:
        ChatGPT_URL = config["ChatGPT_URL"][now_AI_type]
    elif not config["Custom_AI_URL"].isspace():
        ChatGPT_URL = config["Custom_AI_URL"]
    else: # ﾃﾞﾌｫﾙﾄ
        ChatGPT_URL = CHAT_GPT

    Web_view("ChatGPT", ChatGPT_URL)


#MARK:add toptoolbar
def add_gpt_to_the_top_toolbar(links: list, toolbar: Toolbar) -> None:
    try:
        config = mw.addonManager.getConfig(__name__)
        now_AI_type = config["now_AI_type"]
        logo_png, html_label = get_logo_and_html_label(now_AI_type)

        shortcut_key = config["AI_shortcut_key"]

        def create_link(cmd,label,func,tip,id,):#aria-labelがHTMLになるとﾊﾞｸﾞる
            toolbar.link_handlers[cmd] = func
            title_attr = f'title="{tip}"' if tip else ""
            id_attr = f'id="{id}"' if id else ""
            return (
                f"""<a class=hitem tabindex="-1" aria-label="{LABEL_TEXT}" """
                f"""{title_attr} {id_attr} href=# onclick="return pycmd('{cmd}')">"""
                f"""{label}</a>"""
            )

        link = create_link(
            cmd = LABEL_PYCMD,
            label = html_label,
            func = ChatGPT_URL_open,
            tip = f"Open Sidebar ( {shortcut_key} )" ,
            id = LABEL_ID ,
        )
        links.insert(LABEL_INDEX, link)
    except:
        pass


#MARK:setup toolbar
def setup_update_top_toolbar():
    if mw is not None:
        config = mw.addonManager.getConfig(__name__)
        if config["add_gpt_to_the_top_toolbar"]:
            gui_hooks.top_toolbar_did_init_links.remove(add_gpt_to_the_top_toolbar)
            gui_hooks.top_toolbar_did_init_links.append(add_gpt_to_the_top_toolbar)

# Inspired by this add-on👍👍👍
# AJT Flexible Grading / Tatsumoto
# https://ankiweb.net/shared/info/1715096333
# https://github.com/Ajatt-Tools/FlexibleGrading


#MARK:change ai
def change_AI_icon_on_top_tool_bar():
    config = mw.addonManager.getConfig(__name__)
    now_AI_type = config["now_AI_type"]
    logo_png, new_label = get_logo_and_html_label(now_AI_type)

    # js_code = f"""
    # {{
    #     const elem = document.getElementById("{LABEL_ID}");
    #     elem.innerHTML = "{new_label}";
    # }};
    # """

    js_code = f"""
    {{
        const elem = document.getElementById("{LABEL_ID}");
        if (!elem) {{
            console.log("[{ADDON_NAME}] element not found, LABEL_ID={LABEL_ID}");
        }} else {{
            console.log("[{ADDON_NAME}] element found, LABEL_ID={LABEL_ID}");
            elem.innerHTML = "{new_label}";
        }}
    }};"""

    if mw.state in ["review", "overview"] and check_onigiri_enable():
        mw.web.eval(js_code)

    else:
        mw.toolbar.web.eval(js_code)

    show_tooltip_ai(logo_png, now_AI_type)



#MARK:tooltip
def show_tooltip_ai(logo_png, now_AI_type):
    try:
        addon_path = os.path.dirname(__file__)
        tooltip(
            f"<img src='{os.path.join(addon_path, logo_png)}' height='24'>"
            f"<span style='font-size:19px;'> {now_AI_type} </span>")
    except Exception as e:
        print(f"[AnkiTerminatorV2] Error: {e}")


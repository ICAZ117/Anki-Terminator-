# Copyright (C) Shigeyuki <http://patreon.com/Shigeyuki>
# License: GNU AGPL version 3 or later <http://www.gnu.org/licenses/agpl.html>

import os

from aqt import mw, gui_hooks

from .path_manager import ADDON_NAME, LABEL_ID, LABEL_TEXT

import typing
if typing.TYPE_CHECKING:
    from aqt.addons import AddonMeta


# my addon
MY_ADDON_BUTTON_CLASS = "anki-terminator-shige-top-button"
MY_ADDON_BUTTON_ID = LABEL_ID # "anki-terminator-shige-top-button-id"
MY_ADDON_BUTTON_PYCMD = "anki-terminator-shige-pycmd"



# onigiri
# https://github.com/thepeacemonk/Onigiri/issues/8
ADDON_ID_ONIGIRI = 1011095603
ONIGIRI_HEADER = "onigiri-reviewer-header-buttons"
ONIGIRI_BUTTON = "onigiri-reviewer-button"
_addon_onigiri_meta = None #type:"AddonMeta"
_is_onigiri_exists = False
_is_first_run = True

#MARK:check
def check_onigiri_exists():
    try:
        global _is_onigiri_exists, _is_first_run
        if _is_first_run:
            _is_first_run = False

            path = mw.addonManager.addonsFolder(str(ADDON_ID_ONIGIRI))
            if os.path.exists(os.path.join(path, "__init__.py")):
                _is_onigiri_exists = True

        # print(f"[{ADDON_NAME}] _is_onigiri_exists: {_is_onigiri_exists}")

        return _is_onigiri_exists

    except Exception as e:
        print(f"[{ADDON_NAME}] Error: {e} ")
        return False

def check_onigiri_enable():
    try:
        global _addon_onigiri_meta
        if not _addon_onigiri_meta:
            from aqt import mw
            _addon_onigiri_meta = mw.addonManager.addon_meta(str(ADDON_ID_ONIGIRI))

        # print(f"[{ADDON_NAME}] _addon_onigiri_meta: {_addon_onigiri_meta.enabled}")

        return _addon_onigiri_meta.enabled

    except Exception as e:
        print(f"[{ADDON_NAME}] Error: {e} ")
        return False


#MARK:update
def add_onigiri_button(*args, **kwargs):
    try:
        if not check_onigiri_exists():
            return

        if not check_onigiri_enable():
            return

        if mw.state not in ["overview", "review"]:
            return

        config = mw.addonManager.getConfig(__name__)
        if not config.get("add_gpt_to_the_top_toolbar", True):
            return

        from .update_top_toolbar import get_logo_and_html_label
        now_AI_type = config.get("now_AI_type", "Chat_GPT")
        logo_png, html_label = get_logo_and_html_label(now_AI_type)

        RETRY_DURATION = 2000 # 2sec

        js = f"""
        (function() {{
            var startTime = Date.now();
            var maxDuration = {RETRY_DURATION};
            var retryCount = 0;
            var checkInterval = null;

            function tryAddButton() {{
                retryCount++;
                var headerElement = document.querySelector('.{ONIGIRI_HEADER}');

                if (headerElement) {{
                    console.log('[{ADDON_NAME}] headerElement found on try #' + retryCount);
                    if (!headerElement.querySelector('.{MY_ADDON_BUTTON_CLASS}')) {{
                        var newButton = document.createElement('a');
                        newButton.href = '#';
                        newButton.className = '{ONIGIRI_BUTTON} {MY_ADDON_BUTTON_CLASS}';
                        newButton.id = '{MY_ADDON_BUTTON_ID}';
                        newButton.innerHTML = `{html_label}`;
                        newButton.onclick = function() {{ pycmd('{MY_ADDON_BUTTON_PYCMD}'); return false; }};
                        headerElement.appendChild(newButton);
                        console.log('[{ADDON_NAME}] newButton added on try #' + retryCount);
                    }} else {{
                        console.log('[{ADDON_NAME}] newButton already exists on try #' + retryCount);
                    }}
                    return true;
                }} else {{
                    console.log('[{ADDON_NAME}] headerElement not found on try #' + retryCount);
                    var elapsedTime = Date.now() - startTime;
                    if (elapsedTime >= maxDuration) {{
                        console.log('[{ADDON_NAME}] Max retry time (' + (maxDuration / 1000) + 's) reached after ' + retryCount + ' tries');
                        return false;
                    }}
                    return null;
                }}
            }}

            setTimeout(function() {{
                var result = tryAddButton();
                if (result === null) {{
                    console.log('[{ADDON_NAME}] Starting 500ms retry...');
                    checkInterval = setInterval(function() {{
                        var result = tryAddButton();
                        if (result !== null) {{
                            clearInterval(checkInterval);
                        }}
                    }}, 500);
                }}
            }}, 50);
        }})();
        """
        mw.web.eval(js)

    except Exception as e:
        print(f"[{ADDON_NAME}] Error: {e}")


#MARK:pycmd handled
def on_webview_did_receive_js_message(handled, message, context, *args, **kwargs):
    try:
        if message == MY_ADDON_BUTTON_PYCMD:
            from .update_top_toolbar import ChatGPT_URL_open
            ChatGPT_URL_open()
            return (True, None)

        else:
            return handled

    except Exception as e:
        print(f"[{ADDON_NAME}] Error: {e} ")
        return handled


#MARK:set hools
def set_patch_hooks():
    gui_hooks.overview_did_refresh.append(add_onigiri_button)
    gui_hooks.reviewer_did_show_question.append(add_onigiri_button)
    gui_hooks.reviewer_did_show_answer.append(add_onigiri_button)
    gui_hooks.webview_did_receive_js_message.append(on_webview_did_receive_js_message)

import os
import sys
import warnings
import atexit
import inspect

import pygame
from cefpython3 import cefpython as cef

from cefpygame import (
    CefRenderHandler,
    update_scale,
    update_rotation,
    toggle_color,
    draw,
    CefClientHandler,
    CEFSettings,
)

CEF_MOD_DIR = cef.GetModuleDirectory()

def main():
    sys.excepthook = cef.ExceptHook
    os.environ["SDL_VIDEO_CENTERED"] = "1"

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    window = pygame.display.get_wm_info()["window"]

    pygame.display.set_caption("Pygame + CEF")

    atexit.register(cef.Shutdown)

    cef_settings = CEFSettings.app_settings
    browser_settings = CEFSettings.browser_settings
    command_line_switches = CEFSettings.command_line_switches

    cef_settings["locales_dir_path"] = os.path.join(CEF_MOD_DIR, "locales")
    cef_settings["resources_dir_path"] = CEF_MOD_DIR
    cef_settings["browser_subprocess_path"] = os.path.join(CEF_MOD_DIR, "subprocess")

    cef.Initialize(settings=cef_settings, switches=command_line_switches)
    # cef.DPIAware.EnableHighDpiSupport()

    html_path = os.path.abspath("ui/example.html").replace("\\", "/")
    url = f"file:///{html_path}"

    window_info = cef.WindowInfo()
    window_info.SetAsOffscreen(window)
    window_info.SetTransparentPainting(True)

    browser = cef.CreateBrowserSync(
        windowInfo=window_info, browserSettings=browser_settings, url=url
    )

    surface = pygame.Surface((SURFACE_WIDTH, SURFACE_HEIGHT))
    surface.fill((255, 255, 255))
    renderer = CefRenderHandler(surface)

    browser.SetClientHandler(renderer)
    browser.SendFocusEvent(True)
    browser.WasResized()

    client_handler = CefClientHandler()
    browser.SetClientHandler(client_handler)

    set_js_bindings(browser)

    clock = pygame.time.Clock()
    running = True
    while running:
        cef.MessageLoopWork()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEMOTION:
                pos_x, pos_y = event.pos
                modifiers = get_cef_modifiers()
                browser.SendMouseMoveEvent(pos_x, pos_y, mouseLeave=False, modifiers=modifiers)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos_x, pos_y = event.pos
                modifiers = get_cef_modifiers()

                if event.button == 4:
                    browser.SendMouseWheelEvent(
                        pos_x, pos_y, deltaX=0, deltaY=-SCROLL_DELTA, modifiers=modifiers
                    )

                elif event.button == 5:
                    browser.SendMouseWheelEvent(
                        pos_x, pos_y, deltaX=0, deltaY=SCROLL_DELTA, modifiers=modifiers
                    )

                else:
                    button = get_cef_mouse_button(event.button, event.pos)
                    if button is not None:
                        browser.SendMouseClickEvent(
                            pos_x,
                            pos_y,
                            button,
                            mouseUp=False,
                            clickCount=1,
                            modifiers=modifiers,
                        )

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button in (4, 5):
                    # Wheel scroll, ignore mouse up event
                    continue

                pos_x, pos_y = event.pos
                modifiers = get_cef_modifiers()
                button = get_cef_mouse_button(event.button, event.pos)
                if button is not None:
                    browser.SendMouseClickEvent(
                        pos_x, pos_y, button, mouseUp=True, clickCount=1, modifiers=modifiers
                    )

        draw(surface, (255, 0, 0), 100, 100, [(100, 100), (150, 150), (100, 200)])
        screen.blit(surface, (0, 0))

        pygame.display.flip()
        clock.tick(60)

    cef.Shutdown()
    pygame.quit()


def set_js_bindings(browser):
    bindings = cef.JavascriptBindings()
    bindings.SetFunction("py_func", lambda msg: print(f"JS sent: {msg}"))
    bindings.SetFunction("toggle_color", toggle_color)
    bindings.SetProperty("sources", {"toggle_color": inspect.getsource(toggle_color)})
    bindings.SetFunction("update_rotation", update_rotation)
    bindings.SetProperty(
        "sources", {"update_rotation": inspect.getsource(update_rotation)}
    )
    bindings.SetFunction("update_scale", update_scale)
    bindings.SetProperty("sources", {"update_scale": inspect.getsource(update_scale)})
    browser.SetJavascriptBindings(bindings)


def get_cef_mouse_button(pygame_button, event_pos):
    pos_x, pos_y = event_pos
    if pos_x >= SURFACE_WIDTH or pos_y >= SURFACE_HEIGHT or pos_x < 0 or pos_y < 0:
        return None

    if pygame_button == 1:
        return cef.MOUSEBUTTON_LEFT
    elif pygame_button == 2:
        return cef.MOUSEBUTTON_MIDDLE
    elif pygame_button == 3:
        return cef.MOUSEBUTTON_RIGHT

    # These aren't defined by CEF Python as click events
    # We use the SendMouseWheelEvent() function instead
    # elif pygame_button == 4:
    #     return cef.MOUSEBUTTON_WHEELUP
    # elif pygame_button == 5:
    #     return cef.MOUSEBUTTON_WHEELDOWN

    else:
        warnings.warn("Button not recognized")
        return None


def get_cef_modifiers():
    mods = pygame.key.get_mods()
    flags = 0

    if mods & pygame.KMOD_SHIFT:
        flags |= cef.EVENTFLAG_SHIFT_DOWN
    if mods & pygame.KMOD_CTRL:
        flags |= cef.EVENTFLAG_CONTROL_DOWN
    if mods & pygame.KMOD_ALT:
        flags |= cef.EVENTFLAG_ALT_DOWN
    if mods & pygame.KMOD_CAPS:
        flags |= cef.EVENTFLAG_CAPS_LOCK_ON

    # Mac-specific modifiers (not functional unless on Mac)
    if sys.platform == "darwin":
        if mods & pygame.KMOD_META:  # ⌘ Command on Mac
            flags |= cef.EVENTFLAG_COMMAND_DOWN

        # Other modifier not directly supported in Pygame
        # ...

    mouse = pygame.mouse.get_pressed()
    if mouse[0]:
        flags |= cef.EVENTFLAG_LEFT_MOUSE_BUTTON
    if mouse[1]:
        flags |= cef.EVENTFLAG_MIDDLE_MOUSE_BUTTON
    if mouse[2]:
        flags |= cef.EVENTFLAG_RIGHT_MOUSE_BUTTON

    return flags


if __name__ == "__main__":
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600

    SURFACE_WIDTH = WINDOW_WIDTH
    SURFACE_HEIGHT = WINDOW_HEIGHT

    SCROLL_DELTA = 120  # constant across platforms

    main()

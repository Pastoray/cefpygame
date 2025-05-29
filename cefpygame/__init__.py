import math
import pygame

tri_rotation = 0
tri_colored = False
tri_speed = 0.0
tri_scale = 1.0

last_cef_frame = None


class CEFSettings:
    app_settings = {
        "remote_debugging_port": 0,
        "context_menu": {
            "enabled": False,
        },
        "background_color": 0xFFFFFFFF,
        "windowless_rendering_enabled": True,
    }

    browser_settings = {
        "file_access_from_file_urls_allowed": True,
        "universal_access_from_file_urls_allowed": True,
        "windowless_frame_rate": 60,
        "background_color": 0xFFFFFFFF,
    }

    command_line_switches = {}


def toggle_color(value):
    global tri_colored
    tri_colored = value


def update_rotation(value):
    global tri_speed
    tri_speed = float(value)


def update_scale(scale_value):
    global tri_scale
    tri_scale = float(scale_value)


def draw(
    surface: pygame.Surface,
    color: tuple,
    center_x: int,
    center_y: int,
    base_points: list,
):
    """
    Draws the CEF content and a rotating/scaled triangle onto the given surface.

    Args:
        surface (pygame.Surface): The surface to draw on.
        color (tuple): RGB color of the triangle.
        center_x (int): X-coordinate of the triangle's center.
        center_y (int): Y-coordinate of the triangle's center.
        base_points (list): A list of (x, y) tuples representing the triangle's
                            points before any transformations, relative to its center.
    """
    global tri_rotation, tri_scale, tri_colored, tri_speed
    surface.fill((255, 255, 255))

    if last_cef_frame:
        surface.blit(last_cef_frame, (0, 0))

    tri_rotation += tri_speed

    transformed_points = []
    for x, y in base_points:
        scaled_x = x * tri_scale
        scaled_y = y * tri_scale

        angle_rad = math.radians(tri_rotation)
        rotated_x = scaled_x * math.cos(angle_rad) - scaled_y * math.sin(angle_rad)
        rotated_y = scaled_x * math.sin(angle_rad) + scaled_y * math.cos(angle_rad)

        # Translate to the center of the screen
        transformed_points.append((rotated_x + center_x, rotated_y + center_y))

    if tri_colored:
        pygame.draw.polygon(surface, color, transformed_points)
    else:
        pygame.draw.polygon(
            surface, color, transformed_points, 2
        )  # Draw outline with thickness 2


class CefRenderHandler(object):
    def __init__(self, surface):
        self.surface = surface

    def GetViewRect(self, browser, rect_out, *_args, **_kwargs):
        rect_out.extend([0, 0, self.surface.get_width(), self.surface.get_height()])
        return True

    def OnPaint(self, element_type, paint_buffer, dirty_rects, **_kwargs):
        global last_cef_frame, tri_rotation, tri_speed
        if not dirty_rects:
            return

        # CEF provides BGRA, Pygame wants RGBA
        raw = bytearray(paint_buffer.GetString(mode="bgra"))
        width, height = self.surface.get_size()

        last_cef_frame = pygame.image.frombuffer(raw, (width, height), "RGBA")

        for rect in dirty_rects:
            x, y, w, h = rect
            self.surface.fill((0, 0, 0, 0), (x, y, w, h))

        self.surface.fill((255, 255, 255))


class CefClientHandler(object):
    def OnConsoleMessage(self, browser, message, source, line, *_args, **_kwargs):
        print(f"[JS Console] {message} (source: {source}, line: {line})")

    def OnPopupShow(self, **kwargs):
        pass

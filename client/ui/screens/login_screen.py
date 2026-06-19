import pygame
from pathlib import Path

BG_PATH = Path(__file__).parent.parent / "assets" / "sprites" / "bg.png"
FONT_PATH = Path(__file__).parent.parent / "assets" / "fonts" / "pixelboy.ttf"
LOGO_PATH = Path(__file__).parent.parent / "assets" / "sprites" / "logo.png"
BUTTON_PATH = Path(__file__).parent.parent / "assets" / "sprites" / "button.png"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (255, 215, 0)
RED = (220, 60, 60)
GREEN = (60, 210, 80)
BLUE = (50, 130, 200)
DIM = (160, 160, 170)
BG_COLOR = (30, 30, 50)


class LoginScreen:
    SCREEN_W = 800
    SCREEN_H = 600
    CENTER_X = SCREEN_W // 2

    LOGO_WIDTH = 200
    LOGO_HEIGHT = 150
    LOGO_CENTER_Y = 60

    FIELD_W = 240
    FIELD_H = 25
    USERNAME_Y = 160
    PASSWORD_Y = 220
    FIELD_PADDING = 5

    BUTTON_W = 300
    BUTTON_H = 120
    LOGIN_Y = 300
    CREATE_Y = 370
    BUTTON_TEXT_OFFSET = 2

    STATUS_Y = 110

    CURSOR_BLINK_SPEED = 1000
    CURSOR_WIDTH = 2

    FIELD_X = CENTER_X - FIELD_W // 2
    BUTTON_X = CENTER_X - BUTTON_W // 2

    def __init__(self):
        self.username = ""
        self.password = ""
        self.status = "Enter username and password"
        self.focus_username = True
        self.focus_password = False

        self.username_rect = pygame.Rect(
            self.FIELD_X,
            self.USERNAME_Y,
            self.FIELD_W,
            self.FIELD_H
        )
        self.password_rect = pygame.Rect(
            self.FIELD_X,
            self.PASSWORD_Y,
            self.FIELD_W,
            self.FIELD_H
        )
        self.login_btn_rect = pygame.Rect(
            self.BUTTON_X,
            self.LOGIN_Y,
            self.BUTTON_W,
            self.BUTTON_H
        )
        self.create_btn_rect = pygame.Rect(
            self.BUTTON_X,
            self.CREATE_Y,
            self.BUTTON_W,
            self.BUTTON_H
        )

        if FONT_PATH.exists():
            self.font = pygame.font.Font(str(FONT_PATH), 24)
            self.small_font = pygame.font.Font(str(FONT_PATH), 18)
            self.tiny_font = pygame.font.Font(str(FONT_PATH), 14)
        else:
            self.font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 18)
            self.tiny_font = pygame.font.Font(None, 14)

        if BG_PATH.exists():
            self.bg = pygame.image.load(str(BG_PATH)).convert()
            self.bg = pygame.transform.scale(self.bg, (self.SCREEN_W, self.SCREEN_H))
        else:
            self.bg = None

        self.logo = None
        self.logo_rect = None
        if LOGO_PATH.exists():
            try:
                original = pygame.image.load(str(LOGO_PATH)).convert_alpha()
                scale_factor = min(
                    self.LOGO_WIDTH / original.get_width(),
                    self.LOGO_HEIGHT / original.get_height()
                )
                new_w = int(original.get_width() * scale_factor)
                new_h = int(original.get_height() * scale_factor)
                self.logo = pygame.transform.smoothscale(original, (new_w, new_h))
                self.logo_rect = self.logo.get_rect(center=(self.CENTER_X, self.LOGO_CENTER_Y))
            except Exception:
                self.logo = None

        self.button_texture = None
        if BUTTON_PATH.exists():
            try:
                self.button_texture = pygame.image.load(str(BUTTON_PATH)).convert_alpha()
            except Exception:
                self.button_texture = None

        self._cursor_blink_timer = 0

    def update(self, dt_ms: float):
        self._cursor_blink_timer = (self._cursor_blink_timer + dt_ms) % self.CURSOR_BLINK_SPEED

    def _draw_button(self, surface: pygame.Surface, rect: pygame.Rect, text: str):
        if self.button_texture is not None:
            scaled = pygame.transform.smoothscale(self.button_texture, (rect.w, rect.h))
            surface.blit(scaled, rect.topleft)
        else:
            pygame.draw.rect(surface, (70, 70, 90), rect, border_radius=4)
            pygame.draw.rect(surface, (0, 0, 0), rect, 2, border_radius=4)

        text_surf = self.font.render(text, True, WHITE)
        text_rect = text_surf.get_rect(center=rect.center)
        text_rect.centery -= self.BUTTON_TEXT_OFFSET
        surface.blit(text_surf, text_rect)

    def draw(self, surface: pygame.Surface):
        if self.bg:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill(BG_COLOR)

        if self.logo and self.logo_rect:
            surface.blit(self.logo, self.logo_rect)

        color = WHITE
        if "error" in self.status.lower() or "fail" in self.status.lower():
            color = RED
        elif "success" in self.status.lower() or "created" in self.status.lower():
            color = GREEN
        status_surf = self.small_font.render(self.status, True, color)
        status_rect = status_surf.get_rect(center=(self.CENTER_X, self.STATUS_Y))
        surface.blit(status_surf, status_rect)

        pygame.draw.rect(surface, WHITE, self.username_rect, 2)
        user_surf = self.font.render(self.username, True, WHITE)
        surface.blit(user_surf, (self.username_rect.x + self.FIELD_PADDING, self.username_rect.y + self.FIELD_PADDING))

        if self.focus_username and self._cursor_blink_timer < self.CURSOR_BLINK_SPEED // 2:
            cursor_x = self.username_rect.x + self.FIELD_PADDING + self.font.size(self.username)[0]
            cursor_y = self.username_rect.y + self.FIELD_PADDING
            cursor_h = self.FIELD_H - 2 * self.FIELD_PADDING
            pygame.draw.line(
                surface, WHITE,
                (cursor_x, cursor_y),
                (cursor_x, cursor_y + cursor_h),
                self.CURSOR_WIDTH
            )

        pygame.draw.rect(surface, WHITE, self.password_rect, 2)
        display_pass = "*" * len(self.password)
        pass_surf = self.font.render(display_pass, True, WHITE)
        surface.blit(pass_surf, (self.password_rect.x + self.FIELD_PADDING, self.password_rect.y + self.FIELD_PADDING))

        if self.focus_password and self._cursor_blink_timer < self.CURSOR_BLINK_SPEED // 2:
            cursor_x = self.password_rect.x + self.FIELD_PADDING + self.font.size(display_pass)[0]
            cursor_y = self.password_rect.y + self.FIELD_PADDING
            cursor_h = self.FIELD_H - 2 * self.FIELD_PADDING
            pygame.draw.line(
                surface, WHITE,
                (cursor_x, cursor_y),
                (cursor_x, cursor_y + cursor_h),
                self.CURSOR_WIDTH
            )

        self._draw_button(surface, self.login_btn_rect, "Login")
        self._draw_button(surface, self.create_btn_rect, "Create Account")

        label_user = self.tiny_font.render("Username", True, DIM)
        surface.blit(label_user, (self.username_rect.x, self.username_rect.y - 20))
        label_pass = self.tiny_font.render("Password", True, DIM)
        surface.blit(label_pass, (self.password_rect.x, self.password_rect.y - 20))

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if self.focus_username:
                if event.key == pygame.K_BACKSPACE:
                    self.username = self.username[:-1]
                elif event.key == pygame.K_RETURN:
                    return ("login", (self.username, self.password))
                elif event.key == pygame.K_TAB:
                    self.focus_username = False
                    self.focus_password = True
                else:
                    self.username += event.unicode

            elif self.focus_password:
                if event.key == pygame.K_BACKSPACE:
                    self.password = self.password[:-1]
                elif event.key == pygame.K_RETURN:
                    return ("login", (self.username, self.password))
                elif event.key == pygame.K_TAB:
                    self.focus_password = False
                    self.focus_username = True
                else:
                    self.password += event.unicode

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.username_rect.collidepoint(event.pos):
                self.focus_username = True
                self.focus_password = False
                return ("switch_focus", None)

            if self.password_rect.collidepoint(event.pos):
                self.focus_password = True
                self.focus_username = False
                return ("switch_focus", None)

            if self.login_btn_rect.collidepoint(event.pos):
                return ("login", (self.username, self.password))

            if self.create_btn_rect.collidepoint(event.pos):
                return ("create_account", (self.username, self.password))

        return None

    def set_status(self, message: str):
        self.status = message

    def reset(self):
        self.username = ""
        self.password = ""
        self.status = "Enter username and password"
        self.focus_username = True
        self.focus_password = False
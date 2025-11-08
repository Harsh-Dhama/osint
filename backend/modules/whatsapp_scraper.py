"""
WhatsApp Profile Scraper Module (updated)
Playwright-based WhatsApp Web scraper with stealth, improved selectors,
error handling, session persistence, and human-like interactions.
"""
import sys
import asyncio
import base64
import json
import logging
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image
import re

# Set Windows Proactor event loop policy for Playwright subprocess support
if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

from playwright.async_api import (
    async_playwright,
    Page,
    Browser,
    Playwright,
    BrowserContext,
    TimeoutError,
    BrowserType,
)

# keep a stable alias for the rest of the code and for clarity to linters/type-checkers
PlaywrightTimeoutError = TimeoutError

# Correct stealth import
# Robust import of Stealth helper from playwright-stealth
try:
    from playwright_stealth.stealth import Stealth  # preferred
except Exception:  # pragma: no cover - fallback for different packaging
    try:
        from playwright_stealth import Stealth
    except Exception:
        Stealth = None  # type: ignore

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class WhatsAppScraper:
    def __init__(self, profile_path: str = "data/whatsapp_profile", session_file: str = "data/whatsapp_session.json"):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_initialized = False

        # session / persistence
        self.profile_path = Path(profile_path)
        self.session_file = session_file
        self.profile_path.mkdir(parents=True, exist_ok=True)

        # rate limiting state
        self.request_count = 0
        self.last_request_time = 0.0

        # login state
        self._logged_in = False

        # debug artifacts
        self.last_debug_screenshot = None  # type: Optional[str]
        self.last_debug_html = None  # type: Optional[str]

        logger.info("[WhatsAppScraper] Instance created")

    async def initialize(self, headless: bool = True):
        """Start Playwright + Chromium with stealth and realistic context."""
        if self.is_initialized:
            logger.info("[WhatsAppScraper] Already initialized")
            return

        logger.info("[WhatsAppScraper] Initializing Playwright browser...")

        # Ensure Windows Proactor event loop policy is set before starting Playwright
        if sys.platform.startswith("win"):
            try:
                loop = asyncio.get_event_loop()
                if not isinstance(loop.get_loop_policy() if hasattr(loop, 'get_loop_policy') else asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                    logger.info("[WhatsAppScraper] Set Windows Proactor event loop policy")
            except Exception as e:
                logger.warning(f"[WhatsAppScraper] Could not set event loop policy: {e}")

        try:
            self.playwright = await async_playwright().start()
            # Launch options
            chromium = self.playwright.chromium
            launch_args = [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-web-security",
                "--window-size=1920,1080",
            ]

            # Prefer a persistent browser context when running headful (interactive QR)
            # This uses a real user data directory which more closely mimics a real
            # browser profile and improves WhatsApp QR reliability.
            storage_state_path = self.session_file if Path(self.session_file).exists() else None
            if not headless:
                # Launch persistent context using the profile path
                # Ensure profile directory exists
                self.profile_path.mkdir(parents=True, exist_ok=True)
                self.context = await chromium.launch_persistent_context(
                    user_data_dir=str(self.profile_path),
                    headless=False,
                    args=launch_args,
                    viewport={"width": 1920, "height": 1080},
                    device_scale_factor=1,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="en-US",
                    timezone_id="Asia/Kolkata",
                    permissions=["clipboard-read", "clipboard-write"],
                )
                # attach to an existing page if present
                pages = self.context.pages
                self.page = pages[0] if pages else await self.context.new_page()
            else:
                self.browser = await chromium.launch(headless=headless, args=launch_args)
                # create context for headless usage; if storage_state exists, load it for cookies/localStorage
                self.context = await self.browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    device_scale_factor=1,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="en-US",
                    timezone_id="Asia/Kolkata",
                    permissions=["clipboard-read", "clipboard-write"],
                    storage_state=storage_state_path,
                )
                self.page = await self.context.new_page()

            # sensible default timeouts
            try:
                self.context.set_default_timeout(15000)  # 15s default
            except Exception as e:
                logger.warning(f"Could not set context timeout: {e}")
            
            try:
                if self.page:
                    self.page.set_default_navigation_timeout(20000)
            except Exception as e:
                logger.warning(f"Could not set page navigation timeout: {e}")

            # apply stealth
            if Stealth is not None:
                try:
                    stealth = Stealth()
                    # the package exposes a couple of helpers; try async method first then fallback
                    if hasattr(stealth, "apply_stealth_async"):
                        await stealth.apply_stealth_async(self.page)
                    elif hasattr(stealth, "apply_stealth"):
                        stealth.apply_stealth(self.page)
                    logger.info("[WhatsAppScraper] Stealth applied successfully")
                except Exception as e:
                    logger.warning(f"[WhatsAppScraper] Could not apply stealth (continuing anyway): {e}")

            # small extra init script to cover common signals
            await self.page.add_init_script(
                """() => {
                    try {
                      Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                      Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
                      Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                      window.chrome = { runtime: {} };
                    } catch (e) {}
                }"""
            )

            # load cookies if storage_state not already provided
            if not storage_state_path:
                await self._load_session()

            # small human-like pause
            await asyncio.sleep(random.uniform(1.0, 2.5))

            logger.info("[WhatsAppScraper] Initialized successfully")
            self.is_initialized = True

        except Exception as e:
            logger.exception("[WhatsAppScraper] Initialization failed: %s", e)
            raise

    async def _load_session(self):
        """Load saved cookies / storage state if available."""
        try:
            # prefer storage_state if file exists (Playwright format)
            storage_state_file = Path(self.session_file)
            if storage_state_file.exists():
                try:
                    # Playwright can load storage state by passing path to new_context,
                    # but we already created context: try to add cookies/localStorage manually
                    with open(storage_state_file, "r", encoding="utf-8") as f:
                        state = json.load(f)
                    # if cookies present, add them
                    cookies = state.get("cookies") or state
                    if isinstance(cookies, list) and self.context:
                        await self.context.add_cookies(cookies)
                        logger.info("[WhatsAppScraper] Loaded cookies from session file")
                except Exception:
                    # older cookie-only format: try reading as list
                    try:
                        with open(self.session_file, "r", encoding="utf-8") as f:
                            cookies = json.load(f)
                        if isinstance(cookies, list) and self.context:
                            await self.context.add_cookies(cookies)
                            logger.info("[WhatsAppScraper] Loaded cookies (fallback) from session file")
                    except Exception:
                        logger.warning("[WhatsAppScraper] Failed to load session file (ignored)")
        except Exception as e:
            logger.warning("[WhatsAppScraper] _load_session error: %s", e)

    async def _save_session(self):
        """Save storage/state for persistence. Use storage_state if supported otherwise cookies."""
        try:
            # prefer storage_state method
            if self.context and hasattr(self.context, "storage_state"):
                try:
                    # saves cookies + localStorage + origins
                    await self.context.storage_state(path=self.session_file)
                    logger.info("[WhatsAppScraper] Saved storage_state to %s", self.session_file)
                    return
                except Exception:
                    logger.warning("[WhatsAppScraper] storage_state save failed, falling back to cookies")

            # fallback: save cookies to file
            if self.context:
                cookies = await self.context.cookies()
                os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
                with open(self.session_file, "w", encoding="utf-8") as f:
                    json.dump(cookies, f)
                logger.info("[WhatsAppScraper] Saved cookies to %s", self.session_file)
        except Exception as e:
            logger.error("[WhatsAppScraper] Could not save session: %s", e)

    async def _human_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Random sleep to simulate human behavior."""
        delay = random.uniform(min_sec, max_sec)
        logger.debug("[WhatsAppScraper] Human delay: %.2fs", delay)
        await asyncio.sleep(delay)

    async def _simulate_mouse_and_typing(self):
        """Optional small mouse/typing actions to appear more human."""
        try:
            if not self.page:
                return
            viewport = await self.page.evaluate("() => ({w: window.innerWidth, h: window.innerHeight})")
            x = int(viewport["w"] * random.uniform(0.2, 0.8))
            y = int(viewport["h"] * random.uniform(0.05, 0.15))
            try:
                await self.page.mouse.move(x, y, steps=random.randint(5, 12))
                # small random key press
                await self.page.keyboard.down("Shift")
                await self.page.keyboard.up("Shift")
            except Exception:
                pass
        except Exception:
            pass

    async def _rate_limit_check(self):
        """Simple rate limiting: ensure at least 12 seconds between requests by default."""
        min_interval = 12.0
        now = time.time()
        since = now - self.last_request_time
        if since < min_interval:
            wait_time = min_interval - since
            logger.info("[WhatsAppScraper] Rate limit: waiting %.1fs", wait_time)
            await asyncio.sleep(wait_time)
        self.last_request_time = time.time()
        self.request_count += 1

    async def get_qr_code(self) -> Optional[str]:
        """Capture QR code as base64 PNG (data URI). Returns None if QR not shown (already logged in)."""
        if not self.page:
            raise RuntimeError("Scraper not initialized. Call initialize() first.")
        try:
            logger.info("[WhatsAppScraper] Navigating to WhatsApp Web to get QR code")
            await self.page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(1.0, 2.5))

            # if already logged in, skip
            if await self.check_session_active():
                logger.info("[WhatsAppScraper] Already logged in; no QR required")
                return None

            # try multiple selectors for QR canvas
            qr_selectors = [
                'canvas[aria-label="Scan this QR code to link a device!"]',
                'canvas[aria-label*="Scan"]',
                'div[data-ref] canvas',
                'canvas',
            ]

            qr_element = None
            for sel in qr_selectors:
                try:
                    await self.page.wait_for_selector(sel, timeout=5000)
                    qr_element = await self.page.query_selector(sel)
                    if qr_element:
                        logger.info("[WhatsAppScraper] Found QR element using selector: %s", sel)
                        break
                except PlaywrightTimeoutError:
                    continue
                except Exception:
                    continue

            if not qr_element:
                logger.warning("[WhatsAppScraper] QR element not found on the page")
                await self._capture_debug_artifacts(prefix="qr_not_found")
                return None

            # allow QR to render fully
            await asyncio.sleep(1.0)
            # If the QR element is a canvas, get its exact dataURL to avoid
            # scaling/overlay distortions that can make the QR unscannable.
            try:
                tag = await qr_element.evaluate("el => (el.tagName || '').toLowerCase()")
                if tag == 'canvas':
                    data_uri = await qr_element.evaluate("el => el.toDataURL('image/png')")
                    if data_uri and data_uri.startswith('data:image'):
                        logger.info("[WhatsAppScraper] Captured QR code from canvas (dataURI length=%d)", len(data_uri))
                        return data_uri
                # fallback to element screenshot if not canvas or eval fails
            except Exception:
                logger.debug("[WhatsAppScraper] canvas toDataURL extraction failed, falling back to screenshot")

            screenshot_bytes = await qr_element.screenshot(type="png")
            b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
            data_uri = f"data:image/png;base64,{b64}"
            logger.info("[WhatsAppScraper] Captured QR code via screenshot (size=%d bytes)", len(b64))
            return data_uri
        except Exception as e:
            logger.exception("[WhatsAppScraper] get_qr_code error: %s", e)
            await self._capture_debug_artifacts(prefix="qr_error")
            return None

    async def show_whatsapp_web_for_login(self):
        """
        Navigate to WhatsApp Web in a VISIBLE browser window and keep it open
        so the user can scan the QR code directly from the actual WhatsApp page.
        This avoids any QR extraction/modification issues.
        """
        if not self.page:
            raise RuntimeError("Scraper not initialized. Call initialize() first.")
        
        try:
            logger.info("[WhatsAppScraper] Opening WhatsApp Web in visible browser for QR scan")
            await self.page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            # Check if already logged in
            if await self.check_session_active():
                logger.info("[WhatsAppScraper] Already logged in to WhatsApp Web")
                return
            
            # Wait for QR to appear
            qr_selectors = [
                'canvas[aria-label="Scan this QR code to link a device!"]',
                'canvas[aria-label*="Scan"]',
                'div[data-ref] canvas',
                'canvas',
            ]
            
            for sel in qr_selectors:
                try:
                    await self.page.wait_for_selector(sel, timeout=5000)
                    logger.info("[WhatsAppScraper] QR code is visible in browser window")
                    break
                except:
                    continue
            
            logger.info("[WhatsAppScraper] WhatsApp Web page loaded. User can now scan QR from browser window.")
            # Keep the browser window open - don't close it
            # The user will scan the QR code directly from this window
            
        except Exception as e:
            logger.exception("[WhatsAppScraper] show_whatsapp_web_for_login error: %s", e)
            raise

    async def wait_for_login(self, timeout: int = 300) -> bool:
        """Wait for user to scan QR and for chat list to appear. If QR expires, the page is reloaded."""
        if not self.page:
            raise RuntimeError("Scraper not initialized. Call initialize() first.")

        logger.info("[WhatsAppScraper] wait_for_login - polling started (timeout=%ds)", timeout)
        start = time.time()
        reload_interval = 60  # reload page periodically to refresh QR if still not scanned
        check_count = 0

        while time.time() - start < timeout:
            check_count += 1
            elapsed = time.time() - start
            logger.debug(f"[WhatsAppScraper] Polling check #{check_count} at {elapsed:.1f}s")
            
            try:
                if await self.check_session_active():
                        logger.info("[WhatsAppScraper] ✓✓✓ LOGIN DETECTED! Saving session...")
                        # Save the storage state immediately so subsequent runs reuse the session
                        try:
                            await self._save_session()
                            logger.info("[WhatsAppScraper] ✓ Session saved successfully")
                        except Exception as e:
                            logger.warning(f"[WhatsAppScraper] Failed to save session: {e}")
                        return True
            except Exception as e:
                logger.debug(f"[WhatsAppScraper] Check failed: {e}")
                pass

            # reload every reload_interval seconds to refresh QR if present
            # BUT don't reload if we're close to detecting login (avoid interrupting)
            if int(elapsed) % reload_interval == 0 and elapsed > 10:
                try:
                    await self.page.reload()
                    logger.debug("[WhatsAppScraper] Reloaded page while waiting for login")
                except Exception:
                    pass

            await asyncio.sleep(2)

        logger.warning("[WhatsAppScraper] wait_for_login timed out after %ds (%d checks)", timeout, check_count)
        return False

    async def check_session_active(self) -> bool:
        """Check if chat-list (logged-in state) exists."""
        if not self.page:
            logger.debug("[WhatsAppScraper] check_session_active: No page object")
            return False
        try:
            # Updated selectors for latest WhatsApp Web
            selectors = [
                'div[data-testid="chat-list"]',
                '#pane-side',  # More reliable selector for chat pane
                '#side',
                'div[aria-label="Chat list"]',
                'div[role="grid"]',  # Chat list is a grid
            ]
            for sel in selectors:
                try:
                    el = await self.page.query_selector(sel)
                    if el:
                        logger.info(f"[WhatsAppScraper] ✓ Session active - found selector: {sel}")
                        self._logged_in = True
                        return True
                except Exception as e:
                    logger.debug(f"[WhatsAppScraper] Selector {sel} not found: {e}")
                    continue
            logger.debug("[WhatsAppScraper] Session not active - no chat list found")
            self._logged_in = False
            return False
        except Exception as e:
            logger.error(f"[WhatsAppScraper] check_session_active error: {e}")
            return False

    async def scrape_profile(self, phone_number: str, retry_count: int = 2, use_fallback: bool = True) -> Dict[str, Any]:
        """
        Fully automated profile scraping - navigates and extracts data automatically.
        User only provides phone number, system does everything else.
        
        Process:
        1. Navigate to web.whatsapp.com/send?phone=NUMBER
        2. Wait for page load
        3. Try multiple extraction methods automatically
        4. Return all available data
        """
        await self._rate_limit_check()

        result: Dict[str, Any] = {
            "phone_number": phone_number,
            "display_name": None,
            "about": None,
            "profile_picture": None,
            "last_seen": None,
            "is_available": False,
            "status": "failed",
            "error": None,
            "method": "automation",  # track which method succeeded
        }

        try:
            if not self.page or not self.is_initialized:
                raise RuntimeError("Scraper not initialized. Call initialize() first.")

            # ensure logged in
            if not await self.check_session_active():
                result["error"] = "Not logged in"
                return result

            # small human behavior simulation
            await self._simulate_mouse_and_typing()
            await self._human_delay(2.0, 5.0)

            # format phone number: remove non-digit chars, but keep leading country prefix if present
            clean = "".join([c for c in phone_number if c.isdigit()])
            # WhatsApp send expects numbers without +
            url = f"https://web.whatsapp.com/send?phone={clean}"
            logger.info("[WhatsAppScraper] Navigating to %s (for %s)", url, phone_number)

            await self.page.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(2.5, 4.0))

            # quick check for invalid number element
            try:
                invalid_sel = 'div[data-testid="invalid-number"]'
                invalid_el = await self.page.query_selector(invalid_sel)
                if invalid_el:
                    result["error"] = "Number not on WhatsApp"
                    logger.warning("[WhatsAppScraper] %s is not on WhatsApp", phone_number)
                    return result
            except Exception:
                pass

            # get display name - try a few selectors (WhatsApp changes often)
            name_selectors = [
                'header span[title]',  # older styling
                'span[data-testid="conversation-info-header-chat-title"]',
                'header [data-testid="contact-name"]',
                'header ._21nHd',  # fallback class
            ]
            display_name = None
            for sel in name_selectors:
                try:
                    el = await self.page.query_selector(sel)
                    if el:
                        display_name = (await el.get_attribute("title")) or (await el.text_content())
                        if display_name:
                            display_name = display_name.strip()
                            break
                except Exception:
                    continue
            result["display_name"] = display_name or result["display_name"]
            if display_name:
                result["is_available"] = True
                logger.info("[WhatsAppScraper] Found display name: %s", display_name)

            # open profile drawer to access About and profile photo reliably
            try:
                # header click to open contact info
                header_selector = 'header'
                try:
                    await self.page.wait_for_selector(header_selector, timeout=5000)
                    await self.page.click(header_selector)
                    await asyncio.sleep(random.uniform(1.0, 2.5))
                except PlaywrightTimeoutError:
                    logger.debug("[WhatsAppScraper] Header not clickable / not found")

                # About/status selector variants
                about_selectors = [
                    'span[data-testid="status-v3-text"]',
                    'div[data-testid="about-drawer"] span[dir="auto"]',
                    'div[data-testid="about-info"]',
                ]
                about_text = None
                for sel in about_selectors:
                    try:
                        el = await self.page.query_selector(sel)
                        if el:
                            about_text = (await el.text_content() or "").strip()
                            if about_text:
                                result["about"] = about_text
                                logger.info("[WhatsAppScraper] Found about: %s", about_text)
                                break
                    except Exception:
                        continue

                # profile picture: try common selectors, download or store src
                img_selectors = [
                    'img[alt="profile photo"]',
                    'img[data-testid="image-thumb"]',
                    'img[data-testid="profile-picture"]',
                    'div[data-testid="image-view"] img',
                ]
                profile_src = None
                for sel in img_selectors:
                    try:
                        el = await self.page.query_selector(sel)
                        if el:
                            profile_src = await el.get_attribute("src")
                            if profile_src:
                                break
                    except Exception:
                        continue

                if profile_src:
                    # avoid default placeholder
                    if "default-user" not in profile_src:
                        # if data URL, save directly; otherwise attempt download via page
                        if profile_src.startswith("data:image"):
                            # save to file
                            b64 = profile_src.split(",", 1)[1]
                            data = base64.b64decode(b64)
                            file_path = self._save_binary_profile_picture(data, clean)
                            result["profile_picture"] = file_path
                        else:
                            # try to fetch via aiohttp
                            saved = await self._download_image(profile_src, clean)
                            result["profile_picture"] = saved
                        logger.info("[WhatsAppScraper] Profile picture saved: %s", result["profile_picture"])
                # close drawer if possible
                try:
                    close_selectors = [
                        'button[aria-label="Close"]',
                        'div[role="button"][aria-label="Close"]',
                        'span[data-testid="x"]',
                    ]
                    for sel in close_selectors:
                        try:
                            el = await self.page.query_selector(sel)
                            if el:
                                await el.click()
                                await asyncio.sleep(0.5)
                                break
                        except Exception:
                            continue
                except Exception:
                    pass

            except Exception as e:
                logger.warning("[WhatsAppScraper] Could not open profile drawer: %s", e)

            # AUTOMATIC FALLBACK - try JS extraction if selectors didn't find data
            if use_fallback and not result["display_name"]:
                logger.info("[WhatsAppScraper] Automation failed to get name; trying automatic fallback extraction")
                fallback_data = await self._extract_profile_from_raw_data(clean)
                if fallback_data:
                    result.update(fallback_data)
                    result["method"] = "fallback_auto"
                    logger.info("[WhatsAppScraper] Automatic fallback succeeded: %s", fallback_data)
            
            # If still no data, try one more time with longer wait
            if use_fallback and not result["display_name"]:
                logger.info("[WhatsAppScraper] Trying extended wait for lazy-loaded content...")
                await asyncio.sleep(random.uniform(3.0, 5.0))
                fallback_data = await self._extract_profile_from_raw_data(clean)
                if fallback_data:
                    result.update(fallback_data)
                    result["method"] = "fallback_delayed"
                    logger.info("[WhatsAppScraper] Delayed fallback succeeded: %s", fallback_data)

            result["status"] = "success" if result["display_name"] or result["is_available"] else "partial"
            return result

        except PlaywrightTimeoutError:
            result["error"] = "Timeout while loading profile"
            logger.warning("[WhatsAppScraper] Timeout for %s", phone_number)
            # Try fallback if enabled
            if use_fallback:
                try:
                    clean = "".join([c for c in phone_number if c.isdigit()])
                    fallback_data = await self._extract_profile_from_raw_data(clean)
                    if fallback_data:
                        result.update(fallback_data)
                        result["method"] = "fallback_after_timeout"
                        result["status"] = "partial"
                        logger.info("[WhatsAppScraper] Fallback after timeout: %s", fallback_data)
                except Exception:
                    pass
            return result
        except Exception as e:
            result["error"] = str(e)
            logger.exception("[WhatsAppScraper] Error scraping %s: %s", phone_number, e)
            # Try fallback if enabled
            if use_fallback:
                try:
                    clean = "".join([c for c in phone_number if c.isdigit()])
                    fallback_data = await self._extract_profile_from_raw_data(clean)
                    if fallback_data:
                        result.update(fallback_data)
                        result["method"] = "fallback_after_error"
                        result["status"] = "partial"
                        logger.info("[WhatsAppScraper] Fallback after error: %s", fallback_data)
                except Exception:
                    pass
            return result

    def _save_binary_profile_picture(self, data: bytes, clean_number: str) -> str:
        """Save bytes to downloads folder and return local path (relative)."""
        downloads = Path("uploads") / "whatsapp" / "profiles"
        downloads.mkdir(parents=True, exist_ok=True)
        filename = f"{clean_number}.jpg"
        path = downloads / filename
        path.write_bytes(data)
        return str(path.resolve())

    async def _download_image(self, url: str, clean_number: str) -> Optional[str]:
        """
        Download profile image from WhatsApp CDN or any URL.
        Handles WhatsApp's media CDN URLs with proper headers.
        """
        try:
            import aiohttp
            downloads = Path("uploads") / "whatsapp" / "profiles"
            downloads.mkdir(parents=True, exist_ok=True)
            filename = f"{clean_number}.jpg"
            path = downloads / filename
            
            # Prepare headers for WhatsApp CDN
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://web.whatsapp.com/',
                'Origin': 'https://web.whatsapp.com',
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        if len(content) > 100:  # Ensure it's not an error page
                            path.write_bytes(content)
                            logger.info(f"[WhatsAppScraper] ✓ Downloaded image: {len(content)} bytes")
                            return str(path.resolve())
                        else:
                            logger.warning(f"[WhatsAppScraper] Image too small: {len(content)} bytes")
                    else:
                        logger.warning(f"[WhatsAppScraper] Download failed: HTTP {resp.status}")
        except Exception as e:
            logger.warning(f"[WhatsAppScraper] _download_image failed: {e}")
        return None

    async def _capture_debug_artifacts(self, prefix: str = "debug"):
        """Capture full-page screenshot and HTML for debugging and store paths."""
        try:
            if not self.page:
                return
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            screenshot_path = reports_dir / f"{prefix}_{ts}.png"
            html_path = reports_dir / f"{prefix}_{ts}.html"
            try:
                await self.page.screenshot(path=str(screenshot_path), full_page=True)
                self.last_debug_screenshot = str(screenshot_path.resolve())
            except Exception:
                self.last_debug_screenshot = None
            try:
                content = await self.page.content()
                html_path.write_text(content, encoding="utf-8")
                self.last_debug_html = str(html_path.resolve())
            except Exception:
                self.last_debug_html = None
            logger.info("[WhatsAppScraper] Debug artifacts saved: screenshot=%s html=%s", self.last_debug_screenshot, self.last_debug_html)
        except Exception:
            pass

    async def _extract_profile_from_raw_data(self, clean_number: str) -> Optional[Dict[str, Any]]:
        """
        Fallback extraction: parse raw HTML, evaluate JS in console to extract WhatsApp Web internal state.
        This works when normal selectors fail because WhatsApp changes UI or privacy settings block automation.
        
        Strategy:
        1. Try to extract from WhatsApp Web internal React/JS state via page.evaluate
        2. Parse raw HTML for known patterns
        3. Look for profile data in network responses (if available)
        """
        try:
            if not self.page:
                return None
            
            logger.info("[WhatsAppScraper] Attempting raw data extraction for %s", clean_number)
            
            # Method 1: Extract from WhatsApp Web's internal store via console
            # WhatsApp Web uses React and stores contact/chat data in window.Store or similar
            js_extract = """
            () => {
                try {
                    // Common patterns for WhatsApp Web internal stores
                    const stores = [
                        window.Store,
                        window.WAWeb,
                        window.WA,
                        window.__WAWEB,
                    ];
                    
                    let contactData = {};
                    
                    // Try to find contact store
                    for (const store of stores) {
                        if (!store) continue;
                        
                        // Look for contact/chat models
                        if (store.Contact) {
                            // Try to get all contacts
                            const contacts = store.Contact.getModelsArray ? store.Contact.getModelsArray() : [];
                            for (const contact of contacts) {
                                if (contact.id && contact.id.user) {
                                    contactData.name = contact.name || contact.pushname || contact.displayName;
                                    contactData.about = contact.status || contact.statusText;
                                    contactData.profilePic = contact.profilePicThumb || contact.profilePicThumbObj?.img;
                                    if (contactData.name) break;
                                }
                            }
                        }
                        
                        // Try Chat store
                        if (store.Chat && !contactData.name) {
                            const chats = store.Chat.getModelsArray ? store.Chat.getModelsArray() : [];
                            const activeChat = chats.find(c => c.isUser || c.isGroup === false);
                            if (activeChat) {
                                contactData.name = activeChat.contact?.name || activeChat.contact?.pushname;
                                contactData.about = activeChat.contact?.status;
                                contactData.profilePic = activeChat.contact?.profilePicThumb?.img;
                            }
                        }
                    }
                    
                    // Try global objects
                    if (!contactData.name) {
                        const header = document.querySelector('header span[dir="auto"]');
                        if (header) contactData.name = header.textContent;
                    }
                    
                    // Try to get profile picture from any visible img
                    if (!contactData.profilePic) {
                        const imgs = Array.from(document.querySelectorAll('img[src*="blob:"], img[src*="data:image"]'));
                        const profileImg = imgs.find(img => 
                            img.alt && (img.alt.includes('profile') || img.alt.includes('photo'))
                        );
                        if (profileImg) contactData.profilePic = profileImg.src;
                    }
                    
                    return contactData;
                } catch (e) {
                    return { error: e.toString() };
                }
            }
            """
            
            try:
                extracted = await self.page.evaluate(js_extract)
                if extracted and isinstance(extracted, dict):
                    result = {}
                    if extracted.get("name"):
                        result["display_name"] = extracted["name"]
                        result["is_available"] = True
                    if extracted.get("about"):
                        result["about"] = extracted["about"]
                    if extracted.get("profilePic"):
                        # Try to download the profile pic
                        pic_src = extracted["profilePic"]
                        if pic_src.startswith("data:image"):
                            # Save data URL
                            b64 = pic_src.split(",", 1)[1]
                            data = base64.b64decode(b64)
                            file_path = self._save_binary_profile_picture(data, clean_number)
                            result["profile_picture"] = file_path
                        elif pic_src.startswith("blob:") or pic_src.startswith("http"):
                            # Try to fetch
                            saved = await self._download_image(pic_src, clean_number)
                            if saved:
                                result["profile_picture"] = saved
                    
                    if result:
                        logger.info("[WhatsAppScraper] JS extraction found data: %s", result)
                        return result
            except Exception as e:
                logger.warning("[WhatsAppScraper] JS extraction failed: %s", e)
            
            # Method 2: Parse raw HTML for patterns
            try:
                html = await self.page.content()
                
                # Look for name in common patterns
                import re
                name_patterns = [
                    r'<span[^>]*title="([^"]+)"[^>]*>',
                    r'data-testid="conversation-info-header-chat-title"[^>]*>([^<]+)<',
                    r'"displayName":"([^"]+)"',
                    r'"pushname":"([^"]+)"',
                ]
                
                for pattern in name_patterns:
                    matches = re.findall(pattern, html)
                    if matches:
                        name = matches[0].strip()
                        if name and len(name) > 1:
                            logger.info("[WhatsAppScraper] HTML extraction found name: %s", name)
                            return {
                                "display_name": name,
                                "is_available": True,
                            }
            except Exception as e:
                logger.warning("[WhatsAppScraper] HTML parsing failed: %s", e)
            
            return None
            
        except Exception as e:
            logger.exception("[WhatsAppScraper] Raw extraction error: %s", e)
            return None

    async def scrape_multiple(self, phone_numbers: List[str], delay_between: Tuple[int, int] = (2, 5), progress_callback=None, use_fallback: bool = True) -> Dict[str, Dict]:
        """Scrape many numbers sequentially with delays and progress reporting."""
        results: Dict[str, Dict] = {}
        for idx, phone in enumerate(phone_numbers, start=1):
            logger.info("[WhatsAppScraper] (%d/%d) scraping %s", idx, len(phone_numbers), phone)
            res = await self.scrape_profile(phone, use_fallback=use_fallback)
            results[phone] = res
            # progress callback
            if progress_callback:
                try:
                    await progress_callback(idx, len(phone_numbers), res)
                except Exception:
                    pass
            if idx < len(phone_numbers):
                delay = random.uniform(*delay_between)
                logger.debug("[WhatsAppScraper] Sleeping %.1fs before next number", delay)
                await asyncio.sleep(delay)
        return results

    async def auto_navigate_and_extract(self, phone_number: str) -> Dict[str, Any]:
        """
        FULLY AUTOMATED: Navigate to new chat for each contact and extract all data automatically.
        This is the main method for fully automated scraping.
        
        Process:
        1. Navigate to web.whatsapp.com/send?phone=NUMBER (opens NEW chat window)
        2. Wait for chat to load completely
        3. Automatically click header to open contact's profile drawer
        4. Extract name, bio/about, profile picture from CONTACT's profile
        5. Verify we're viewing the correct contact (not our own profile)
        6. Return complete profile data
        
        User provides only phone number, system does everything automatically.
        Returns complete profile data ready for frontend display and report generation.
        """
        logger.info("[WhatsAppScraper] AUTO-NAVIGATE: Starting fully automated extraction for %s", phone_number)
        
        # Convert to string first (handles int, numpy.int64, etc.)
        phone_number_str = str(phone_number)
        
        result = {
            "phone_number": phone_number_str,
            "display_name": None,
            "about": None,
            "profile_picture": None,
            "last_seen": None,
            "is_available": False,
            "status": "processing",
            "error": None,
            "method": "auto_navigate",
            "extraction_timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            if not self.page:
                raise RuntimeError("Scraper not initialized")
            
            # Clean phone number (remove non-digits)
            clean = "".join([c for c in phone_number_str if c.isdigit()])
            if not clean:
                result["error"] = "Invalid phone number format"
                result["status"] = "failed"
                return result
            
            # Navigate to direct WhatsApp chat link (opens NEW chat for this contact)
            url = f"https://web.whatsapp.com/send?phone={clean}"
            logger.info("[WhatsAppScraper] AUTO-NAVIGATE: Opening NEW chat window for %s", url)
            
            # Use domcontentloaded first (faster), then wait for specific elements
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            logger.info("[WhatsAppScraper] AUTO-NAVIGATE: Page DOM loaded, waiting for WhatsApp UI...")
            
            # Wait for WhatsApp to render (it's a React SPA that loads in stages)
            # Increased wait time to ensure chat fully loads
            await asyncio.sleep(12.0)
            
            # Check if we're actually logged in
            try:
                # If QR code is visible, we're not logged in
                qr_visible = await self.page.query_selector('canvas[aria-label="Scan this QR code to link a device!"]')
                if qr_visible:
                    result["error"] = "Not logged in to WhatsApp - QR code visible"
                    result["status"] = "failed"
                    logger.error("[WhatsAppScraper] AUTO-NAVIGATE: ❌ Not logged in! QR code is visible")
                    try:
                        await self.page.screenshot(path=f"reports/whatsapp/not_logged_in_{clean}.png")
                    except:
                        pass
                    return result
            except Exception:
                pass
            
            # CRITICAL: WhatsApp loads UI in stages, especially for new/unsaved contacts
            # We need to wait for the chat header to fully load before proceeding
            logger.info("[WhatsAppScraper] AUTO-NAVIGATE: Waiting for chat UI to render...")
            header_ready = False
            for attempt in range(15):  # More attempts
                try:
                    # Check if chat header is loaded (indicates chat is ready)
                    header = await self.page.query_selector('header[data-testid="conversation-header"]')
                    if header:
                        # Verify header has content (name or profile pic)
                        has_content = await self.page.evaluate("""
                            () => {
                                const header = document.querySelector('header[data-testid="conversation-header"]');
                                if (!header) return false;
                                // Check for name or profile picture
                                const hasName = header.querySelector('span[dir="auto"]');
                                const hasPic = header.querySelector('img');
                                return !!(hasName || hasPic);
                            }
                        """)
                        if has_content:
                            header_ready = True
                            logger.info(f"[WhatsAppScraper] AUTO-NAVIGATE: ✓✓ Chat header ready after {attempt + 1} attempts")
                            break
                except Exception as e:
                    logger.debug(f"[WhatsAppScraper] Header check error: {e}")
                logger.debug(f"[WhatsAppScraper] AUTO-NAVIGATE: Waiting for header... attempt {attempt + 1}/15")
                await asyncio.sleep(9.0)  # Longer wait between checks
            
            if not header_ready:
                logger.warning("[WhatsAppScraper] AUTO-NAVIGATE: Header not fully loaded after 15 attempts (45 seconds)")
                # Take screenshot for debugging
                try:
                    await self.page.screenshot(path=f"reports/whatsapp/header_not_loaded_{clean}.png")
                    logger.warning(f"[WhatsAppScraper] Debug screenshot saved: reports/whatsapp/header_not_loaded_{clean}.png")
                except:
                    pass
                logger.warning("[WhatsAppScraper] AUTO-NAVIGATE: Attempting extraction anyway (may fail)...")
            
            # Additional wait for animations/lazy loading
            await asyncio.sleep(7.0)  # Longer wait for animations
            
            # Check if number is invalid/not on WhatsApp
            try:
                invalid_el = await self.page.query_selector('div[data-testid="invalid-number"]')
                if invalid_el:
                    result["error"] = "Phone number not on WhatsApp"
                    result["status"] = "failed"
                    logger.warning("[WhatsAppScraper] AUTO-NAVIGATE: %s not on WhatsApp", phone_number)
                    return result
            except Exception:
                pass
            
            # Extract data using sequential methods (each builds on the previous)
            logger.info("[WhatsAppScraper] AUTO-NAVIGATE: Extracting profile data...")
            
            # Method 1: Open profile drawer to get full details (name, bio, profile pic)
            # This is the PRIMARY extraction method - opens contact's profile drawer
            logger.info("[WhatsAppScraper] AUTO-NAVIGATE: Opening contact's profile drawer...")
            drawer_name, about, photo = await self._try_extract_profile_drawer(clean)
            
            # Use drawer data (most reliable)
            if drawer_name:
                result["display_name"] = drawer_name
                result["is_available"] = True
                logger.info(f"[WhatsAppScraper] AUTO-NAVIGATE: ✓ Got name from drawer: {drawer_name}")
            if about:
                result["about"] = about
                logger.info(f"[WhatsAppScraper] AUTO-NAVIGATE: ✓ Got bio: {about[:50]}...")
            if photo:
                result["profile_picture"] = photo
                logger.info(f"[WhatsAppScraper] AUTO-NAVIGATE: ✓ Got profile picture: {photo}")
            
            # Method 2: Fallback - Try quick name extraction from chat header (only if drawer failed)
            if not result["display_name"]:
                logger.info("[WhatsAppScraper] AUTO-NAVIGATE: Drawer name failed, trying header fallback...")
                name = await self._try_extract_name()
                if name:
                    result["display_name"] = name
                    result["is_available"] = True
                    logger.info(f"[WhatsAppScraper] AUTO-NAVIGATE: ✓ Got name from header: {name}")
            
            # Method 3: If still no data, use JS extraction fallback
            if not result["display_name"] and not result["about"] and not result["profile_picture"]:
                logger.info("[WhatsAppScraper] AUTO-NAVIGATE: Using JavaScript extraction fallback...")
                js_data = await self._extract_profile_from_raw_data(clean)
                if js_data:
                    # Merge JS data (only fill in missing fields)
                    for key, value in js_data.items():
                        if value and not result.get(key):
                            result[key] = value
                    result["method"] = "auto_navigate_js_fallback"
                    logger.info(f"[WhatsAppScraper] AUTO-NAVIGATE: ✓ JS fallback provided: {js_data}")
            
            # Set final status based on what we extracted
            if result["display_name"] or result["about"] or result["profile_picture"]:
                result["status"] = "success"
                result["is_available"] = True
            else:
                result["status"] = "partial"
                result["error"] = "Could not extract profile data (contact may have strict privacy settings)"
            
            logger.info("[WhatsAppScraper] AUTO-NAVIGATE: Extraction complete - Status: %s, Name: %s, Bio: %s, Photo: %s", 
                       result["status"], 
                       result["display_name"] or "None", 
                       ("Yes" if result["about"] else "None"),
                       ("Yes" if result["profile_picture"] else "None"))
            return result
            
        except Exception as e:
            logger.exception("[WhatsAppScraper] AUTO-NAVIGATE: Error: %s", e)
            result["error"] = str(e)
            result["status"] = "failed"
            # Capture debug screenshot on error
            try:
                await self._capture_debug_artifacts(prefix=f"auto_extract_error_{clean}")
            except:
                pass
            return result
    
    async def _try_extract_name(self) -> Optional[str]:
        """
        Extract display name ONLY from NEW CHAT header (right side of screen).
        CRITICAL: Must be from the chat conversation area, NOT from sidebar or other areas.
        """
        logger.info("[WhatsAppScraper] Extracting name from NEW CHAT header only...")
        
        # STRICT: Only target the conversation header on the RIGHT side (x > 400px)
        name_selectors = [
            'header[data-testid="conversation-header"] span[data-testid="conversation-info-header-chat-title"]',
            'div[data-testid="conversation-panel-wrapper"] header span[title]',
            'header[data-testid="conversation-header"] span[dir="auto"]',
        ]
        
        # Placeholder texts to ignore (these are NOT real names)
        invalid_names = [
            'click here for contact info',
            'click here',
            'tap here',
            'loading',
            'whatsapp',
            '',
        ]
        
        for sel in name_selectors:
            try:
                el = await self.page.query_selector(sel)
                if el:
                    # VERIFY: Element is on the right side of screen (chat area)
                    box = await el.bounding_box()
                    if box and box['x'] > 350:  # Right side of screen
                        name = (await el.get_attribute("title")) or (await el.text_content())
                        if name and name.strip():
                            name_clean = name.strip().lower()
                            # Check if it's a valid name (not a placeholder)
                            if name_clean not in invalid_names and len(name_clean) > 2:
                                logger.info("[WhatsAppScraper] ✓ Found valid name from CHAT header (x=%.0f): %s", box['x'], name.strip())
                                return name.strip()
                            else:
                                logger.debug(f"[WhatsAppScraper] Ignoring placeholder text: {name.strip()}")
                    else:
                        logger.debug(f"[WhatsAppScraper] Skipping element (wrong position: x={box['x'] if box else 'none'})")
            except Exception as e:
                logger.debug(f"[WhatsAppScraper] Selector {sel} failed: {e}")
                continue
        return None
    
    async def _extract_name_about_from_drawer_dom(self, phone_number: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract name and about directly from drawer DOM using JavaScript.
        This is the PRIMARY method - more reliable than OCR.
        
        Args:
            phone_number: Phone number for logging
            
        Returns:
            Tuple[name, about]: Extracted name and about from drawer DOM
        """
        try:
            logger.info(f"[WhatsAppScraper] 🎯 PRIMARY: Extracting name and about from drawer DOM for {phone_number}")
            
            # Wait a bit to ensure drawer is fully loaded
            await asyncio.sleep(2.0)
            
            # JavaScript to extract name and about from the opened drawer
            result = await self.page.evaluate("""
                () => {
                    const drawer = document.querySelector('div[data-testid="drawer-right"]');
                    if (!drawer) {
                        console.log('[DOM] Drawer not found');
                        return { success: false, error: 'Drawer not found' };
                    }
                    
                    console.log('[DOM] Drawer found, extracting data...');
                    let name = null;
                    let about = null;
                    
                    // ========== EXTRACT NAME ==========
                    // Strategy 1: Look for main header/title
                    const headerElements = drawer.querySelectorAll('h2, [role="heading"], span[dir="auto"]');
                    for (let elem of headerElements) {
                        const text = elem.textContent?.trim();
                        if (!text) continue;
                        
                        // Skip if it's just a phone number
                        const digitsOnly = text.replace(/[^0-9]/g, '');
                        if (digitsOnly.length >= 10) {
                            console.log('[DOM] Skipping phone number:', text);
                            continue;
                        }
                        
                        // Skip common labels
                        const lowerText = text.toLowerCase();
                        if (lowerText.includes('contact info') || 
                            lowerText.includes('media') || 
                            lowerText.includes('about') ||
                            lowerText.includes('starred') ||
                            lowerText.includes('mute')) {
                            continue;
                        }
                        
                        // This should be the name
                        if (text.length >= 2 && text.length <= 50 && !name) {
                            name = text;
                            console.log('[DOM] ✓ Found name:', name);
                            break;
                        }
                    }
                    
                    // ========== EXTRACT ABOUT/BIO ==========
                    // Strategy 1: Look for section with "About" header
                    const sections = drawer.querySelectorAll('section');
                    for (let section of sections) {
                        const sectionText = section.textContent || '';
                        
                        // Check if this section contains "About"
                        if (sectionText.toLowerCase().includes('about')) {
                            console.log('[DOM] Found About section');
                            
                            // Get all spans in this section
                            const spans = section.querySelectorAll('span[dir="auto"]');
                            for (let span of spans) {
                                const text = span.textContent?.trim();
                                if (!text) continue;
                                
                                // Skip the "About" label itself
                                if (text.toLowerCase() === 'about') continue;
                                
                                // This should be the about text
                                if (text.length >= 3 && text.length <= 300) {
                                    about = text;
                                    console.log('[DOM] ✓ Found about:', about);
                                    break;
                                }
                            }
                            
                            if (about) break;
                        }
                    }
                    
                    // Strategy 2: Alternative search if not found
                    if (!about) {
                        console.log('[DOM] About not found in sections, trying alternative...');
                        const allSpans = drawer.querySelectorAll('span[dir="ltr"], span[dir="auto"]');
                        for (let span of allSpans) {
                            const text = span.textContent?.trim();
                            if (!text) continue;
                            
                            // Look for text that seems like a bio (medium length, not a label)
                            if (text.length >= 10 && text.length <= 300) {
                                const lowerText = text.toLowerCase();
                                // Skip common UI labels
                                if (!lowerText.includes('media') && 
                                    !lowerText.includes('starred') && 
                                    !lowerText.includes('mute') && 
                                    !lowerText.includes('notification') &&
                                    !lowerText.includes('encryption') &&
                                    !lowerText.includes('disappearing')) {
                                    about = text;
                                    console.log('[DOM] ✓ Found about (alt):', about);
                                    break;
                                }
                            }
                        }
                    }
                    
                    console.log('[DOM] Final results - Name:', name, '| About:', about);
                    
                    return {
                        success: true,
                        name: name,
                        about: about
                    };
                }
            """)
            
            if result.get('success'):
                extracted_name = result.get('name')
                extracted_about = result.get('about')
                
                if extracted_name:
                    logger.info(f"[WhatsAppScraper] ✅ DOM extracted name: '{extracted_name}'")
                else:
                    logger.warning(f"[WhatsAppScraper] ⚠️ DOM could not extract name")
                    
                if extracted_about:
                    logger.info(f"[WhatsAppScraper] ✅ DOM extracted about: '{extracted_about[:60]}...'")
                else:
                    logger.warning(f"[WhatsAppScraper] ⚠️ DOM could not extract about")
                
                return extracted_name, extracted_about
            else:
                logger.warning(f"[WhatsAppScraper] DOM extraction failed: {result.get('error')}")
                return None, None
                
        except Exception as e:
            logger.error(f"[WhatsAppScraper] DOM extraction error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None, None

    def _extract_from_drawer_screenshot(self, screenshot_path: str, phone: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        FALLBACK METHOD: Extract name, about, and profile picture from drawer screenshot using OCR.
        Only used if DOM extraction fails.
        
        Args:
            screenshot_path: Path to the drawer screenshot
            phone: Phone number for saving profile pic
            
        Returns:
            Tuple[name, about, profile_pic_path]: Extracted data from screenshot
        """
        logger.info(f"[WhatsAppScraper] 🔄 FALLBACK: Using OCR extraction from screenshot")
        name = None
        about = None
        profile_pic_path = None
        
        try:
            logger.info(f"[WhatsAppScraper] 🔍 OCR: Loading screenshot: {screenshot_path}")
            
            if not os.path.exists(screenshot_path):
                logger.error(f"[WhatsAppScraper] ❌ Screenshot not found: {screenshot_path}")
                return None, None, None
            
            img = cv2.imread(screenshot_path)
            if img is None:
                logger.error(f"[WhatsAppScraper] ❌ Failed to load screenshot: {screenshot_path}")
                return None, None, None
            
            height, width = img.shape[:2]
            logger.info(f"[WhatsAppScraper] 📐 Screenshot size: {width}x{height}")

            try:
                logger.info(f"[WhatsAppScraper] 📸 Extracting profile picture from screenshot...")
                # Profile picture is typically at top center of drawer
                profile_top = 80
                profile_height = 250
                profile_left = int(width * 0.1)
                profile_width = int(width * 0.8)
                
                profile_region = img[profile_top:profile_top+profile_height, profile_left:profile_left+profile_width]
                
                # Find circular contours
                gray = cv2.cvtColor(profile_region, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(gray, (9, 9), 2)
                
                circles = cv2.HoughCircles(
                    blurred,
                    cv2.HOUGH_GRADIENT,
                    dp=1.2,
                    minDist=100,
                    param1=50,
                    param2=30,
                    minRadius=50,
                    maxRadius=150
                )
                
                if circles is not None:
                    circles = np.uint16(np.around(circles))
                    circle = circles[0][0]
                    center_x, center_y, radius = circle
                    
                    crop_x = max(0, center_x - radius)
                    crop_y = max(0, center_y - radius)
                    crop_size = radius * 2
                    
                    profile_crop = profile_region[crop_y:crop_y+crop_size, crop_x:crop_x+crop_size]
                    
                    os.makedirs("uploads/whatsapp/profiles", exist_ok=True)
                    profile_pic_path = f"uploads/whatsapp/profiles/{phone}.jpg"
                    cv2.imwrite(profile_pic_path, profile_crop)
                    logger.info(f"[WhatsAppScraper] ✅ Profile picture extracted: {profile_pic_path}")
                else:
                    logger.warning(f"[WhatsAppScraper] ⚠️ No circular profile picture detected, using region")
                    os.makedirs("uploads/whatsapp/profiles", exist_ok=True)
                    profile_pic_path = f"uploads/whatsapp/profiles/{phone}.jpg"
                    cv2.imwrite(profile_pic_path, profile_region)
                    logger.info(f"[WhatsAppScraper] ⚠️ Saved profile region as fallback")
                    
            except Exception as e:
                logger.error(f"[WhatsAppScraper] ❌ Profile picture extraction failed: {e}")
            
            # Crop right drawer panel
            drawer_left = int(width * 0.67)
            drawer_img = img[0:height, drawer_left:width]

            logger.info(f"[WhatsAppScraper] 🔤 Initializing EasyOCR reader...")
            if not hasattr(self, '_ocr_reader'):
                import easyocr
                self._ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
                logger.info(f"[WhatsAppScraper] ✓ EasyOCR reader initialized")
            
            logger.info(f"[WhatsAppScraper] 🔍 Running OCR on drawer region only...")
            results = self._ocr_reader.readtext(drawer_img, detail=1, paragraph=False)
            logger.info(f"[WhatsAppScraper] 📊 OCR found {len(results)} text elements in drawer region")
            
            results_sorted = sorted(results, key=lambda x: x[0][0][1])
            text_lines = []
            for idx, (bbox, text, confidence) in enumerate(results_sorted):
                text_clean = text.strip()
                y_position = bbox[0][1]
                x_position = bbox[0][0]
                if text_clean and len(text_clean) >= 2 and confidence > 0.2:
                    text_lines.append({
                        'text': text_clean,
                        'y': y_position,
                        'x': x_position,
                        'confidence': confidence
                    })
                    logger.debug(f"[WhatsAppScraper] OCR[{idx}]: y={y_position:.0f}, x={x_position:.0f}, conf={confidence:.2f}, text='{text_clean}'")

            # Name extraction
            name_candidates = []
            for line in text_lines:
                y = line['y']
                text = line['text']
                conf = line['confidence']
                text_lower = text.lower()
                # Exclude phone number, known labels, and 'add' symbol
                if 50 <= y <= 350 and (text_lower not in ['contact info', 'about', 'add', 'media', 'mute', 'starred', 'disappearing messages']):
                    if not text.startswith('+') and not text.replace(' ', '').isdigit() \
                        and len(text) >= 3 and len(text) <= 50 and conf > 0.3:
                        name_candidates.append(line)
            # If no valid name or detected 'Add', set blank
            if name_candidates:
                candidate = name_candidates[0]['text']
                if candidate.lower() == 'add':
                    name = ''
                else:
                    name = candidate
            else:
                name = ''

            # About extraction (between 'About' and 'Media, links and docs')
            about = ''
            about_start_idx, about_end_idx = None, None
            for idx, line in enumerate(text_lines):
                if 'about' in line['text'].lower():
                    about_start_idx = idx
                if 'media' in line['text'].lower() and 'links' in line['text'].lower() and 'docs' in line['text'].lower():
                    if about_start_idx is not None:
                        about_end_idx = idx
                        break

            if about_start_idx is not None and about_end_idx is not None:
                bio_parts = [l['text'] for l in text_lines[about_start_idx + 1 : about_end_idx] if l['text'].strip()]
                about = ' '.join(bio_parts).strip()
            else:
                about = ''

            # If about section contains WhatsApp labels and no user text, set to blank
            unwanted_labels = ['starred messages', 'mute notifications', 'disappearing messages', 'advanced chat privacy', 'encryption']
            for label in unwanted_labels:
                if about.lower() == label:
                    about = ''
            # Additional fallback for empty bio (no user bio text between about and media)
            if not about or any(label in about.lower() for label in unwanted_labels):
                about = ''

            logger.info(f"[WhatsAppScraper] 📊 OCR Extraction Summary: name={'✓' if name else '✗'}, about={'✓' if about else '✗'}, photo={'✓' if profile_pic_path else '✗'}")
            return name, about, profile_pic_path

        except Exception as e:
            logger.error(f"[WhatsAppScraper] ❌ Screenshot extraction failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None, None, None

    
    async def _try_extract_profile_drawer(self, clean_number: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Open CONTACT's profile drawer (NOT our own profile) using ROBUST automation.
        
        CRITICAL: This opens the NEW CHAT's header to view the CONTACT's profile info.
        We're already on web.whatsapp.com/send?phone=NUMBER which shows the contact's chat.
        Clicking the header opens THEIR profile drawer with THEIR name, bio, and photo.
        
        Returns:
            Tuple[name, about, profile_picture]: Contact's name, bio/about, and profile picture path
        
        Implements multiple fallback strategies for maximum reliability:
        1. header[data-testid="conversation-header"] - Most stable selector
        2. header[role="button"] span[dir="auto"] - Name-based click
        3. header picture img[src*="whatsapp.net"] - Profile pic click
        4. JavaScript click bypass - Handles overlays/animations
        5. Generic header click - Last resort fallback
        """
        about = None
        photo_path = None
        
        try:
            logger.info("[WhatsAppScraper] Opening CONTACT's profile drawer for number: %s", clean_number)
            logger.info("[WhatsAppScraper] Current URL: %s", self.page.url if self.page else "No page")
            
            clicked = False
            
            # STRATEGY 1: Primary selector - data-testid (most stable)
            try:
                logger.info("[WhatsAppScraper] Strategy 1: Waiting for conversation-header data-testid...")
                await self.page.wait_for_selector('header[data-testid="conversation-header"]', timeout=10000, state='visible')
                
                # CRITICAL: Verify this is the CHAT header, not sidebar
                # Chat header is on the right side of the screen (x > 400)
                header_box = await self.page.locator('header[data-testid="conversation-header"]').bounding_box()
                if header_box and header_box['x'] > 400:
                    logger.info(f"[WhatsAppScraper] ✓ Chat header confirmed (x={header_box['x']}, should be > 400)")
                    await asyncio.sleep(1.0)  # Wait before clicking
                    await self.page.click('header[data-testid="conversation-header"]')
                    clicked = True
                    logger.info("[WhatsAppScraper] ✓✓ Strategy 1 SUCCESS: Clicked via data-testid")
                else:
                    logger.warning(f"[WhatsAppScraper] Header found but position wrong (x={header_box['x'] if header_box else 'none'})")
            except Exception as e:
                logger.debug(f"[WhatsAppScraper] Strategy 1 failed: {e}")
            
            # STRATEGY 2: Click name span in header (when contact name is visible)
            if not clicked:
                try:
                    logger.info("[WhatsAppScraper] Strategy 2: Trying role='button' span...")
                    await self.page.click('header[role="button"] span[dir="auto"]', timeout=5000)
                    clicked = True
                    logger.info("[WhatsAppScraper] ✓✓ Strategy 2 SUCCESS: Clicked via role button span")
                except Exception as e:
                    logger.debug(f"[WhatsAppScraper] Strategy 2 failed: {e}")
            
            # STRATEGY 3: Click profile picture (works when no name shown)
            if not clicked:
                try:
                    logger.info("[WhatsAppScraper] Strategy 3: Trying profile picture...")
                    await self.page.click('header picture img[src*="whatsapp.net"]', timeout=5000)
                    clicked = True
                    logger.info("[WhatsAppScraper] ✓✓ Strategy 3 SUCCESS: Clicked profile picture")
                except Exception as e:
                    logger.debug(f"[WhatsAppScraper] Strategy 3 failed: {e}")
            
            # STRATEGY 4: JavaScript click bypass (handles overlays/animations)
            if not clicked:
                try:
                    logger.info("[WhatsAppScraper] Strategy 4: JS click bypass...")
                    js_result = await self.page.evaluate("""
                        () => {
                            const header = document.querySelector('header[data-testid="conversation-header"]')
                                        || document.querySelector('header[role="button"]')
                                        || document.querySelector('header[class*="x1rg5ohu"]');
                            if (header) {
                                header.click();
                                return 'clicked';
                            }
                            return 'not_found';
                        }
                    """)
                    if js_result == 'clicked':
                        clicked = True
                        logger.info("[WhatsAppScraper] ✓✓ Strategy 4 SUCCESS: JS click bypass")
                    else:
                        logger.warning(f"[WhatsAppScraper] Strategy 4: Header not found via JS")
                except Exception as e:
                    logger.debug(f"[WhatsAppScraper] Strategy 4 failed: {e}")
            
            # STRATEGY 5: Advanced fallback - any clickable header element
            if not clicked:
                try:
                    logger.info("[WhatsAppScraper] Strategy 5: Advanced fallback - any header...")
                    # First, take a debug screenshot to see what's on the page
                    try:
                        debug_ss = f"reports/whatsapp/before_strategy5_{clean_number}.png"
                        await self.page.screenshot(path=debug_ss)
                        logger.info(f"[WhatsAppScraper] Debug screenshot before Strategy 5: {debug_ss}")
                    except Exception:
                        pass
                    
                    # Try clicking any header element that's visible and on the right side
                    headers = await self.page.query_selector_all('header')
                    logger.info(f"[WhatsAppScraper] Found {len(headers)} header elements on page")
                    
                    for idx, header in enumerate(headers):
                        try:
                            box = await header.bounding_box()
                            if box:
                                logger.info(f"[WhatsAppScraper] Header {idx+1}: x={box['x']:.0f}, y={box['y']:.0f}, width={box['width']:.0f}, height={box['height']:.0f}")
                                if box['x'] > 300:  # Right side of screen
                                    await header.click()
                                    clicked = True
                                    logger.info(f"[WhatsAppScraper] ✓✓ Strategy 5 SUCCESS: Clicked header {idx+1} at x={box['x']:.0f}")
                                    break
                        except Exception as e:
                            logger.debug(f"[WhatsAppScraper] Header {idx+1} click failed: {e}")
                            continue
                    
                    if not clicked:
                        logger.warning(f"[WhatsAppScraper] No headers found on right side of screen (x > 300)")
                        
                except Exception as e:
                    logger.debug(f"[WhatsAppScraper] Strategy 5 failed: {e}")
            
            if not clicked:
                logger.error("[WhatsAppScraper] ❌ ALL STRATEGIES FAILED - Cannot open profile drawer!")
                # Debug: save screenshot
                try:
                    screenshot_path = f"reports/failed_drawer_open_{clean_number}.png"
                    await self.page.screenshot(path=screenshot_path)
                    logger.error(f"[WhatsAppScraper] Debug screenshot saved: {screenshot_path}")
                except Exception:
                    pass
                return None, None, None
            
            # CRITICAL: Wait for profile drawer to appear and be fully rendered
            # WhatsApp takes 2-4 seconds to load all profile data
            logger.info("[WhatsAppScraper] Waiting for profile drawer to fully load...")
            await asyncio.sleep(5.0)  # Increased from 2.5 to 3.0 seconds
            
            drawer_found = False
            try:
                # WhatsApp's profile drawer has aria-label="Contact info"
                await self.page.wait_for_selector('div[aria-label="Contact info"], div[data-testid="drawer-right"]', timeout=15000, state='visible')
                drawer_found = True
                logger.info("[WhatsAppScraper] ✓✓✓ Profile drawer opened and verified!")
                
                # ADDITIONAL WAIT: Let profile image and data fully render
                await asyncio.sleep(3.0)
                logger.info("[WhatsAppScraper] Profile data fully loaded")
                
            except Exception as e:
                logger.warning(f"[WhatsAppScraper] Profile drawer verification failed: {e}")
                # Try alternate verification
                try:
                    # Check if drawer has appeared by looking for common drawer elements
                    drawer_check = await self.page.evaluate("""
                        () => {
                            const drawer = document.querySelector('[data-testid="drawer-right"]')
                                        || document.querySelector('section[aria-label]');
                            return drawer ? 'found' : 'not_found';
                        }
                    """)
                    if drawer_check == 'found':
                        drawer_found = True
                        logger.info("[WhatsAppScraper] ✓ Profile drawer found via JS check")
                except Exception:
                    pass
            
            if not drawer_found:
                logger.error("[WhatsAppScraper] ❌ Profile drawer did not open! Screenshot saved for debug.")
                try:
                    await self.page.screenshot(path=f"reports/drawer_not_opened_{clean_number}.png")
                except Exception:
                    pass
            
            # ============================================================================
            # CRITICAL VERIFICATION: Ensure we're viewing CONTACT's profile (not our own!)
            # ============================================================================
            # Since we navigated to web.whatsapp.com/send?phone=NUMBER, clicking the header
            # SHOULD open the contact's profile. But we need to verify this actually happened.
            try:
                logger.info(f"[WhatsAppScraper] 🔍 VERIFICATION: Checking if drawer shows CONTACT {clean_number} (not our own profile)...")
                
                phone_in_drawer = await self.page.evaluate(r"""
                    () => {
                        // Strategy 1: Look for phone number in header/title area
                        const titleElements = document.querySelectorAll('div[data-testid="drawer-right"] h2, div[data-testid="drawer-right"] [role="heading"]');
                        for (const el of titleElements) {
                            const text = el.textContent || '';
                            console.log('Checking title:', text);
                            // Match phone patterns like "+91 89761 86404"
                            if (text.match(/[+\d\s()-]{10,}/)) {
                                return text.trim();
                            }
                        }
                        
                        // Strategy 2: Look in all spans/divs in drawer
                        const allElements = document.querySelectorAll('div[data-testid="drawer-right"] span, div[data-testid="drawer-right"] div');
                        for (const el of allElements) {
                            const text = el.textContent || '';
                            // Only match if it looks like a phone number (starts with + or has many digits)
                            if (text.match(/^\+\d{1,3}\s?\d{4,5}\s?\d{4,6}$/) || text.match(/^\d{10,}$/)) {
                                console.log('Found phone in drawer:', text);
                                return text.trim();
                            }
                        }
                        
                        // Strategy 3: Check section headers
                        const sections = document.querySelectorAll('section span');
                        for (const el of sections) {
                            const text = el.textContent || '';
                            if (text.match(/[+\d\s()-]{10,}/) && !text.includes('@')) {
                                console.log('Found phone in section:', text);
                                return text.trim();
                            }
                        }
                        
                        console.log('No phone found in drawer');
                        return null;
                    }
                """)
                
                verification_passed = False
                
                if phone_in_drawer:
                    logger.info(f"[WhatsAppScraper] 📞 Phone found in drawer: '{phone_in_drawer}' | Expected: '{clean_number}'")
                    
                    # Extract digits only for comparison (ignores country codes, formatting)
                    clean_drawer = "".join([c for c in str(phone_in_drawer) if c.isdigit()])
                    
                    # More lenient matching - just check if last 10 digits match
                    # This handles cases like "+91 89761 86404" vs "918976186404"
                    drawer_last_10 = clean_drawer[-10:] if len(clean_drawer) >= 10 else clean_drawer
                    target_last_10 = clean_number[-10:] if len(clean_number) >= 10 else clean_number
                    
                    is_match = (drawer_last_10 == target_last_10) or (clean_number in clean_drawer) or (clean_drawer in clean_number)
                    
                    logger.info(f"[WhatsAppScraper] Comparing: drawer='{clean_drawer}' (last10={drawer_last_10}) vs target='{clean_number}' (last10={target_last_10})")
                    
                    if is_match:
                        logger.info(f"[WhatsAppScraper] ✅✅ VERIFICATION PASSED: Viewing CONTACT {clean_number}")
                        verification_passed = True
                    else:
                        logger.error(f"[WhatsAppScraper] ❌❌ VERIFICATION FAILED!")
                        logger.error(f"[WhatsAppScraper] Expected contact: {clean_number}")
                        logger.error(f"[WhatsAppScraper] Drawer shows: {phone_in_drawer} (cleaned: {clean_drawer})")
                        logger.error(f"[WhatsAppScraper] ⚠️ This is YOUR OWN profile or WRONG contact!")
                        logger.error(f"[WhatsAppScraper] STOPPING extraction to prevent incorrect data")
                        
                        # Take debug screenshot
                        try:
                            await self.page.screenshot(path=f"reports/wrong_profile_{clean_number}.png")
                            logger.error(f"[WhatsAppScraper] Debug screenshot: reports/wrong_profile_{clean_number}.png")
                        except:
                            pass
                        
                        # CRITICAL: Return immediately without extracting data
                        return None, None, None
                else:
                    logger.warning(f"[WhatsAppScraper] ⚠️ Could not find phone number in drawer for verification")
                    logger.warning(f"[WhatsAppScraper] This likely means we're viewing YOUR profile instead of the contact's")
                    logger.warning(f"[WhatsAppScraper] STOPPING extraction to prevent incorrect data")
                    
                    # Take screenshot for debugging
                    try:
                        await self.page.screenshot(path=f"reports/no_phone_in_drawer_{clean_number}.png")
                        logger.warning(f"[WhatsAppScraper] Debug screenshot: reports/no_phone_in_drawer_{clean_number}.png")
                    except:
                        pass
                    
                    # CRITICAL: Return immediately without extracting data
                    return None, None, None
                    
            except Exception as e:
                logger.warning(f"[WhatsAppScraper] Phone verification failed with error: {e}")
                logger.warning(f"[WhatsAppScraper] Cannot confirm profile ownership - STOPPING extraction")
                return None, None, None
            
            # ============================================================================
            # ONLY PROCEED WITH EXTRACTION IF VERIFICATION PASSED
            # ============================================================================
            if not verification_passed:
                logger.error(f"[WhatsAppScraper] ❌ Verification did not pass - aborting extraction")
                return None, None, None
            
            logger.info(f"[WhatsAppScraper] ✅ Verification passed - proceeding with data extraction from CONTACT's drawer")
            
            # DEBUG: Capture screenshot of opened drawer
            screenshot_path = None
            try:
                screenshot_path = f"reports/whatsapp/drawer_opened_{clean_number}.png"
                await self.page.screenshot(path=screenshot_path, full_page=True)
                logger.info(f"[WhatsAppScraper] 📸 Screenshot saved: {screenshot_path}")
            except Exception as e:
                logger.error(f"[WhatsAppScraper] Screenshot failed: {e}")
            
            # ============================================================================
            # PRIMARY METHOD: Extract data using DOM (JavaScript) - MOST RELIABLE
            # ============================================================================
            name = None
            about = None
            photo_path = None
            
            logger.info(f"[WhatsAppScraper] 🎯 PRIMARY: Attempting DOM extraction...")
            extracted_name, extracted_about = await self._extract_name_about_from_drawer_dom(clean_number)
            
            if extracted_name:
                name = extracted_name
                logger.info(f"[WhatsAppScraper] ✅ DOM extracted name: '{name}'")
            
            if extracted_about:
                about = extracted_about
                logger.info(f"[WhatsAppScraper] ✅ DOM extracted about: '{about[:60]}...'")
            
            # ============================================================================
            # FALLBACK METHOD: Use OCR from screenshot if DOM extraction failed
            # ============================================================================
            if (not name or not about) and screenshot_path and os.path.exists(screenshot_path):
                logger.info(f"[WhatsAppScraper] 🔄 FALLBACK: DOM incomplete, trying OCR extraction...")
                ocr_name, ocr_about, ocr_photo = self._extract_from_drawer_screenshot(screenshot_path, clean_number)
                
                if not name and ocr_name:
                    name = ocr_name
                    logger.info(f"[WhatsAppScraper] ✅ OCR extracted name: '{name}'")
                
                if not about and ocr_about:
                    about = ocr_about
                    logger.info(f"[WhatsAppScraper] ✅ OCR extracted about: '{about[:60]}...'")
                
                if not photo_path and ocr_photo:
                    photo_path = ocr_photo
                    logger.info(f"[WhatsAppScraper] ✅ OCR extracted profile pic: '{photo_path}'")
            
            # ============================================================================
            # Extract Profile Picture using existing methods
            # ============================================================================
            if not photo_path:
                logger.info(f"[WhatsAppScraper] 🖼️ Extracting profile picture from drawer...")
                photo_path = await self._extract_profile_picture(clean_number)
            
            # ============================================================================
            # FINAL LOGGING
            # ============================================================================
            logger.info(f"[WhatsAppScraper] 📊 FINAL EXTRACTION RESULTS:")
            logger.info(f"[WhatsAppScraper]   Name: {'✓ ' + name if name else '✗ Not found'}")
            logger.info(f"[WhatsAppScraper]   About: {'✓ ' + about[:50] + '...' if about else '✗ Not found'}")
            logger.info(f"[WhatsAppScraper]   Photo: {'✓ ' + photo_path if photo_path else '✗ Not found'}")
            
            return name, about, photo_path
        
        except Exception as e:
            logger.error(f"[WhatsAppScraper] Profile drawer extraction failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None, None, None
    
    async def _extract_profile_picture(self, clean_number: str) -> Optional[str]:
        """
        Extract profile picture from the opened drawer.
        
        Args:
            clean_number: Phone number for saving the profile picture
            
        Returns:
            Path to saved profile picture or None
        """
        try:
            logger.info(f"[WhatsAppScraper] 🖼️ Extracting profile picture for {clean_number}")
            
            # Use JavaScript to find the profile picture URL in the drawer
            profile_pic_url = await self.page.evaluate("""
                () => {
                    const drawer = document.querySelector('div[data-testid="drawer-right"]');
                    if (!drawer) return null;
                    
                    // Find images in drawer
                    const images = drawer.querySelectorAll('img');
                    for (let img of images) {
                        const src = img.src || '';
                        // Look for WhatsApp profile picture URLs
                        if (src.includes('pps.whatsapp.net') || src.includes('mmg.whatsapp.net') || 
                            src.startsWith('blob:') || src.startsWith('data:image')) {
                            // Skip small icons
                            const width = img.naturalWidth || img.width || 0;
                            if (width >= 50) {
                                return src;
                            }
                        }
                    }
                    return null;
                }
            """)
            
            if profile_pic_url:
                logger.info(f"[WhatsAppScraper] Found profile picture URL: {profile_pic_url[:80]}...")
                # Download and save the profile picture
                saved_path = await self._download_image(profile_pic_url, clean_number)
                if saved_path:
                    logger.info(f"[WhatsAppScraper] ✅ Profile picture saved: {saved_path}")
                    return saved_path
            else:
                logger.warning(f"[WhatsAppScraper] ⚠️ No profile picture URL found")
            
            return None
            
        except Exception as e:
            logger.error(f"[WhatsAppScraper] Profile picture extraction failed: {e}")
            return None

    async def close(self):
        """Close browser and save session state."""
        try:
            logger.info("[WhatsAppScraper] Closing - saving session")
            if self.context:
                await self._save_session()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("[WhatsAppScraper] Closed cleanly")
        except Exception as e:
            logger.exception("[WhatsAppScraper] Error during close: %s", e)
        finally:
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
            self.is_initialized = False


# singleton instance helpers
_scraper_instance: Optional[WhatsAppScraper] = None
_scraper_lock = asyncio.Lock()


async def get_scraper_instance() -> WhatsAppScraper:
    global _scraper_instance
    async with _scraper_lock:
        if _scraper_instance is None:
            _scraper_instance = WhatsAppScraper()
        return _scraper_instance


async def close_scraper_instance():
    global _scraper_instance
    async with _scraper_lock:
        if _scraper_instance:
            await _scraper_instance.close()
            _scraper_instance = None

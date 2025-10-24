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
        FULLY AUTOMATED: Navigate to chat link and extract all data automatically.
        This is the main method for fully automated scraping.
        User provides only phone number, system does everything.
        
        Returns complete profile data ready for frontend display and report generation.
        """
        logger.info("[WhatsAppScraper] AUTO-NAVIGATE: Starting fully automated extraction for %s", phone_number)
        
        result = {
            "phone_number": phone_number,
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
            
            # Clean phone number
            clean = "".join([c for c in phone_number if c.isdigit()])
            if not clean:
                result["error"] = "Invalid phone number format"
                result["status"] = "failed"
                return result
            
            # Navigate to direct WhatsApp chat link
            url = f"https://web.whatsapp.com/send?phone={clean}"
            logger.info("[WhatsAppScraper] AUTO-NAVIGATE: Opening %s", url)
            
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            logger.info("[WhatsAppScraper] AUTO-NAVIGATE: Page loaded, waiting for chat to render...")
            
            # CRITICAL: For new/unknown numbers, WhatsApp needs time to load chat UI
            # Poll for header readiness (WhatsApp shows minimal UI first, then full header)
            header_ready = False
            for attempt in range(5):
                try:
                    # Check if header with name OR profile pic is loaded
                    header = await self.page.query_selector('header span[title], header img[src*="whatsapp.net"]')
                    if header:
                        header_ready = True
                        logger.info(f"[WhatsAppScraper] AUTO-NAVIGATE: ✓ Header ready after {attempt + 1} attempts")
                        break
                except Exception:
                    pass
                await asyncio.sleep(2.0)
            
            if not header_ready:
                logger.warning("[WhatsAppScraper] AUTO-NAVIGATE: Header not detected after polling, continuing anyway")
            
            # Final wait for all elements to be interactive
            await asyncio.sleep(2.0)
            
            # Check if number is invalid
            try:
                invalid_el = await self.page.query_selector('div[data-testid="invalid-number"]')
                if invalid_el:
                    result["error"] = "Phone number not on WhatsApp"
                    result["status"] = "failed"
                    logger.warning("[WhatsAppScraper] AUTO-NAVIGATE: %s not on WhatsApp", phone_number)
                    return result
            except Exception:
                pass
            
            # Extract data using all available methods
            logger.info("[WhatsAppScraper] AUTO-NAVIGATE: Extracting profile data...")
            
            # Method 1: Try standard selectors
            name = await self._try_extract_name()
            if name:
                result["display_name"] = name
                result["is_available"] = True
            
            # Method 2: Try opening profile drawer for more data
            about, photo = await self._try_extract_profile_drawer(clean)
            if about:
                result["about"] = about
            if photo:
                result["profile_picture"] = photo
            
            # Method 3: If still no data, use JS extraction
            if not result["display_name"]:
                logger.info("[WhatsAppScraper] AUTO-NAVIGATE: Using JS extraction fallback...")
                js_data = await self._extract_profile_from_raw_data(clean)
                if js_data:
                    result.update(js_data)
                    result["method"] = "auto_navigate_js_fallback"
            
            # Set final status
            if result["display_name"] or result["is_available"]:
                result["status"] = "success"
            else:
                result["status"] = "partial"
                result["error"] = "Could not extract profile data"
            
            logger.info("[WhatsAppScraper] AUTO-NAVIGATE: Extraction complete - %s", result["status"])
            return result
            
        except Exception as e:
            logger.exception("[WhatsAppScraper] AUTO-NAVIGATE: Error: %s", e)
            result["error"] = str(e)
            result["status"] = "failed"
            return result
    
    async def _try_extract_name(self) -> Optional[str]:
        """Try multiple selectors to get display name - FILTER OUT placeholder text."""
        name_selectors = [
            'header span[data-testid="conversation-info-header-chat-title"]',
            'header span[title]',
            'header [data-testid="contact-name"]',
            'header span[dir="auto"]',
        ]
        
        # Placeholder texts to ignore (these are NOT real names)
        invalid_names = [
            'click here for contact info',
            'click here',
            'tap here',
            'loading',
            '',
        ]
        
        for sel in name_selectors:
            try:
                el = await self.page.query_selector(sel)
                if el:
                    name = (await el.get_attribute("title")) or (await el.text_content())
                    if name and name.strip():
                        name_clean = name.strip().lower()
                        # Check if it's a valid name (not a placeholder)
                        if name_clean not in invalid_names and len(name_clean) > 2:
                            logger.info("[WhatsAppScraper] ✓ Found valid name via selector %s: %s", sel, name.strip())
                            return name.strip()
                        else:
                            logger.debug(f"[WhatsAppScraper] Ignoring placeholder text: {name.strip()}")
            except Exception:
                continue
        return None
    
    async def _try_extract_profile_drawer(self, clean_number: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Open contact's profile drawer using ROBUST DOM selector chain.
        Implements senior-level engineering approach with multiple fallback strategies.
        
        Selector Priority Chain:
        1. header[data-testid="conversation-header"] - Most stable
        2. header[role="button"] span[dir="auto"] - Name-based
        3. header picture img[src*="whatsapp.net"] - Profile pic
        4. JavaScript click bypass - Animation/overlay workaround
        5. Retry with progressive waits - A/B test variations
        """
        about = None
        photo_path = None
        
        try:
            logger.info("[WhatsAppScraper] Opening profile drawer using robust selector chain for: %s", clean_number)
            
            clicked = False
            
            # STRATEGY 1: Primary selector - data-testid (most stable)
            try:
                logger.info("[WhatsAppScraper] Strategy 1: Waiting for conversation-header data-testid...")
                await self.page.wait_for_selector('header[data-testid="conversation-header"]', timeout=10000, state='visible')
                await self.page.click('header[data-testid="conversation-header"]')
                clicked = True
                logger.info("[WhatsAppScraper] ✓✓ Strategy 1 SUCCESS: Clicked via data-testid")
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
                    # Try clicking any header element that's visible and on the right side
                    headers = await self.page.query_selector_all('header')
                    for header in headers:
                        try:
                            box = await header.bounding_box()
                            if box and box['x'] > 300:  # Right side of screen
                                await header.click()
                                clicked = True
                                logger.info("[WhatsAppScraper] ✓✓ Strategy 5 SUCCESS: Clicked generic header")
                                break
                        except Exception:
                            continue
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
                return about, photo_path
            
            # Wait for profile drawer to appear (using recommended selector)
            await asyncio.sleep(2.5)
            
            drawer_found = False
            try:
                # WhatsApp's profile drawer has aria-label="Contact info"
                await self.page.wait_for_selector('div[aria-label="Contact info"], div[data-testid="drawer-right"]', timeout=10000, state='visible')
                drawer_found = True
                logger.info("[WhatsAppScraper] ✓✓✓ Profile drawer opened and verified!")
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
            
            # VERIFICATION: Check if we opened the correct profile (not our own!)
            # Extract the phone number from the drawer to verify it matches what we're scraping
            try:
                phone_in_drawer = await self.page.evaluate(r"""
                    () => {
                        // Look for phone number in the drawer
                        const phoneElements = document.querySelectorAll('div[data-testid="drawer-right"] span, section span');
                        for (const el of phoneElements) {
                            const text = el.textContent || '';
                            // Match phone number patterns
                            if (text.match(/[+\d\s()-]{8,}/)) {
                                return text.trim();
                            }
                        }
                        return null;
                    }
                """)
                if phone_in_drawer:
                    logger.info(f"[WhatsAppScraper] 📞 Phone in drawer: {phone_in_drawer} (Expected: {clean_number})")
                    # Basic validation - check if the number matches (ignoring formatting)
                    clean_drawer = "".join([c for c in str(phone_in_drawer) if c.isdigit()])
                    if clean_drawer and clean_number not in clean_drawer and clean_drawer not in clean_number:
                        logger.error(f"[WhatsAppScraper] ❌❌ WRONG PROFILE! Drawer shows {phone_in_drawer} but expected {clean_number}")
                        logger.error("[WhatsAppScraper] This might be YOUR profile instead of the contact's!")
                else:
                    logger.warning("[WhatsAppScraper] Could not find phone number in drawer for verification")
            except Exception as e:
                logger.warning(f"[WhatsAppScraper] Phone verification failed: {e}")
            
            # Extract profile name (from drawer)
            name = None
            name_selectors = [
                'div[data-testid="drawer-right"] h2',
                'div[data-testid="drawer-right"] span[dir="auto"][title]',
                'section h2 span',
                'div[data-testid="contact-info-drawer"] h2',
            ]
            for sel in name_selectors:
                try:
                    el = await self.page.query_selector(sel)
                    if el:
                        # Try title attribute first (most reliable)
                        name = await el.get_attribute("title")
                        if not name:
                            name = await el.text_content()
                        if name and name.strip() and len(name.strip()) > 0:
                            logger.info(f"[WhatsAppScraper] ✓✓ Found CONTACT name: '{name.strip()}'")
                            break
                except Exception:
                    continue
            
            # Extract about/bio/status
            about_selectors = [
                'div[data-testid="about-drawer"] span[dir="auto"]',
                'span[data-testid="status-v3-text"]',
                'div.about-section span[dir="auto"]',
                'section div[title]',  # Sometimes about is in title attribute
            ]
            for sel in about_selectors:
                try:
                    el = await self.page.query_selector(sel)
                    if el:
                        # Try text content first
                        text = await el.text_content()
                        if not text or not text.strip():
                            # Try title attribute
                            text = await el.get_attribute("title")
                        if text and text.strip() and text.strip().lower() not in ['', 'about', 'bio']:
                            about = text.strip()
                            logger.info(f"[WhatsAppScraper] ✓ Found about/bio: {about[:50]}...")
                            break
                except Exception as e:
                    logger.debug(f"[WhatsAppScraper] About selector {sel} failed: {e}")
                    continue
            
            # Extract profile photo - UPDATED to match your HTML structure
            # From your HTML: <img alt="" draggable="false" class="x1n2onr6 x1lliihq..." src="https://media-del2-2.cdn.whatsapp.net/v/t61.24694-24/...">
            img_selectors = [
                # High resolution profile photo from drawer
                'div[data-testid="drawer-right"] img[src*="whatsapp.net"]',
                'div[data-testid="contact-info-drawer"] img[src*="whatsapp.net"]',
                # Profile image with specific classes (from your HTML)
                'img.x1n2onr6.x1lliihq.xh8yej3[src*="whatsapp.net"]',
                'img[alt=""][src*="whatsapp.net"]',
                # Generic fallbacks
                'img[alt="Profile picture"]',
                'img[data-testid="profile-picture"]',
                'div[data-testid="image-view"] img',
                'section img[src*="cdn.whatsapp"]',
            ]
            
            for sel in img_selectors:
                try:
                    el = await self.page.query_selector(sel)
                    if el:
                        src = await el.get_attribute("src")
                        logger.info(f"[WhatsAppScraper] Found image with selector {sel}: {src[:100] if src else 'None'}...")
                        
                        if src and "default-user" not in src.lower() and "blank" not in src.lower():
                            # Check if it's a real WhatsApp CDN image
                            if "whatsapp.net" in src or "cdn" in src:
                                logger.info(f"[WhatsAppScraper] ✓ Found WhatsApp CDN profile photo")
                                photo_path = await self._download_image(src, clean_number)
                                if photo_path:
                                    logger.info(f"[WhatsAppScraper] ✓✓ Saved profile photo: {photo_path}")
                                    break
                            # Handle base64 images
                            elif src.startswith("data:image"):
                                try:
                                    b64 = src.split(",", 1)[1]
                                    data = base64.b64decode(b64)
                                    photo_path = self._save_binary_profile_picture(data, clean_number)
                                    logger.info(f"[WhatsAppScraper] ✓ Saved base64 profile photo: {photo_path}")
                                    break
                                except Exception as e:
                                    logger.warning(f"[WhatsAppScraper] Base64 decode failed: {e}")
                            # Handle blob URLs
                            elif src.startswith("blob:"):
                                logger.warning("[WhatsAppScraper] Blob URL detected, trying screenshot method")
                                # For blob URLs, we need to screenshot the image element
                                try:
                                    downloads = Path("uploads") / "whatsapp" / "profiles"
                                    downloads.mkdir(parents=True, exist_ok=True)
                                    filename = f"{clean_number}.jpg"
                                    path = downloads / filename
                                    await el.screenshot(path=str(path))
                                    photo_path = str(path.resolve())
                                    logger.info(f"[WhatsAppScraper] ✓ Screenshot saved: {photo_path}")
                                    break
                                except Exception as e:
                                    logger.warning(f"[WhatsAppScraper] Screenshot failed: {e}")
                except Exception as e:
                    logger.debug(f"[WhatsAppScraper] Image selector {sel} failed: {e}")
                    continue
            
            # Additional: Try JavaScript extraction for profile image if selectors failed
            if not photo_path:
                logger.info("[WhatsAppScraper] Trying JS extraction for profile image...")
                try:
                    js_img_src = await self.page.evaluate("""
                        () => {
                            // Find any image with WhatsApp CDN URL
                            const imgs = document.querySelectorAll('img');
                            for (const img of imgs) {
                                if (img.src && img.src.includes('whatsapp.net')) {
                                    return img.src;
                                }
                            }
                            return null;
                        }
                    """)
                    if js_img_src:
                        logger.info(f"[WhatsAppScraper] JS found image: {js_img_src[:100]}...")
                        photo_path = await self._download_image(js_img_src, clean_number)
                        if photo_path:
                            logger.info(f"[WhatsAppScraper] ✓ JS extraction saved photo: {photo_path}")
                except Exception as e:
                    logger.warning(f"[WhatsAppScraper] JS image extraction failed: {e}")
            
            # Close drawer by pressing ESC or clicking close button
            try:
                # Try ESC key first (most reliable)
                await self.page.keyboard.press("Escape")
                await asyncio.sleep(0.8)
                logger.info("[WhatsAppScraper] Closed drawer with ESC key")
            except Exception:
                # Fallback to click close button
                close_selectors = [
                    'button[aria-label="Close"]',
                    'span[data-testid="x-viewer"]',
                    'div[data-testid="drawer-right"] button',
                ]
                for sel in close_selectors:
                    try:
                        el = await self.page.query_selector(sel)
                        if el:
                            await el.click()
                            await asyncio.sleep(0.5)
                            logger.info(f"[WhatsAppScraper] Closed drawer with {sel}")
                            break
                    except Exception:
                        continue
        
        except Exception as e:
            logger.error(f"[WhatsAppScraper] Profile drawer extraction error: {e}", exc_info=True)
        
        return about, photo_path

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

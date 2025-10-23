"""Browser automation engine implementing human-like behavior and resilient posting."""
from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


STATUS_CALLBACK = Callable[[str, str, Optional[float]], None]


class AutomationError(RuntimeError):
    """Raised when automation cannot continue."""


@dataclass
class AutomationConfiguration:
    headless: bool = True
    mobile_user_agents: Optional[list[str]] = None
    implicit_wait: int = 10
    base_url: str = "https://www.example.com"
    platform: str = "generic"


class BrowserAutomationEngine:
    """Encapsulates all browser automation behaviors with stealth and resilience."""

    def __init__(
        self,
        configuration: Optional[Dict[str, str]] = None,
        status_callback: Optional[STATUS_CALLBACK] = None,
    ) -> None:
        conf = configuration or {}
        mobile_agents = conf.get("mobile_user_agents")
        if isinstance(mobile_agents, str):
            try:
                mobile_agents = json.loads(mobile_agents)
            except json.JSONDecodeError:
                mobile_agents = None
        self.configuration = AutomationConfiguration(
            headless=conf.get("headless", "true").lower() != "false",
            mobile_user_agents=mobile_agents,
            implicit_wait=int(conf.get("implicit_wait", 10)),
            base_url=conf.get("base_url", "https://www.example.com"),
            platform=conf.get("platform", "generic"),
        )
        self._status_callback = status_callback
        self.driver: Optional[webdriver.Chrome] = None
        self._action_chain: Optional[ActionChains] = None
        self._viewport = (random.randint(360, 1920), random.randint(640, 1080))

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def _notify(self, message: str, status: str = "info", progress: Optional[float] = None) -> None:
        if self._status_callback:
            self._status_callback(message, status, progress)

    def _random_user_agent(self) -> str:
        candidates = self.configuration.mobile_user_agents or [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/95.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0 Mobile Safari/537.36",
            "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A5341f Safari/604.1",
        ]
        return random.choice(candidates)

    def _build_options(self) -> ChromeOptions:
        options = ChromeOptions()
        chrome_binary = os.getenv("GOOGLE_CHROME_BIN")
        if chrome_binary:
            options.binary_location = chrome_binary
        if self.configuration.headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"--user-agent={self._random_user_agent()}")
        options.add_argument(f"--window-size={self._viewport[0]},{self._viewport[1]}")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--lang=en-US")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        return options

    def _chromedriver_service(self) -> Service:
        driver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
        if not Path(driver_path).exists():
            raise AutomationError("ChromeDriver not found. Ensure build.sh installs the driver")
        service = Service(driver_path)
        service.creationflags = 0
        service.start_error_message = f"Unable to start ChromeDriver at {driver_path}"
        return service

    def setup_browser(self) -> None:
        """Configure an undetectable browser instance."""
        options = self._build_options()
        try:
            service = self._chromedriver_service()
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.implicitly_wait(self.configuration.implicit_wait)
            self._action_chain = ActionChains(self.driver)
            self._notify("Browser ready", "info")
        except WebDriverException as exc:
            raise AutomationError(f"Failed to initialize browser: {exc}") from exc

    # ------------------------------------------------------------------
    # Human behavior simulation
    # ------------------------------------------------------------------
    def random_delay(self) -> float:
        return random.uniform(2.0, 8.0)

    def _random_typing_speed(self) -> float:
        return random.uniform(0.05, 0.2)

    def human_like_interaction(self) -> None:
        if not self.driver:
            raise AutomationError("Browser not initialized")
        self._notify("Simulating human interaction", "info")
        # Random mouse movement across viewport
        width, height = self._viewport
        for _ in range(random.randint(3, 6)):
            x_offset = random.randint(0, width)
            y_offset = random.randint(0, height)
            ActionChains(self.driver).move_by_offset(x_offset, y_offset).pause(random.uniform(0.1, 0.4)).perform()
        time.sleep(self.random_delay() / 4)

    # ------------------------------------------------------------------
    # Platform flows
    # ------------------------------------------------------------------
    def platform_login(self, credentials: Dict[str, str]) -> None:
        if not self.driver:
            raise AutomationError("Browser not initialized")
        self._notify("Performing platform login", "info")
        self.driver.get(self.configuration.base_url)
        username = credentials.get("username")
        password = credentials.get("password")
        if not username or not password:
            raise AutomationError("Credentials missing username/password")

        try:
            user_field = self._discover_element([
                (By.NAME, "email"),
                (By.NAME, "username"),
                (By.CSS_SELECTOR, "input[type='text']"),
            ])
            pass_field = self._discover_element([
                (By.NAME, "pass"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
            ])
            self._type_like_human(user_field, username)
            self._type_like_human(pass_field, password)
            pass_field.send_keys(Keys.RETURN)
            self._notify("Login submitted", "info")
            time.sleep(self.random_delay())
        except NoSuchElementException as exc:
            raise AutomationError("Unable to locate login form") from exc

    def _discover_element(self, selectors: list[tuple[str, str]]):
        if not self.driver:
            raise AutomationError("Browser not initialized")
        last_error: Optional[Exception] = None
        for by, value in selectors:
            try:
                element = self.driver.find_element(by, value)
                if element.is_displayed():
                    return element
            except Exception as exc:  # pylint: disable=broad-except
                last_error = exc
                time.sleep(random.uniform(0.2, 0.8))
        if last_error:
            raise last_error
        raise NoSuchElementException("Element not found for provided selectors")

    def navigate_interface(self, content: "ContentItem") -> None:
        if not self.driver:
            raise AutomationError("Browser not initialized")
        self._notify("Navigating to posting interface", "info")
        navigation_selectors = [
            (By.PARTIAL_LINK_TEXT, "Groups"),
            (By.CSS_SELECTOR, "a[href*='groups']"),
            (By.CSS_SELECTOR, "button[data-testid*='group']"),
        ]
        try:
            nav_element = self._discover_element(navigation_selectors)
            nav_element.click()
            time.sleep(self.random_delay())
        except Exception as exc:  # pylint: disable=broad-except
            raise AutomationError("Failed to navigate to groups") from exc

        search_box = self._discover_element([
            (By.CSS_SELECTOR, "input[placeholder*='Search']"),
            (By.CSS_SELECTOR, "input[type='search']"),
        ])
        self._type_like_human(search_box, content.target_group)
        time.sleep(self.random_delay())

    def submit_content(self, content: "ContentItem") -> None:
        if not self.driver:
            raise AutomationError("Browser not initialized")
        self._notify(f"Preparing content '{content.title}'", "info")
        editor = self._discover_element([
            (By.CSS_SELECTOR, "textarea"),
            (By.CSS_SELECTOR, "div[role='textbox']"),
        ])
        self._type_like_human(editor, content.body)
        time.sleep(random.uniform(1.0, 2.0))
        submit = self._discover_element([
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[contains(., 'Post')]"),
        ])
        submit.click()
        time.sleep(self.random_delay())
        self._notify(f"Content '{content.title}' submitted", "success")

    def recover_from_error(self, error: Exception) -> None:  # pylint: disable=unused-argument
        self._notify("Attempting recovery", "warning")
        time.sleep(self.random_delay())
        if self.driver:
            try:
                self.driver.refresh()
            except WebDriverException:
                self._notify("Browser refresh failed during recovery", "error")

    def capture_debug_artifacts(self, reason: str) -> None:
        if not self.driver:
            return
        ts = int(time.time())
        screenshot_path = Path("debug") / f"screenshot_{ts}.png"
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.driver.save_screenshot(str(screenshot_path))
            self._notify(f"Saved screenshot for debugging: {screenshot_path}", "info")
        except WebDriverException:
            self._notify("Failed to capture screenshot", "error")
        logs_path = Path("debug") / f"console_{ts}.json"
        try:
            logs = self.driver.get_log("browser")
        except Exception:  # pylint: disable=broad-except
            logs = []
        logs_path.write_text(json.dumps({"reason": reason, "logs": logs}, indent=2), encoding="utf-8")

    def shutdown(self) -> None:
        if self.driver:
            try:
                self.driver.quit()
            except WebDriverException:
                self._notify("Browser shutdown encountered an error", "warning")
        self.driver = None
        self._action_chain = None

    # ------------------------------------------------------------------
    # Typing helpers
    # ------------------------------------------------------------------
    def _type_like_human(self, element, text: str) -> None:
        for char in text:
            element.send_keys(char)
            time.sleep(self._random_typing_speed())
        # Random chance to backspace and correct
        if random.random() > 0.7:
            element.send_keys(Keys.BACKSPACE)
            time.sleep(self._random_typing_speed())
            element.send_keys(text[-1] if text else "")


__all__ = ["BrowserAutomationEngine", "AutomationError"]

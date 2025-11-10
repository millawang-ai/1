"""Automate Xiaomi coupon claiming using Playwright."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from playwright.async_api import Browser, Page, async_playwright


@dataclass
class CouponConfig:
    """Configuration for a coupon campaign."""

    url: str
    click_selectors: List[str]
    success_selectors: List[str] = field(default_factory=list)
    start_time: Optional[str] = None
    max_attempts: int = 150
    pause_between_attempts: float = 0.05
    wait_selector: Optional[str] = None
    cookies_path: Optional[Path] = None
    headless: bool = False
    timeout: int = 5000

    @staticmethod
    def from_json(path: Path) -> "CouponConfig":
        data = json.loads(path.read_text(encoding="utf-8"))
        cookies = data.get("cookies_path")
        return CouponConfig(
            url=data["url"],
            click_selectors=data["click_selectors"],
            success_selectors=data.get("success_selectors", []),
            start_time=data.get("start_time"),
            max_attempts=data.get("max_attempts", 150),
            pause_between_attempts=data.get("pause_between_attempts", 0.05),
            wait_selector=data.get("wait_selector"),
            cookies_path=Path(cookies) if cookies else None,
            headless=data.get("headless", False),
            timeout=data.get("timeout", 5000),
        )


async def _load_cookies(page: Page, path: Path) -> None:
    cookies = json.loads(path.read_text(encoding="utf-8"))
    await page.context.add_cookies(cookies)


async def _click_selectors(page: Page, selectors: Iterable[str], timeout: int) -> None:
    for selector in selectors:
        try:
            await page.click(selector, timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            logging.debug("Click on %s failed: %s", selector, exc)


async def _check_success(page: Page, selectors: Iterable[str]) -> bool:
    for selector in selectors:
        try:
            await page.wait_for_selector(selector, timeout=500)
            return True
        except Exception:  # noqa: BLE001
            continue
    return False


async def _claim_coupon(config: CouponConfig) -> None:
    async with async_playwright() as p:
        browser: Browser = await p.chromium.launch(headless=config.headless)
        context = await browser.new_context()
        page: Page = await context.new_page()

        if config.cookies_path:
            await _load_cookies(page, config.cookies_path)

        logging.info("Opening %s", config.url)
        await page.goto(config.url, wait_until="domcontentloaded", timeout=config.timeout)

        if config.wait_selector:
            logging.info("Waiting for selector %s", config.wait_selector)
            await page.wait_for_selector(config.wait_selector, timeout=config.timeout)

        if config.start_time:
            target = datetime.fromisoformat(config.start_time)
            if target.tzinfo is None:
                target = target.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            wait_seconds = (target - now).total_seconds()
            if wait_seconds > 0:
                logging.info("Sleeping %.2f seconds until start", wait_seconds)
                await asyncio.sleep(wait_seconds)

        attempt = 0
        while attempt < config.max_attempts:
            attempt += 1
            logging.debug("Attempt %d", attempt)
            await _click_selectors(page, config.click_selectors, config.timeout)
            if config.success_selectors and await _check_success(page, config.success_selectors):
                logging.info("Coupon claimed successfully!")
                break
            await asyncio.sleep(config.pause_between_attempts)
        else:
            logging.warning("Maximum attempts reached without detecting success selector")

        await browser.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Automate Xiaomi coupon claiming.")
    parser.add_argument(
        "config",
        type=Path,
        help="Path to JSON configuration file."
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(asctime)s %(levelname)s %(message)s")
    config = CouponConfig.from_json(args.config)
    asyncio.run(_claim_coupon(config))


if __name__ == "__main__":
    main()

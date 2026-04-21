from __future__ import annotations

import os

from playwright.sync_api import sync_playwright


BASE_URL = os.environ.get("APP_URL", "http://127.0.0.1:8501")
INVITE_CODE = os.environ.get("APP_INVITE_CODE", "DEMO")
NICKNAME = os.environ.get("APP_NICKNAME", "playwright-smoke")


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1200})
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        page.get_by_label("邀请码").fill(INVITE_CODE)
        page.get_by_label("昵称").fill(NICKNAME)
        page.get_by_role("button", name="进入复习平台").click()
        page.wait_for_load_state("networkidle")

        page.get_by_role("link", name="去刷题").click()
        page.wait_for_load_state("networkidle")

        page.get_by_text("选择你的答案").scroll_into_view_if_needed()
        page.get_by_text("A. 希波克拉底", exact=False).click()
        page.get_by_role("button", name="提交当前答案").click()
        page.wait_for_timeout(800)

        page.get_by_role("link", name="错题本").click()
        page.wait_for_load_state("networkidle")
        with page.expect_download():
            page.get_by_role("button", name="导出当前错题为 DOCX").click()

        page.get_by_role("link", name="进度").click()
        page.wait_for_load_state("networkidle")
        browser.close()


if __name__ == "__main__":
    main()

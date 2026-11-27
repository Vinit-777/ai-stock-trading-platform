"""End-to-end headless UI & live market data tests across all 14 public and authenticated pages."""

import time
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
APP_FILE = str(ROOT / "app.py")


def assert_clean(at: AppTest, label: str) -> None:
    if at.exception:
        msgs = [f"{e.value}\n{e.stack_trace}" for e in at.exception]
        raise AssertionError(f"[{label}] Uncaught Streamlit exceptions:\n" + "\n".join(msgs))
    if at.error:
        raise AssertionError(f"[{label}] Unexpected st.error alerts: {[e.value for e in at.error]}")


def goto_page(at: AppTest, url_or_name: str, timeout: float = 45.0) -> AppTest:
    target = url_or_name.lower()
    for page_hash, info in at._registered_pages.items():
        if info.get("url_pathname", "").lower() == target or info.get("page_name", "").lower() == target:
            at._page_hash = page_hash
            return at.run(timeout=timeout)
    raise AssertionError(f"Page {url_or_name!r} not registered. Known: {at._registered_pages}")


def main() -> None:
    t0 = time.time()
    print("1. Booting Home (public) & fetching live Yahoo Finance market batch...", flush=True)
    at = AppTest.from_file(APP_FILE, default_timeout=45).run(timeout=45)
    assert_clean(at, "Public Home")
    is_live = at.session_state["_is_live"]
    usdinr = at.session_state["_usdinr"]
    print(f"   Home loaded in {time.time() - t0:.2f}s | live_feed={is_live} | USD/INR=₹{usdinr:.2f}", flush=True)

    assert len(at.get("html")) >= 2, "Expected marquee & hero spotlight HTML on Home"
    at.segmented_control(key="home_movers_tab").set_value("NSE Leaders").run(timeout=45)
    assert_clean(at, "Home NSE Leaders toggle")
    at.segmented_control(key="home_movers_tab").set_value("Flagship Movers").run(timeout=45)
    assert_clean(at, "Home Flagship Movers toggle")

    for pub_url in ["products", "fees", "about", "support", "home"]:
        print(f"2. Checking public page '{pub_url}'...", flush=True)
        at = goto_page(at, pub_url)
        assert_clean(at, f"Public {pub_url}")

    print("3. Clicking 1-Click Demo Login (Trader_XYZ)...", flush=True)
    demo_btn = [b for b in at.button if "Demo Login" in b.label]
    assert demo_btn, "Demo Login button missing on Home page"
    demo_btn[0].click().run(timeout=45)
    assert_clean(at, "Dashboard after Demo Login")
    assert at.session_state["logged_in"] is True
    assert at.session_state["username"] == "Trader_XYZ"
    print(f"   Logged in! Dashboard metrics={len(at.metric)}", flush=True)

    # Verify Dashboard NSE 172-stock filter + pagination Next button works smoothly
    at.segmented_control(key="dash_ex_filter").set_value("NSE").run(timeout=45)
    assert_clean(at, "Dashboard NSE Filter (172 stocks)")
    next_btns = [b for b in at.button if b.key == "dash_next"]
    assert next_btns, "Expected pagination Next button for 172 NSE stocks"
    next_btns[0].click().run(timeout=45)
    assert_clean(at, "Dashboard NSE Pagination Next Page")
    at.segmented_control(key="dash_ex_filter").set_value("Featured").run(timeout=45)
    assert_clean(at, "Dashboard Featured Filter reset")

    # Test clicking SuperChart button on Dashboard stock card (RELIANCE.NS)
    print("4. Clicking SuperChart on Dashboard RELIANCE.NS card...", flush=True)
    sc_btns = [b for b in at.button if b.key == "go_chart_RELIANCE.NS"]
    assert sc_btns, "RELIANCE.NS SuperChart button missing"
    sc_btns[0].click().run(timeout=45)
    assert_clean(at, "SuperChart via Dashboard jump")
    assert len(at.get("plotly_chart")) >= 1

    # Sync AppTest page hash to 'superchart' before switching segmented_control views
    at = goto_page(at, "superchart")
    assert_clean(at, "SuperChart direct")

    # Switch to ML Forecast & Peer Comparison views inside SuperChart
    print("5. Testing ML Forecast & Evaluation view inside SuperChart...", flush=True)
    at.segmented_control(key="terminal_view").set_value("ML Forecast & Evaluation").run(timeout=45)
    assert_clean(at, "SuperChart -> ML Forecast view")
    assert len(at.get("plotly_chart")) >= 1
    assert len(at.dataframe) >= 1

    print("6. Testing Peer Comparison view inside SuperChart...", flush=True)
    at.segmented_control(key="terminal_view").set_value("Peer Comparison").run(timeout=45)
    assert_clean(at, "SuperChart -> Peer Comparison view")

    # Test all remaining authenticated pages
    for auth_url in ["advisor", "orders", "holdings", "positions", "funds", "scanner", "calculator", "dashboard"]:
        print(f"7. Checking authenticated page '{auth_url}'...", flush=True)
        at = goto_page(at, auth_url)
        assert_clean(at, f"Auth {auth_url}")

        if auth_url == "advisor":
            at.chat_input[0].set_value("Should I buy Reliance?").run(timeout=45)
            assert_clean(at, "AI Advisor advisory query")
            at.chat_input[0].set_value("Compare TCS vs Infosys").run(timeout=45)
            assert_clean(at, "AI Advisor multi-stock comparison")
            assert len(at.chat_message) >= 4
            print("   AI Advisor advisory & multi-stock comparison passed cleanly!", flush=True)

        if auth_url == "scanner":
            at.segmented_control(key="apps_view").set_value("Live Multi-Market Scanner").run(timeout=45)
            assert_clean(at, "Scanner -> Live Multi-Market Scanner view")
            assert len(at.dataframe) >= 1

    print("8. Testing Sidebar Logout...", flush=True)
    logout_btns = [b for b in at.sidebar.button if "Logout" in b.label]
    assert logout_btns, "Logout button missing from sidebar"
    logout_btns[0].click().run(timeout=45)
    assert_clean(at, "After Logout")
    assert at.session_state["logged_in"] is False

    print(f"\nALL 14 PAGES & LIVE E2E FLOWS PASSED CLEANLY in {time.time() - t0:.2f}s!", flush=True)


if __name__ == "__main__":
    main()

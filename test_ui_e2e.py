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

    at.segmented_control(key="dash_ex_filter").set_value("NSE").run(timeout=45)
    assert_clean(at, "Dashboard NSE Filter (172 stocks)")
    next_btns = [b for b in at.button if b.key == "dash_next"]
    assert next_btns, "Expected pagination Next button for 172 NSE stocks"
    next_btns[0].click().run(timeout=45)
    assert_clean(at, "Dashboard NSE Pagination Next Page")
    at.segmented_control(key="dash_ex_filter").set_value("Featured").run(timeout=45)
    assert_clean(at, "Dashboard Featured Filter reset")

    print("4. Clicking SuperChart on Dashboard RELIANCE.NS card...", flush=True)
    sc_btns = [b for b in at.button if b.key == "go_chart_RELIANCE.NS"]
    assert sc_btns, "RELIANCE.NS SuperChart button missing"
    sc_btns[0].click().run(timeout=45)
    assert_clean(at, "SuperChart via Dashboard jump")
    assert len(at.get("plotly_chart")) >= 1

    at = goto_page(at, "superchart")
    assert_clean(at, "SuperChart direct")

    print("5. Testing ML Forecast & Evaluation view inside SuperChart...", flush=True)
    at.segmented_control(key="terminal_view").set_value("ML Forecast & Evaluation").run(timeout=45)
    assert_clean(at, "SuperChart -> ML Forecast view")
    assert len(at.get("plotly_chart")) >= 1
    assert len(at.dataframe) >= 1

    print("6. Testing Peer Comparison view inside SuperChart...", flush=True)
    at.segmented_control(key="terminal_view").set_value("Peer Comparison").run(timeout=45)
    assert_clean(at, "SuperChart -> Peer Comparison view")

    for auth_url in ["basket", "health", "advisor", "orders", "holdings", "positions", "funds", "scanner", "calculator", "dashboard"]:
        print(f"7. Checking authenticated page '{auth_url}'...", flush=True)
        at = goto_page(at, auth_url, timeout=75.0 if auth_url == "health" else 45.0)
        assert_clean(at, f"Auth {auth_url}")

        if auth_url == "basket":
            assert len(at.metric) >= 7, "Expected 4 top KPIs + 3 expected outcome KPIs on Smart Basket"
            assert len(at.get("plotly_chart")) >= 2, "Expected Allocation Donut and Correlation Heatmap"
            basket_res = at.session_state["_smart_basket_res"]
            assert len(basket_res.get("items", [])) == 5, f"Expected default 5 stocks in basket, got {len(basket_res.get('items', []))}"
            print("   Smart Basket (5 stocks + covariance analysis) passed cleanly!", flush=True)

        if auth_url == "health":
            buy_btns = [b for b in at.button if (b.key or "").startswith("hl_buy_")]
            assert len(buy_btns) == 10, f"Expected 10 stock health cards on page 1, found {len(buy_btns)}"
            hl_next = [b for b in at.button if b.key == "hl_next_top"]
            assert hl_next, "Expected Next 10 pagination button on Traffic-Light Health"
            hl_next[0].click().run(timeout=45)
            assert_clean(at, "Traffic-Light Health Next 10 Page")
            buy_btns_p2 = [b for b in at.button if (b.key or "").startswith("hl_buy_")]
            assert len(buy_btns_p2) == 10, f"Expected 10 stock health cards on page 2, found {len(buy_btns_p2)}"
            at.selectbox(key="hl_light").set_value("Healthy").run(timeout=45)
            assert_clean(at, "Traffic-Light Health Filter = Healthy")
            healthy_htmls = [h.value for h in at.get("html") if "/100</div>" in h.value]
            assert len(healthy_htmls) == 10, f"Expected 10 Healthy cards, got {len(healthy_htmls)}"
            assert all("🟢 Healthy" in h and "🔴 High Risk" not in h and "🟡 Moderate" not in h for h in healthy_htmls), "Non-Healthy stock appeared under Healthy filter!"
            at.selectbox(key="hl_light").set_value("High Risk").run(timeout=45)
            assert_clean(at, "Traffic-Light Health Filter = High Risk")
            risk_htmls = [h.value for h in at.get("html") if "/100</div>" in h.value]
            assert len(risk_htmls) >= 1, "Expected High Risk cards under High Risk filter"
            assert all("🔴 High Risk" in h and "🟢 Healthy" not in h and "🟡 Moderate" not in h for h in risk_htmls), "Non-High Risk stock appeared under High Risk filter!"
            at.selectbox(key="hl_light").set_value("All Lights").run(timeout=45)
            at.text_input(key="hl_search").set_value("Reliance").run(timeout=45)
            assert_clean(at, "Traffic-Light Health Search")
            print("   Traffic-Light Health (345-stock ML sort, Healthy/High Risk filter strictness, Next 10 & Search) passed cleanly!", flush=True)

        if auth_url == "advisor":
            audit_btn = [b for b in at.button if b.key == "ap_audit_btn"]
            assert audit_btn, "AI Auto-Pilot Audit Portfolio Risk button missing"
            audit_btn[0].click().run(timeout=45)
            assert_clean(at, "AI Auto-Pilot Portfolio Audit")
            at.chat_input[0].set_value("Should I buy Reliance?").run(timeout=45)
            assert_clean(at, "AI Advisor advisory query")
            at.chat_input[0].set_value("Compare TCS vs Infosys").run(timeout=45)
            assert_clean(at, "AI Advisor multi-stock comparison")
            assert len(at.chat_message) >= 6
            print("   AI Advisor Auto-Pilot audit, advisory & multi-stock comparison passed cleanly!", flush=True)

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

    print(f"\nALL 16 PAGES & LIVE E2E FLOWS PASSED CLEANLY in {time.time() - t0:.2f}s!", flush=True)


if __name__ == "__main__":
    main()

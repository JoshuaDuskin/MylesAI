from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

import myles_common
import myles_runtime_v9 as rt
import myles_quick
import myles_model_runtime


def main():
    myles_common.init_db()
    cfg = myles_common.load_config()
    checks = {
        "version": myles_common.APP_VERSION == "10.1.3",
        "config_loads": isinstance(cfg, dict),
        "telegram_setting_present": "telegram_enabled" in cfg,
        "root_exists": myles_common.ROOT.exists(),
        "workspaces_exists": myles_common.WORKSPACES.exists(),
        "localhost_only": cfg.get("core_host") == "127.0.0.1",
        "max_recoveries_raised": int(cfg.get("max_recoveries", 0)) >= 8,
    }

    import myles_tools
    import myles_capabilities
    import job_worker
    import myles_core
    import myles_windows
    import myles_console
    import configure_telegram

    checks["tools_import"] = True
    checks["capability_loader_import"] = True
    checks["worker_import"] = True
    checks["core_import"] = True
    checks["console_import"] = True
    checks["telegram_config_import"] = True
    checks["quick_lookup_import"] = True
    checks["model_runtime_import"] = True
    checks["windows_action_layer_import"] = True
    checks["conversation_fallback_is_natural"] = (
        myles_model_runtime.fallback_conversation("Yo") == "Hey — I’m here. What’s up?"
        and "task" not in myles_model_runtime.fallback_conversation("Yo").lower()
    )
    abstract = myles_model_runtime.abstract_decision_state(
        "Open my private report and stop the current job",
        "start",
        has_active=True,
        has_recent_cancelled=False,
    )
    checks["jev_envelope_excludes_owner_text"] = (
        "private report" not in json.dumps(abstract).lower()
        and set(abstract).issuperset({"proposed_intent", "has_active_task", "has_explicit_action_verb"})
    )

    captured_jev = {}
    original_jev_request = myles_model_runtime._json_request

    def fake_jev_request(url, payload, timeout=3, headers=None):
        captured_jev.update({"url": url, "payload": payload, "headers": headers or {}})
        return {
            "model": "jev-test",
            "answers": {
                "intent": {"type": "choice", "choice": "chat", "confidence": 0.97}
            },
        }

    try:
        myles_model_runtime._json_request = fake_jev_request
        jev_route, jev_meta = myles_model_runtime.verify_with_jev(
            "Open my private report",
            "start",
            has_active=False,
            has_recent_cancelled=False,
            cfg={
                "jev_enabled": True,
                "jev_url": "https://api.typesafe.ai/v1/systemone",
                "jev_model": "jev-latest",
                "jev_min_confidence": 0.60,
            },
            secrets={"TYPESAFE_API_KEY": "test-only"},
        )
    finally:
        myles_model_runtime._json_request = original_jev_request
    checks["jev_official_choice_contract"] = (
        jev_route == "chat"
        and jev_meta.get("used") is True
        and captured_jev.get("payload", {}).get("questions", {}).get("intent", {}).get("type") == "choice"
        and "private report" not in json.dumps(captured_jev.get("payload", {})).lower()
    )

    original_model_request = myles_model_runtime._json_request
    original_model_health = myles_model_runtime.ensure_model_runtime
    replay_calls = {"count": 0}

    def fake_model_health(_cfg, force=False):
        return myles_model_runtime.ModelHealth(True, model="qwen-test", endpoint="http://127.0.0.1:11434", recovered=force)

    def flaky_model_request(_url, _payload, timeout=15, headers=None):
        replay_calls["count"] += 1
        if replay_calls["count"] == 1:
            raise ConnectionRefusedError("test recovery")
        return {"message": {"role": "assistant", "content": "recovered"}}

    try:
        myles_model_runtime.ensure_model_runtime = fake_model_health
        myles_model_runtime._json_request = flaky_model_request
        replay_result = myles_model_runtime.model_chat({}, [{"role": "user", "content": "Yo"}])
    finally:
        myles_model_runtime.ensure_model_runtime = original_model_health
        myles_model_runtime._json_request = original_model_request
    checks["conversation_replays_after_model_recovery"] = (
        replay_calls["count"] == 2
        and replay_result.get("message", {}).get("content") == "recovered"
    )

    core_source = Path(myles_core.__file__).read_text(encoding="utf-8")
    worker_source = Path(job_worker.__file__).read_text(encoding="utf-8")
    tools_source = Path(myles_tools.__file__).read_text(encoding="utf-8")
    caps_source = Path(myles_capabilities.__file__).read_text(encoding="utf-8")
    restart_source = (myles_common.ROOT / "restart_helper.py").read_text(encoding="utf-8")
    supervisor_path = myles_common.ROOT / "bin" / "runtime_supervisor_v074.py"
    start_path = myles_common.ROOT / "START_MYLESAI.cmd"
    stop_path = myles_common.ROOT / "STOP_MYLES.cmd"
    supervisor_source = supervisor_path.read_text(encoding="utf-8") if supervisor_path.exists() else ""
    start_source = start_path.read_text(encoding="utf-8") if start_path.exists() else ""
    stop_source = stop_path.read_text(encoding="utf-8") if stop_path.exists() else ""
    console_path = myles_common.ROOT / "bin" / "myles_console_v074.py"
    console_source = console_path.read_text(encoding="utf-8") if console_path.exists() else ""
    guardian_path = myles_common.ROOT / "bin" / "ensure_myles_runtime.py"
    guardian_source = guardian_path.read_text(encoding="utf-8") if guardian_path.exists() else ""

    # --- Conversation/control routing ---
    checks["semantic_natural_language_router"] = (
        hasattr(myles_core, "_router_call")
        and "OWNER_ACTION=start" in core_source
    )
    checks["deterministic_control_layer"] = (
        "deterministic_control(" in core_source
        and "explicit_stop_requested" in core_source
    )
    checks["question_does_not_stop"] = (
        rt.deterministic_control("You trying that again?", has_active=True, has_recent_cancelled=False) == "status"
    )
    checks["negative_stop_resumes"] = (
        rt.deterministic_control("No don't stop", has_active=False, has_recent_cancelled=True) == "resume"
    )
    checks["explicit_stop_still_stops"] = (
        rt.deterministic_control("Stop", has_active=True, has_recent_cancelled=False) == "stop"
    )
    checks["casual_stop_word_not_destructive"] = (
        rt.explicit_stop_requested("I don't want you to stop working") is False
    )

    dashboard_prompt = (
        "Build the Myles-only progress dashboard under my JoshuaDuskin GitHub account. "
        "Use real Myles runtime and job state only—no sample projects, placeholder percentages, or fake data. "
        "Show current task, state, phase, elapsed time, last verified progress, worker status, queued task count, "
        "last completed task, and last failure/blocker. PineTree is off-limits. "
        "Host the dashboard and verify the public URL actually loads."
    )
    checks["long_dashboard_prompt_is_strong_action"] = rt.strong_action_request(dashboard_prompt) is True
    checks["long_dashboard_prompt_not_status"] = (
        rt.looks_like_status_request(dashboard_prompt, has_active=False) is False
        and rt.deterministic_control(dashboard_prompt, has_active=False, has_recent_cancelled=False) is None
    )
    checks["fortnite_bypasses_model_router"] = (
        "if _direct_fortnite_request(raw) or _fortnite_launch_followup(raw):" in core_source
        and core_source.index("if _direct_fortnite_request(raw) or _fortnite_launch_followup(raw):")
            < core_source.index('CHAT_BUSY.set()')
        and "launch_fortnite_verified" in core_source
        and "FORTNITE_RUNNING" in Path(myles_windows.__file__).read_text(encoding="utf-8")
    )
    checks["fortnite_diagnostic_is_not_shortcut"] = (
        myles_core._direct_fortnite_request("Start Fortnite now.")
        and myles_core._direct_fortnite_request("Can you open Fortnite on the tower?")
        and not myles_core._direct_fortnite_request(
            "Diagnose why launch Fortnite failed, inspect Epic, and report the exact blocker."
        )
    )
    checks["diagnostic_is_not_local_report_lookup"] = (
        not myles_core._local_location_request(
            "Find the exact Epic blocker and report the visible failure."
        )
        and myles_core._local_location_request("Where did you put the backtest report?")
    )
    checks["specific_job_result_is_deterministic"] = (
        myles_core._specific_job_result_request(
            "What was the exact result from M83-20261007-233905-ef3303?"
        )
        and not myles_core._specific_job_result_request("What was the exact result?")
        and not myles_core._specific_job_result_request(
            "Create a real background task continuing M83-20261007-233905-ef3303 and fix its blocker."
        )
        and 'route = {"intent": "job_result", "task": ""}' in core_source
        and "_specific_job_result_answer(raw)" in core_source
    )
    checks["single_guarded_conversation_agent_path"] = (
        'route = {"intent": "agent", "task": ""}' in core_source
        and "def _conversation_agent_turn" in core_source
        and "def _conversation_tool_authorized" in core_source
        and "_conversation_agent_turn(raw, source)" in core_source
    )
    checks["conversation_errors_have_safe_fallback"] = (
        "fallback_conversation(raw, status_text()" in core_source
        and "My local conversation controller hit an error" not in core_source
    )
    checks["model_health_is_observable"] = (
        '"model_runtime": model_health_dict(runtime_cfg)' in core_source
        and '"privacy_mode": "abstract_state_only"' in core_source
    )
    checks["core_strong_action_bypasses_router"] = (
        'elif strong_action_request(raw) and not natural_question(raw):' in core_source
        and '"intent": "modify" if parent else "start"' in core_source
    )
    checks["router_receives_exact_latest_message"] = (
        '{"role": "user", "content": str(raw or "").strip()}' in core_source
    )

    screenshot_followup = (
        "It looks good. Fix it by making it look more modern and add more navigation for me. "
        "Also make your tasks / what you working on more easy to understand. I'm not a robot."
    )
    checks["natural_followup_edit_is_action"] = rt.followup_action_request(screenshot_followup) is True
    checks["angry_reminder_is_action"] = rt.followup_action_request(
        "wtf I told you to redesign the site for the progress etc"
    ) is True
    checks["about_done_is_status"] = (
        rt.looks_like_status_request("You about done?", has_active=True) is True
    )
    checks["chat_execution_promises_are_detected"] = (
        rt.execution_promise_text("Got it. I'll refresh the dashboard and get started right away.") is True
        and rt.execution_promise_text("That makes sense.") is False
    )
    checks["followup_workspace_reuse_present"] = (
        "job.workspace_reused" in core_source
        and "reuse_workspace=reuse" in core_source
        and "OWNER_ACTION=modify" in core_source
    )
    checks["promise_truth_firewall_present"] = (
        "execution_promise_text(final)" in core_source
        and "I created a real background task" in core_source
    )

    # --- Fast conversational lookup / feedback boundary ---
    weather_prompt = "Give me update on weather for tomorrow in Lebanon Missouri"
    feedback_prompt = "This should be a quick google search or something, not a whole fucking job description and shit retry"
    checks["weather_is_quick_lookup"] = myles_quick.looks_like_quick_public_lookup(weather_prompt) is True
    checks["weather_location_parser"] = myles_quick._extract_weather_location(weather_prompt).lower() == "lebanon missouri"
    natural_weather_prompt = "What's up how's the weather in Lebanon Mo tomorrow"
    checks["weather_location_parser_state_abbrev_and_day_tail"] = (
        myles_quick._extract_weather_location(natural_weather_prompt).lower() == "lebanon missouri"
    )
    checks["weather_location_variants_include_city_fallback"] = (
        myles_quick._weather_location_variants("Lebanon Mo tomorrow")[:2] == ["Lebanon Missouri", "Lebanon"]
    )
    checks["weather_day_parser"] = myles_quick._requested_weather_day(weather_prompt) == "tomorrow"
    sample_weather = myles_quick._format_weather_payload(
        {"name": "Lebanon", "admin1": "Missouri", "country_code": "US"},
        {
            "daily": {
                "time": ["2026-09-24", "2026-09-25"],
                "weather_code": [3, 2],
                "temperature_2m_max": [75, 76],
                "temperature_2m_min": [60, 63],
                "precipitation_probability_max": [20, 10],
                "wind_speed_10m_max": [11, 9],
            }
        },
        "tomorrow",
    )
    checks["weather_answer_is_plain_and_compact"] = (
        "Tomorrow in Lebanon, Missouri" in sample_weather
        and "high 76°F" in sample_weather
        and "Rain chance 10%" in sample_weather
        and "###" not in sample_weather
    )
    checks["behavior_correction_is_feedback"] = rt.behavior_feedback_request(feedback_prompt) is True
    checks["behavior_correction_not_followup_job"] = rt.followup_action_request(feedback_prompt) is False
    capability_prompt = "Add the tools to your kit so you can look it up buddy"
    checks["self_capability_request_detected"] = rt.self_capability_request(capability_prompt) is True
    checks["self_capability_not_previous_artifact"] = rt.refers_to_previous_result(capability_prompt) is False
    checks["self_capability_not_followup_modify"] = rt.followup_action_request(capability_prompt) is False
    checks["self_capability_fresh_workspace_route_present"] = (
        "elif self_capability_request(raw):" in core_source
        and '"intent": "start", "task": _self_capability_task(raw)' in core_source
        and "not any previous project artifact" in core_source
    )
    checks["feedback_precedes_followup_job_routing"] = (
        "elif behavior_feedback_request(raw):" in core_source
        and "elif quick.looks_like_quick_public_lookup(raw):" in core_source
        and core_source.index("elif behavior_feedback_request(raw):")
            < core_source.index("elif quick.looks_like_quick_public_lookup(raw):")
            < core_source.index("elif self_capability_request(raw):")
            < core_source.index("elif strong_action_request(raw) and not natural_question(raw):")
    )
    lookup_branch = core_source.split('if intent == "lookup":', 1)[1].split('elif intent == "feedback":', 1)[0]
    checks["quick_lookup_has_no_job_creation"] = (
        'OWNER_ACTION=lookup' in lookup_branch
        and 'def _quick_lookup_answer' in core_source
        and '_start_task(' not in lookup_branch
        and 'create_job(' not in lookup_branch
    )
    checks["job_ack_is_compact"] = (
        "def _human_task_label" in core_source
        and "I’m on it — I’ll post a concise verified summary when it’s finished. ({label})" in core_source
        and "I'm working on: {task or raw}" not in core_source
    )
    cleaned = myles_core._telegram_plain_text("### **General Overview**\n* **Weather:** Clear")
    checks["telegram_plain_text_cleanup"] = (
        cleaned == "General Overview\n• Weather: Clear"
    )


    # --- Capability truth / actual tool inventory ---
    checks["capability_questions_are_deterministic"] = (
        myles_core._capability_report_request("What can you do?") is True
        and myles_core._capability_report_request("Do you have internet?") is True
        and myles_core._capability_report_request("How are you?") is False
    )
    capability_report = myles_core._capability_truth_report().lower()
    checks["capability_report_truthfully_has_internet"] = (
        "internet: yes" in capability_report
        and "browser automation" in capability_report
        and "downloads" in capability_report
    )
    checks["capability_report_truthfully_has_self_update"] = (
        "self-development" in capability_report
        and "rollback backup" in capability_report
    )
    checks["capability_report_describes_persistent_history"] = (
        "persistent history" in capability_report
        and "not perfect human-like long-term semantic memory" in capability_report
    )
    checks["reusable_web_search_tool_present"] = (
        hasattr(myles_tools, "web_search")
        and '"name":"web_search"' in worker_source
        and '"name":"tool_inventory"' in worker_source
    )
    checks["dashboard_local_chat_cors_is_exact_origin"] = (
        "https://joshuaduskin.github.io" in core_source
        and "Access-Control-Allow-Origin" in core_source
        and "def do_OPTIONS" in core_source
    )


    # --- v9.6 canonical dashboard + truthful live queue/status ---
    checks["dashboard_aliases_collapse_to_one_repo"] = (
        myles_tools._canonical_myles_dashboard_repo_name("Myles-ControlCenter") == "MylesAI"
        and myles_tools._canonical_myles_dashboard_repo_name("myles-dashboard") == "MylesAI"
        and myles_tools._canonical_myles_dashboard_repo_name("Myles-AI-Dashboard") == "MylesAI"
    )
    checks["dashboard_url_is_direct_not_job"] = (
        myles_core._dashboard_url_request("Give me the dashboard URL") is True
        and myles_core._dashboard_url_request("Redesign the dashboard") is False
        and "MylesAI" in myles_core._dashboard_url_reply()
    )
    snap2 = myles_tools._runtime_public_snapshot()
    checks["public_status_schema_v2_has_real_queue"] = (
        snap2.get("schema_version") in {2, 3, 4}
        and isinstance(snap2.get("queued_tasks"), list)
        and "queue_count" in snap2
    )
    checks["status_feed_nonblocking_async_present"] = (
        hasattr(myles_tools, "runtime_status_feed_tick_async")
        and "runtime_status_feed_tick_async()" in core_source
    )
    checks["status_feed_forced_freshness_present"] = (
        "force_refresh_seconds" in tools_source
        and "force_due" in tools_source
    )


    # --- v9.7 continuous owner program ---
    checks["continuous_enable_language_detected"] = (
        myles_core._continuous_enable_request("Work nonstop on yourself tonight") is True
        and myles_core._continuous_enable_request("Keep improving yourself") is True
    )
    checks["continuous_disable_language_detected"] = (
        myles_core._continuous_disable_request("Stop continuous improvement") is True
        and myles_core._continuous_disable_request("Don't stop improving yourself") is False
    )
    checks["continuous_program_tick_present"] = (
        hasattr(myles_core, "_continuous_program_tick")
        and "_continuous_program_tick()" in core_source
        and "CONTINUOUS IMPROVEMENT CYCLE" in core_source
    )
    checks["owner_work_preempts_continuous_lane"] = (
        "_preempt_continuous_for_owner()" in core_source
        and 'phase="preempted_for_owner"' in core_source
    )
    checks["continuous_cycles_are_quiet"] = (
        'if source != "continuous":' in worker_source
        and 'source == "continuous" and load_config().get("telegram_enabled")' in worker_source
    )
    checks["local_public_status_endpoint_present"] = (
        'if path == "/api/public-status":' in core_source
        and "tools._runtime_public_snapshot()" in core_source
    )
    snap3 = myles_tools._runtime_public_snapshot()
    checks["public_status_schema_v3_has_continuous_program"] = (
        snap3.get("schema_version") == 4
        and isinstance(snap3.get("continuous_program"), dict)
        and "queued_tasks" in snap3
    )

    # --- Single-instance / startup ---
    checks["graceful_local_shutdown_endpoint"] = (
        '/api/control/shutdown' in core_source
        and 'self.server.shutdown' in core_source
        and 'STOP.set()' in core_source
    )
    checks["single_instance_binds_before_telegram"] = (
        "server = MylesHTTPServer" in core_source
        and "target=telegram_loop" in core_source
        and core_source.index("server = MylesHTTPServer") < core_source.index("target=telegram_loop")
    )
    checks["canonical_supervisor_contract_present"] = (
        supervisor_path.exists()
        and "runtime_supervisor_v074.pid" in supervisor_source
        and "runtime_supervisor_v074.lock" in supervisor_source
        and "runtime_supervisor_v074.stop" in supervisor_source
        and "RESTART_REQUEST" in supervisor_source
        and "_wait_for_core_offline" in supervisor_source
        and "_restart_for_update" in supervisor_source
    )
    checks["canonical_start_path_is_persistent"] = (
        start_path.exists()
        and "runtime_supervisor_v074.py" in start_source
        and "myles_console_v074.py" in start_source
        and "MYLES_SUPERVISOR_RUNNING" in start_source
    )
    checks["windowless_runtime_guardian"] = (
        guardian_path.exists()
        and "runtime_supervisor_v074.py" in guardian_source
        and "CREATE_NO_WINDOW" in guardian_source
        and "DETACHED_PROCESS" in guardian_source
        and "powershell.exe" not in guardian_source.lower()
    )
    checks["canonical_stop_path_is_scoped"] = (
        stop_path.exists()
        and "runtime_supervisor.py" in stop_source
        and "taskkill" not in stop_source.lower()
    )
    checks["visible_console_waits_for_hidden_core"] = (
        "while time.time()<end and not health()" in console_source
        and "DASHBOARD = \"https://joshuaduskin.github.io/MylesAI/\"" in console_source
    )
    checks["core_restart_is_supervisor_owned"] = (
        "restart_helper.py" not in core_source
        and "RESTART_REQUEST" in core_source
        and "supervisor will perform verified restart" in core_source
    )
    checks["legacy_restart_helper_is_retired_shim"] = (
        "never starts the core" in restart_source
        and "runtime_supervisor.py" in restart_source
        and "subprocess.Popen" not in restart_source
    )

    # --- Model/tool recovery ---
    checks["private_reasoning_filtered"] = (
        myles_common.clean_model_text("<think>secret</think>hello") == "hello"
    )
    checks["action_job_starts_real_worker"] = (
        "def _start_task" in core_source and "start_job(job)" in core_source
    )
    checks["compact_action_planner_present"] = (
        "def call_execution_bridge" in worker_source
        and "action_planner.plan" in worker_source
        and "write_generated_file" in worker_source
    )
    checks["planner_internal_retry_present"] = (
        "planner_retry_count" in worker_source
        and "action_planner.retry" in worker_source
    )
    checks["model_internal_retry_present"] = "model.retry" in worker_source
    checks["internal_recovery_queue"] = "job.internal_recovery_queued" in worker_source
    checks["safe_tool_retry_is_wired"] = (
        "def execute_with_internal_retry" in worker_source
        and worker_source.count("execute_with_internal_retry(job_id, name, args)") >= 2
        and "tool.internal_retry" in worker_source
    )

    malformed = '{"tool":"write_text_file","path":"C:\\\\Users\\\\Joshu\\\\x\\\\index.html","content":"<!DOCTYPE html>\\n<html>ok</html>"}'
    tool, args = rt.normalize_action_plan(malformed, {"write_text_file"})
    checks["malformed_multiline_json_repaired"] = (
        tool == "write_text_file" and args.get("path", "").endswith("index.html")
    )
    checks["structured_tool_outcomes"] = (
        rt.classify_tool_result("OWNER_AUTH_REQUIRED: login").owner_gate
        and rt.classify_tool_result("TIMEOUT after 10s").retryable
        and rt.classify_tool_result("PATH=x\\nSIZE=1").ok
    )

    checks["large_file_generator_present"] = hasattr(myles_tools, "write_generated_file")
    checks["visual_desktop_toolkit_present"] = all(
        hasattr(myles_tools, name)
        for name in (
            "desktop_windows", "desktop_activate_window", "desktop_screenshot",
            "desktop_click", "desktop_key", "desktop_type",
        )
    ) and all(name in worker_source for name in (
        '"desktop_windows"', '"desktop_screenshot"', '"desktop_click"',
        '"desktop_key"', '"desktop_type"', "_desktop_image_message",
    )) and all(marker in tools_source for marker in (
        "_enable_windows_dpi_awareness", "class MOUSEINPUT", "class HARDWAREINPUT",
    ))
    checks["deterministic_patch_tool_present"] = hasattr(myles_tools, "apply_text_patch")

    # --- Completion verification ---
    checks["completion_verifier_present"] = (
        "def completion_gaps" in worker_source
        and "completion.rejected" in worker_source
        and "completion.accepted" in worker_source
    )
    urls = job_worker._extract_http_urls(
        "Live: **https://joshuaduskin.github.io/progress-dashboard/** and "
        "`https://example.com/test/`"
    )
    checks["markdown_wrapped_urls_are_cleaned"] = (
        "https://joshuaduskin.github.io/progress-dashboard/" in urls
        and "https://example.com/test/" in urls
    )
    checks["publisher_evidence_can_supply_final_url"] = (
        "def _verified_public_url_from_traces" in worker_source
        and "def _augment_final_with_verified_evidence" in worker_source
    )

    test_ws = myles_common.WORKSPACES / "_v91_completion_selftest"
    shutil.rmtree(test_ws, ignore_errors=True)
    test_ws.mkdir(parents=True, exist_ok=True)
    (test_ws / "dashboard.html").write_text("<html><body>test</body></html>", encoding="utf-8")
    gaps = job_worker.completion_gaps(
        "SELFTEST",
        "Build a progress dashboard and host it on the internet with a public URL",
        test_ws,
        "Perfect! The remote is already configured for GitHub Pages at",
    )
    checks["rejects_false_hosting_completion"] = (
        any("public" in g.lower() for g in gaps)
        and any("entrypoint" in g for g in gaps)
    )

    (test_ws / "index.html").write_text(
        """
        <html><script>
        async function fetchStatus(){
          const mockResponse = await getMockRuntimeState();
          updateDashboard(mockResponse);
        }
        function getMockRuntimeState(){
          return {task:{id:`task_${Math.floor(Math.random()*10000)}`}};
        }
        // For this static dashboard, we simulate the data retrieval.
        </script></html>
        """,
        encoding="utf-8",
    )
    fake_gaps = job_worker.completion_gaps(
        "SELFTEST",
        "Build a dashboard using real Myles runtime data only; no sample projects or fake data.",
        test_ws,
        "Dashboard created.",
    )
    checks["rejects_actual_mock_dashboard_pattern"] = any(
        "sample/simulated/placeholder" in g for g in fake_gaps
    )

    (test_ws / "index.html").write_text(
        "<html><script>fetch('https://raw.githubusercontent.com/JoshuaDuskin/MylesAI/main/status.json?x='+Date.now())</script></html>",
        encoding="utf-8",
    )
    live_gaps = job_worker.completion_gaps(
        "SELFTEST_NO_FEED",
        "Build and host a public live dashboard using real Myles runtime data only; no fake data.",
        test_ws,
        "Dashboard created.",
    )
    checks["public_live_dashboard_requires_verified_feed"] = any(
        "runtime status feed" in g.lower() for g in live_gaps
    )

    snapshot = myles_tools._runtime_public_snapshot()
    serialized_snapshot = json.dumps(snapshot).lower()
    checks["sanitized_status_snapshot_present"] = (
        snapshot.get("schema_version") in {1, 2, 3, 4}
        and "prompt" not in serialized_snapshot
        and "workspace" not in serialized_snapshot
        and "runner_pid" not in serialized_snapshot
    )
    checks["status_feed_background_publisher_present"] = (
        hasattr(myles_tools, "configure_runtime_status_feed")
        and hasattr(myles_tools, "runtime_status_feed_tick")
        and hasattr(myles_tools, "runtime_status_feed_tick_async")
        and "runtime_status_feed_tick_async()" in core_source
        and "configure_runtime_status_feed" in worker_source
    )
    shutil.rmtree(test_ws, ignore_errors=True)

    # --- Capability framework behavior, not just source presence ---
    checks["capability_plugin_registry_present"] = (
        hasattr(myles_capabilities, "discover_capabilities")
        and hasattr(myles_capabilities, "execute")
        and (myles_common.ROOT / "capabilities").exists()
    )
    checks["capability_enable_flag_is_enforced"] = (
        "capability_plugins_enabled" in caps_source and "def _enabled" in caps_source
    )
    checks["capability_modules_are_cached"] = (
        "_MODULE_CACHE" in caps_source and "st_mtime_ns" in caps_source
    )
    checks["capability_background_is_nonblocking"] = (
        "_BG_RUNNING" in caps_source and "threading.Thread(" in caps_source
    )

    # Prove a provider module keeps in-memory state across discovery calls.
    cap_dir = myles_common.ROOT / "capabilities"
    cap_dir.mkdir(parents=True, exist_ok=True)
    temp_cap = cap_dir / "v92_cache_selftest.py"
    temp_cap.write_text(
        "STATE={'n':0}\n"
        "DESCRIPTION='selftest'\nAUTH_KIND='none'\nTOOL_DEFS=[]\nTOOLS={}\n",
        encoding="utf-8",
    )
    try:
        mod1 = myles_capabilities._load_module(temp_cap)
        mod1.STATE["n"] = 7
        mod2 = myles_capabilities._load_module(temp_cap)
        checks["capability_state_persists"] = (mod1 is mod2 and mod2.STATE["n"] == 7)
    finally:
        temp_cap.unlink(missing_ok=True)

    # --- PineTree boundary (application-layer) ---
    checks["powershell5_guard"] = (
        "Windows PowerShell 5.1" in tools_source
        and '"||" in command or "&&" in command' in tools_source
    )
    checks["pinetree_tool_refusal"] = myles_tools._contains_pinetree_reference(
        "https://github.com/PineTreePayments/app.pinetree-payments"
    ) is True
    checks["pinetree_actual_task_blocked"] = (
        myles_core._is_pinetree_task("Edit PineTreePayments app.pinetree-payments") is True
    )
    checks["pinetree_exclusion_allowed"] = (
        myles_core._is_pinetree_task(
            "Build a Myles dashboard. Do not access or touch any PineTree resource."
        ) is False
    )

    # --- Self-update completeness / rollback ---
    checks["self_update_copies_full_v9_runtime"] = (
        '"myles_runtime_v9.py"' in tools_source
        and '"myles_model_runtime.py"' in tools_source
        and '"myles_windows.py"' in tools_source
        and '"myles_capabilities.py"' in tools_source
        and '"myles_quick.py"' in tools_source
    )
    checks["self_update_requires_full_runtime"] = "missing_required_runtime_files" in tools_source
    checks["self_update_has_supervisor_health_rollback"] = (
        "def _restart_for_update" in supervisor_source
        and "_restore_backup" in supervisor_source
        and "candidate restart failed health check" in supervisor_source
        and "rollback passed health check" in supervisor_source
    )

    checks["dedicated_github_profile_required"] = (
        "github_identity.json" in tools_source
        and "GH_CONFIG_DIR" in tools_source
        and "dedicated-gh-profile" in tools_source
    )
    checks["gcm_reuse_removed"] = (
        "credential-manager" not in tools_source
        and "git credential fill" not in tools_source
    )
    checks["auth_gate_state"] = (
        "blocked_auth" in worker_source and "awaiting_owner_auth" in worker_source
    )
    checks["chat_live_state_injected"] = "LIVE_EXECUTION_STATE" in core_source
    checks["automatic_continuation"] = (
        "job.continuation_queued" in worker_source and "continuing_unverified" in worker_source
    )

    result = {
        "version": myles_common.APP_VERSION,
        "checks": checks,
        "pass": all(checks.values()),
    }
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

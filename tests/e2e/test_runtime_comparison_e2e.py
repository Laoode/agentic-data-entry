"""Opt-in same-model comparisons across different runtime and tool paths."""

import asyncio
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
from uuid import uuid4

import pytest

from tests.e2e.capability_cases import CAPABILITY_SEED
from tests.e2e.comparison import (
    ComparisonScope,
    SingleWorkbookSUT,
    fixture_digest,
    seeded_comparison_case,
)
from tests.e2e.comparison_owner import comparison_owner
from tests.e2e.comparison_run import ComparisonRun
from tests.e2e.conftest import requires_live
from tests.e2e.engine_inprocess import TURN_TIMEOUT_S, run_case_inprocess
from tests.e2e.report import Report
from tests.e2e.sandbox import sandbox_enabled
from tests.e2e.sut import LegacySUT, MainAgentSUT

pytestmark = [
    requires_live,
    pytest.mark.skipif(
        os.environ.get("E2E_RUNTIME_COMPARISON") != "1",
        reason="Set E2E_RUNTIME_COMPARISON=1 to call live models for repeated comparisons",
    ),
]


@pytest.fixture(scope="module", autouse=True)
def comparison_manifests(request):
    """Save selected schedules before service setup can fail.

    Args:
        request: Pytest collection used to exclude deselected scenarios.

    Yields:
        Scenario-to-run/path mapping with only non-secret configuration.
    """
    from config.settings import get_settings
    from klaudia.core.agent.agent import RunLimits

    if os.environ.get("E2E_SANDBOX_ACTIVE") != "1" or not sandbox_enabled():
        raise RuntimeError("Runtime comparison requires the isolated sandbox")
    settings = get_settings()
    if settings.memory_mode != "off" or settings.sheets_backend != "ledger":
        raise RuntimeError(
            "Runtime comparison requires MEMORY_MODE=off and SHEETS_BACKEND=ledger"
        )
    metadata = {
        "comparison_kind": "same_model_different_runtime_and_tools",
        "model": settings.llm_model,
        "provider": settings.model_provider,
        "temperature": settings.llm_temperature,
        "disable_thinking": settings.llm_disable_thinking,
        "thinking_level_routing": settings.llm_thinking_level_routing,
        "thinking_level_worker": settings.llm_thinking_level_worker,
        "fixture_seed": CAPABILITY_SEED,
        "fixture_version": 1,
        "scope": "single_workbook_fixture",
        "git_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "git_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
        ),
        "freeze_now": os.environ.get("E2E_FREEZE_NOW"),
        "turn_timeout_seconds": TURN_TIMEOUT_S,
        "memory_mode": settings.memory_mode,
        "main_agent_limits": RunLimits().model_dump(),
    }
    repeats = int(os.environ.get("E2E_COMPARISON_REPEATS", "3"))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifests = {}
    for item in request.session.items:
        if item.module is request.module:
            scenario = item.callspec.params["scenario"]
            run = ComparisonRun(scenario, repeats, metadata)
            path = (
                Path(__file__).with_name("outputs")
                / f"comparison-{scenario}-{stamp}-{uuid4().hex}.json"
            )
            run.write(path)
            manifests[scenario] = (run, path)
    try:
        yield manifests
    finally:
        for run, path in manifests.values():
            run.write(path)
            print(f"Runtime comparison report: {path}")


def configured_main_agent(container):
    """Use the same configured model/provider as the legacy container.

    Args:
        container: Live sandbox services and settings.

    Returns:
        Fresh optional main agent with checked append support.
    """
    from app.services.core.operations import OperationService
    from klaudia.core.agent.agent import MainAgent
    from klaudia.core.supervisor.llm import build_chat_llm

    settings = container.settings
    endpoint, api_key = settings.active_openai_endpoint()
    model = build_chat_llm(
        model=settings.llm_model,
        provider=settings.model_provider,
        temperature=settings.llm_temperature,
        use_vertexai=settings.google_genai_use_vertexai,
        llm_api_key=settings.llm_api_key,
        google_cloud_project=settings.google_cloud_project,
        google_cloud_location=settings.google_cloud_location,
        openai_base_url=endpoint,
        openai_api_key=api_key,
        thinking_level=settings.llm_thinking_level_worker,
        disable_thinking=settings.llm_disable_thinking,
    )
    return MainAgent(
        model, container.catalogue, operations=OperationService(container.ledger_store)
    )


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.e2e
@pytest.mark.parametrize(
    "scenario", ["sum_1000", pytest.param("append", marks=pytest.mark.mutating)]
)
async def test_runtime_comparison(
    scenario, comparison_manifests, container, orchestrator, spy, extraction_spy
):
    """Attempt the complete selected schedule before asserting financial outcomes."""
    run, path = comparison_manifests[scenario]

    async def execute_trial(trial):
        """Seed fresh identity and state, check equivalence, then grade one turn."""
        async with comparison_owner(container.db_client.pool) as user_id:
            trial["fixture_user_id"] = user_id
            async with seeded_comparison_case(
                container.ledger_store, scenario, user_id
            ) as fixture:
                trial["fixture_workbook_id"] = fixture.workbook_id
                run.check_fixture(trial, await fixture_digest(fixture))
                run.write(path)
                delegate = (
                    LegacySUT(orchestrator, (spy, extraction_spy))
                    if trial["runtime"] == "legacy"
                    else MainAgentSUT(configured_main_agent(container))
                )
                adapter = SingleWorkbookSUT(
                    delegate,
                    container.ledger_store.pool,
                    ComparisonScope(user_id, fixture.workbook_id),
                )
                try:
                    records = await run_case_inprocess(
                        orchestrator,
                        spy,
                        extraction_spy,
                        fixture.case,
                        spreadsheet_ids={"active": fixture.workbook_id},
                        sut=adapter,
                        observe_state=fixture.observe_state,
                    )
                    report = Report(records)
                    trial["report"] = report.to_json()
                    return report
                finally:
                    await asyncio.wait_for(orchestrator.drain_background(), timeout=30)

    await run.execute(execute_trial, path)
    assert run.to_json()["passed"] == run.to_json()["planned"], run.to_json()

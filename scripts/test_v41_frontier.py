"""Regression checks for score integrity and Genesys-only job configuration."""
import argparse
import json
import os
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch
from types import SimpleNamespace

from run_v41_frontier import MANIFEST, build_config, summarize_result


class FrontierTests(unittest.TestCase):
    def test_infrastructure_zero_is_not_a_model_zero(self):
        for result in ({}, {"verifier_result": {"rewards": {"reward": 0, "valid": 0}}},
                       {"verifier_result": {"rewards": {"reward": 1, "valid": 1}},
                        "exception_info": {"exception_type": "Timeout"}}):
            with self.subTest(result=result):
                summary = summarize_result(result)
                self.assertEqual(summary["status"], "error")
                self.assertIsNone(summary["score"])

    def test_valid_zero_and_partial_score(self):
        for reward in (0, 0.5863, 1):
            summary = summarize_result({"verifier_result": {"rewards": {"reward": reward, "valid": 1}}})
            self.assertEqual(summary["status"], "completed")
            self.assertAlmostEqual(summary["score"], reward * 100)

    def test_agent_budget_exhaustion_keeps_valid_grade(self):
        summary = summarize_result({"verifier_result": {"rewards": {"reward": 0.4, "valid": 1}},
                                    "exception_info": {"exception_type": "AgentTimeoutError"}})
        self.assertEqual(summary["score"], 40)
        self.assertTrue(summary["budget_exhausted"])

    def test_invalid_reward_rejected(self):
        for reward in (float("nan"), float("inf"), -1, 1.1, "1"):
            summary = summarize_result({"verifier_result": {"rewards": {"reward": reward, "valid": 1}}})
            self.assertIsNone(summary["score"])

    def test_genesys_config_has_no_oracle_or_literal_credentials(self):
        manifest = json.loads(MANIFEST.read_text())
        name, spec = next(iter(manifest["tasks"].items()))
        args = argparse.Namespace(mode="genesys", memory_mb=None)
        with patch.dict(os.environ, {"LUA_API_KEY": "test-secret-must-not-be-serialized"}):
            config = build_config(Path(name), spec, manifest, args)
        serialized = config.model_dump_json()
        self.assertNotIn("test-secret-must-not-be-serialized", serialized)
        self.assertNotIn("HARBOR_ORACLE_FLAG", serialized)
        self.assertEqual(len(config.agents), 1)
        self.assertEqual(config.agents[0].model_name, "lua/genesys-pi-house")
        self.assertEqual(config.agents[0].extra_allowed_hosts, ["api.lua.vision"])
        self.assertEqual(config.n_attempts, 1)
        self.assertEqual(config.retry.max_retries, 0)
        self.assertFalse(config.verifier.disable)
        self.assertFalse(config.environment.mounts)

    def test_native_configs_preserve_controls_and_limits(self):
        manifest = json.loads(MANIFEST.read_text())
        name = "cranelift-codegen-opt"
        for mode, model in (("astra", "gpt-6-astra"), ("fable", "claude-fable-5-1")):
            config = build_config(Path(name), manifest["tasks"][name], manifest,
                                  argparse.Namespace(mode=mode, memory_mb=32768))
            from harbor.agents.factory import AgentFactory
            AgentFactory.run_preflight(config.agents[0])
            self.assertEqual(config.agents[0].model_name, model)
            self.assertEqual(config.agents[0].env, {})
            self.assertEqual(config.environment.override_memory_mb, 32768)
            self.assertNotIn("HARBOR_ORACLE_FLAG", config.model_dump_json())
            self.assertFalse(config.environment.mounts)
            self.assertEqual(config.n_attempts, 1)
            self.assertEqual(config.retry.max_retries, 0)
            self.assertFalse(config.verifier.disable)

    def test_claude_auth_never_inherits_api_key(self):
        from frontier_native import FrontierClaude
        adapter = object.__new__(FrontierClaude)
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            self.assertEqual(adapter._resolve_auth_env(), {})


class InstallerNetworkTests(unittest.IsolatedAsyncioTestCase):
    async def test_successful_preflight_reaches_model(self):
        from frontier_opencode import FrontierOpenCode
        from harbor.environments.base import ExecResult
        adapter = object.__new__(FrontierOpenCode)
        adapter.exec_as_agent = AsyncMock(return_value=ExecResult(return_code=0))
        with patch("frontier_opencode.OpenCode.run", new=AsyncMock()) as model_run:
            await adapter.run("task", None, None)
            model_run.assert_awaited_once_with("task", None, None)

    async def test_restores_offline_policy_even_when_installer_fails(self):
        from frontier_opencode import FrontierOpenCode
        from harbor.models.task.config import NetworkMode, NetworkPolicy
        policy = NetworkPolicy(network_mode=NetworkMode.ALLOWLIST)
        environment = SimpleNamespace(network_policy=policy, set_network_policy=AsyncMock())
        adapter = object.__new__(FrontierOpenCode)
        with patch("frontier_opencode.OpenCode.install", new=AsyncMock(side_effect=RuntimeError("installer failed"))):
            with self.assertRaisesRegex(RuntimeError, "installer failed"):
                await adapter.install(environment)
        calls = environment.set_network_policy.call_args_list
        self.assertEqual(calls[0].args[0].network_mode, NetworkMode.PUBLIC)
        self.assertEqual(calls[-1].args[0], policy)


if __name__ == "__main__":
    unittest.main()

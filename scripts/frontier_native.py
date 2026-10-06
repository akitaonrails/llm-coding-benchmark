"""Native subscription harnesses with phase-limited network and isolated auth."""
import json
from pathlib import Path
from harbor.agents.installed.codex import Codex
from harbor.agents.installed.claude_code import ClaudeCode
from harbor.models.task.config import NetworkMode, NetworkPolicy


class RestrictedInstall:
    async def install(self, environment):
        original = environment.network_policy
        await environment.set_network_policy(NetworkPolicy(network_mode=NetworkMode.PUBLIC))
        try:
            await super().install(environment)
        finally:
            await environment.set_network_policy(original)

    async def check_isolation(self, environment):
        await self.exec_as_agent(environment, command=(
            'test ! -r /root/tests/test.sh && test ! -e /solution && '
            '! curl -fsS -m 5 -o /dev/null https://github.com'
        ))


class FrontierCodex(RestrictedInstall, Codex):
    def _resolve_auth_json_path(self):
        # Keep this choice out of extra_env: Harbor treats AUTH keys as secrets
        # and would replace every "1" in trial artifacts for a boolean flag.
        path = Path.home() / '.codex/auth.json'
        if not path.is_file():
            raise RuntimeError('Astra subscription credentials are missing')
        return path

    async def run(self, instruction, environment, context):
        await self.check_isolation(environment)
        auth = json.loads(self._resolve_auth_json_path().read_text())
        if auth.get('OPENAI_API_KEY') or not auth.get('tokens'):
            raise RuntimeError('Astra requires subscription auth, without an API key')
        await super().run(instruction, environment, context)


class FrontierClaude(RestrictedInstall, ClaudeCode):
    def _resolve_auth_env(self):
        # Authenticate through the isolated credential file, never an API key.
        return {}

    async def run(self, instruction, environment, context):
        await self.check_isolation(environment)
        source = Path.home() / '.claude/.credentials.json'
        oauth = json.loads(source.read_text()).get('claudeAiOauth') or {}
        if not (oauth.get('accessToken') or oauth.get('refreshToken')):
            raise RuntimeError('Fable subscription credentials are empty; run claude auth login')
        directory = (self.environment_logs_dir / 'sessions').as_posix()
        remote = '/tmp/frontier-claude-credentials.json'
        link = directory + '/.credentials.json'
        await self.exec_as_agent(environment, command=f'mkdir -p {directory}')
        await environment.upload_file(source, remote)
        if environment.default_user is not None:
            await self.exec_as_root(environment, command=f'chown {environment.default_user} {remote}')
        await self.exec_as_agent(environment, command=f'ln -sf {remote} {link}')
        try:
            await super().run(instruction, environment, context)
        finally:
            await self.exec_as_root(environment, command=f'rm -f {remote} {link}')

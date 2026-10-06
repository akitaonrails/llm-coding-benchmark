"""Harbor OpenCode adapter with network access limited by execution phase.

Task images do not contain Node/OpenCode. Permit the stock installer network
access before any model runs, then restore the original offline task policy.
Harbor adds only the model API hostname during agent.run().
"""
from harbor.agents.installed.opencode import OpenCode
from harbor.models.task.config import NetworkMode, NetworkPolicy


class FrontierOpenCode(OpenCode):
    async def install(self, environment):
        original = environment.network_policy
        await environment.set_network_policy(NetworkPolicy(network_mode=NetworkMode.PUBLIC))
        try:
            await super().install(environment)
        finally:
            await environment.set_network_policy(original)

    async def run(self, instruction, environment, context):
        await self.exec_as_agent(environment, command=(
            "test ! -r /root/tests/test.sh && test ! -e /solution && "
            "test \"$(curl -sS -m 15 -o /dev/null -w '%{http_code}' "
            "https://api.lua.vision/v1/models)\" = 401 && "
            "! curl -fsS -m 5 -o /dev/null https://github.com"
        ))
        await super().run(instruction, environment, context)

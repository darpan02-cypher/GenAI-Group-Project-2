"""Loop tests using a scripted fake provider (no API key or model needed)."""
from langchain_core.messages import AIMessage

from codemax.agent.loop import Agent, AgentConfig, DENIED_MESSAGE
from codemax.providers.base import LLMProvider
from codemax.tools.builtin import builtin_tools


class FakeProvider(LLMProvider):
    """Returns pre-scripted replies one by one."""
    name = "fake"

    def __init__(self, replies):
        self.replies = list(replies)

    def chat(self, messages, tools, on_token=None):
        return self.replies.pop(0)


class FakeUI:
    def __init__(self, approve=True):
        self.approve = approve
        self.events = []

    def on_token(self, text): pass
    def on_thinking(self, active): pass
    def confirm_tool(self, name, args):
        self.events.append(("confirm", name))
        return self.approve
    def on_tool_start(self, name, args): self.events.append(("start", name))
    def on_tool_result(self, name, result): self.events.append(("result", name))
    def on_notice(self, text): self.events.append(("notice", text))


def call(name, args, id="1"):
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": id}])


def test_reads_file_then_finishes(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hello")
    provider = FakeProvider([call("read_file", {"path": str(f)}), AIMessage(content="done")])
    ui = FakeUI()
    answer = Agent(provider, builtin_tools(), ui).run("read it")
    assert answer == "done"
    assert ("confirm", "read_file") not in ui.events  # read-only: no confirmation


def test_confirm_mode_denied_does_not_write(tmp_path):
    f = tmp_path / "out.txt"
    provider = FakeProvider([
        call("write_file", {"path": str(f), "content": "x"}), AIMessage(content="ok")])
    agent = Agent(provider, builtin_tools(), FakeUI(approve=False))
    agent.run("write it")
    assert not f.exists()
    assert agent.messages[-2].content == DENIED_MESSAGE


def test_auto_mode_writes_without_asking(tmp_path):
    f = tmp_path / "out.txt"
    provider = FakeProvider([
        call("write_file", {"path": str(f), "content": "x"}), AIMessage(content="ok")])
    ui = FakeUI()
    Agent(provider, builtin_tools(), ui, AgentConfig(auto_execute=True)).run("write it")
    assert f.read_text() == "x"
    assert ("confirm", "write_file") not in ui.events


def test_edit_requires_unique_match(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("aa")
    provider = FakeProvider([
        call("edit_file", {"path": str(f), "old_text": "a", "new_text": "b"}),
        AIMessage(content="ok")])
    agent = Agent(provider, builtin_tools(), FakeUI(), AgentConfig(auto_execute=True))
    agent.run("edit")
    assert f.read_text() == "aa"  # ambiguous edit rejected
    assert "appears 2 times" in agent.messages[-2].content


def test_unknown_tool_is_reported_not_crashed():
    provider = FakeProvider([call("nope", {}), AIMessage(content="ok")])
    agent = Agent(provider, builtin_tools(), FakeUI())
    agent.run("x")
    assert "unknown tool" in agent.messages[-2].content


class FlakyProvider(FakeProvider):
    """Raises on the first call, then behaves normally."""
    def chat(self, messages, tools, on_token=None):
        if not getattr(self, "failed", False):
            self.failed = True
            raise RuntimeError("Failed to parse tool call arguments as JSON")
        return super().chat(messages, tools, on_token)


def test_provider_error_is_retried():
    ui = FakeUI()
    agent = Agent(FlakyProvider([AIMessage(content="recovered")]), builtin_tools(), ui)
    assert agent.run("x") == "recovered"
    assert any(e[0] == "notice" and "retrying" in e[1] for e in ui.events)


def test_provider_error_gives_up_after_retries():
    class AlwaysFails(FakeProvider):
        def chat(self, *a, **k):
            raise RuntimeError("boom")
    agent = Agent(AlwaysFails([]), builtin_tools(), FakeUI(), AgentConfig(provider_retries=1))
    assert "kept failing" in agent.run("x")


def test_system_prompt_contains_working_directory():
    import os
    agent = Agent(FakeProvider([]), builtin_tools(), FakeUI())
    assert os.getcwd() in agent.messages[0].content


def test_max_iterations_guard():
    provider = FakeProvider([call("run_shell", {"command": "true"}, id=str(i)) for i in range(5)])
    ui = FakeUI()
    agent = Agent(provider, builtin_tools(), ui, AgentConfig(max_iterations=3, auto_execute=True))
    assert "max iterations" in agent.run("loop forever")
    assert any(e[0] == "notice" for e in ui.events)


def test_rate_limit_wait_parsing():
    from codemax.agent.loop import rate_limit_wait
    assert rate_limit_wait(RuntimeError("boom")) is None
    assert rate_limit_wait(RuntimeError("429 Rate limit reached. Please try again in 6.5s.")) == 7.5
    assert rate_limit_wait(RuntimeError("rate limit ... try again in 500ms")) == 1.5
    assert rate_limit_wait(RuntimeError("rate limit ... try again in 5m2.0s")) == 30  # capped


def test_long_tool_results_are_truncated():
    from codemax.tools.base import Tool, MAX_RESULT_CHARS
    t = Tool("big", "d", {"type": "object", "properties": {}}, lambda: "x" * 20000)
    assert len(t.run({})) < MAX_RESULT_CHARS + 100

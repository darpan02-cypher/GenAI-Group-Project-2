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


def test_max_iterations_guard():
    provider = FakeProvider([call("run_shell", {"command": "true"}, id=str(i)) for i in range(5)])
    ui = FakeUI()
    agent = Agent(provider, builtin_tools(), ui, AgentConfig(max_iterations=3, auto_execute=True))
    assert "max iterations" in agent.run("loop forever")
    assert any(e[0] == "notice" for e in ui.events)

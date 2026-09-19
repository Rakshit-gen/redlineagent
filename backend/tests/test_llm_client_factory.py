import json
import os
from unittest import mock

from app.llm import MockLLMClient
from app.openai_client import OpenAIClient, get_llm_client


def test_defaults_to_mock_without_api_key():
    with mock.patch.dict(os.environ, {}, clear=True):
        assert isinstance(get_llm_client(), MockLLMClient)


def test_uses_real_client_when_api_key_present():
    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        assert isinstance(get_llm_client(), OpenAIClient)


def test_openai_client_requires_a_key():
    with mock.patch.dict(os.environ, {}, clear=True):
        try:
            OpenAIClient()
            assert False, "expected KeyError"
        except KeyError:
            pass


def _fake_response(body: dict):
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(body).encode()

    return _Resp()


def test_next_action_parses_a_tool_call():
    client = OpenAIClient(api_key="test-key")
    response_body = {
        "choices": [
            {
                "message": {
                    "content": None,
                    "tool_calls": [
                        {"function": {"name": "search_clause", "arguments": json.dumps({"topic": "auto_renewal"})}}
                    ],
                }
            }
        ]
    }
    with mock.patch("urllib.request.urlopen", return_value=_fake_response(response_body)):
        action = client.next_action(vendor_name="Acme", topics=["auto_renewal"], policy_rules={}, history=[])

    assert action.tool_name == "search_clause"
    assert action.tool_args == {"topic": "auto_renewal"}
    assert not action.done


def test_next_action_treats_plain_text_reply_as_done():
    client = OpenAIClient(api_key="test-key")
    response_body = {"choices": [{"message": {"content": "All topics checked.", "tool_calls": []}}]}
    with mock.patch("urllib.request.urlopen", return_value=_fake_response(response_body)):
        action = client.next_action(vendor_name="Acme", topics=["auto_renewal"], policy_rules={}, history=[])

    assert action.tool_name is None
    assert action.done

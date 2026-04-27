from vibe_tool.templates import (
    get_hook_pre_session,
    get_hook_post_session,
    get_hook_post_commit,
)


def test_pre_session_hook_syncs_and_generates_context():
    content = get_hook_pre_session()
    assert "vibe sync pull" in content
    assert "session-context" in content or "preloader" in content


def test_post_session_hook_generates_handoff_and_syncs():
    content = get_hook_post_session()
    assert "handoff" in content
    assert "vibe sync push" in content


def test_post_commit_hook_updates_index():
    content = get_hook_post_commit()
    assert "vibe index" in content

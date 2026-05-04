#!/usr/bin/env python3
"""
Benchmark Audit Scanner — collects structural data from a run to assist
the benchmark-audit skill evaluation.

Usage:
    python scripts/benchmark_audit_scan.py ../../results/<slug>
    # or from project root:
    python .agents/skills/benchmark-audit/scripts/benchmark_audit_scan.py results/<slug>

Output: JSON with structural metrics (artifacts, tests, gems, RubyLLM patterns).
"""

import json
import os
import re
import sys
from pathlib import Path


def find_files(root: Path, pattern: str) -> list[Path]:
    return list(root.rglob(pattern))


def read_file(path: Path, max_bytes: int = 500_000) -> str | None:
    try:
        return path.read_text(errors="ignore")[:max_bytes]
    except Exception:
        return None


def count_test_methods(test_dir: Path) -> dict:
    """Count test files and test methods."""
    files = list(test_dir.rglob("*_test.rb"))
    total_methods = 0
    for f in files:
        text = read_file(f)
        if text:
            # test "name" do ... end  or  def test_something
            total_methods += len(re.findall(r'\btest\s+["\']', text))
            total_methods += len(re.findall(r'\bdef\s+test_\w+', text))
    return {"files": len(files), "methods": total_methods}


def scan_gemfile(gemfile_path: Path) -> dict:
    """Extract relevant gems from the Gemfile."""
    text = read_file(gemfile_path) or ""
    gems = {
        "ruby_llm": bool(re.search(r'gem\s+["\']ruby_llm["\']', text)),
        "ruby_openai": bool(re.search(r'gem\s+["\']ruby-openai["\']', text)),
        "turbo_rails": bool(re.search(r'gem\s+["\']turbo-rails["\']', text)),
        "stimulus_rails": bool(re.search(r'gem\s+["\']stimulus-rails["\']', text)),
        "tailwindcss_rails": bool(re.search(r'gem\s+["\']tailwindcss-rails["\']', text)),
        "brakeman": bool(re.search(r'gem\s+["\']brakeman["\']', text)),
        "rubocop": bool(re.search(r'gem\s+["\']rubocop', text)),
        "simplecov": bool(re.search(r'gem\s+["\']simplecov["\']', text)),
        "bundle_audit": bool(re.search(r'gem\s+["\']bundler-audit["\']', text)),
        "mocha": bool(re.search(r'gem\s+["\']mocha["\']', text)),
        "webmock": bool(re.search(r'gem\s+["\']webmock["\']', text)),
    }
    # attempt to extract ruby version
    ruby_version_match = re.search(r'^\s*ruby\s+["\']([^"\']+)["\']', text, re.MULTILINE)
    ruby_version = ruby_version_match.group(1) if ruby_version_match else None
    return {"gems": gems, "ruby_version": ruby_version}


def scan_dockerfile(dockerfile_path: Path) -> dict:
    """Check Dockerfile for common issues."""
    text = read_file(dockerfile_path) or ""
    # extract FROM ruby:X
    from_match = re.search(r'FROM\s+ruby:([\d.]+)', text, re.IGNORECASE)
    ruby_version = from_match.group(1) if from_match else None
    has_secretkey = "SECRET_KEY_BASE" in text or "secret_key_base" in text
    return {"ruby_version": ruby_version, "has_secret_key_base": has_secretkey}


def scan_readme(readme_path: Path) -> dict:
    """Check whether the README has real content or is a stock template."""
    text = read_file(readme_path) or ""
    stock_phrases = [
        "This README would normally document",
        "This README.md file was generated",
        "Please feel free to use a different markup language",
    ]
    is_stock = any(p in text for p in stock_phrases)
    word_count = len(text.split())
    return {"is_stock_template": is_stock, "word_count": word_count, "has_content": word_count > 50}


def scan_rubyllm_patterns(project_dir: Path) -> dict:
    """Search for RubyLLM patterns in app code."""
    patterns = {
        "valid_entry_chat": re.compile(r'RubyLLM\.chat\('),
        "valid_entry_chat_new": re.compile(r'RubyLLM::Chat\.new\('),
        "valid_ask": re.compile(r'\.ask\('),
        "valid_content": re.compile(r'\.content\b'),
        "valid_add_message": re.compile(r'\.add_message\('),
        "valid_complete": re.compile(r'\.complete\('),
        "valid_with_instructions": re.compile(r'\.with_instructions\('),
        "hallucinated_client": re.compile(r'RubyLLM::Client\.new'),
        "hallucinated_text_accessor": re.compile(r'response\.text\b|\.output_text\b'),
        "hallucinated_user_dsl": re.compile(r'chat\.user\(|\.user\("|\suser\('),
        "hallucinated_assistant_dsl": re.compile(r'chat\.assistant\(|\.assistant\("'),
        "hallucinated_batch": re.compile(r'RubyLLM\.chat\s*\(\s*messages:'),
        "hallucinated_openrouter_client": re.compile(r'Openrouter::Client'),
        "bypass_ruby_openai": re.compile(r'OpenAI::Client\.new'),
    }
    results = {key: [] for key in patterns}
    ruby_files = list(project_dir.rglob("*.rb"))
    for f in ruby_files:
        text = read_file(f, max_bytes=200_000)
        if not text:
            continue
        for key, pat in patterns.items():
            for m in pat.finditer(text):
                line = text[:m.start()].count("\n") + 1
                results[key].append(f"{f.relative_to(project_dir)}:{line}")
    # summary
    summary = {k: len(v) for k, v in results.items()}
    summary["locations"] = {k: v for k, v in results.items() if v}
    return summary


def scan_test_mocks(test_dir: Path) -> dict:
    """Check whether tests contain mocks/stubs."""
    files = list(test_dir.rglob("*_test.rb"))
    has_mocha = False
    has_webmock = False
    has_minitest_mock = False
    has_fake_chat = False
    has_method_stubbing = False
    has_any_mock = False
    mock_locations = []
    for f in files:
        text = read_file(f)
        if not text:
            continue
        for m in re.finditer(r'\b(Mocha|WebMock|MiniTest::Mock|FakeChat|any_instance|stubs?|expects|define_method|instance_method)\b', text):
            line = text[:m.start()].count("\n") + 1
            mock_locations.append(f"{f.name}:{line}")
        if "mocha" in text.lower():
            has_mocha = True
        if "webmock" in text.lower():
            has_webmock = True
        if "Minitest::Mock" in text or "MiniTest::Mock" in text:
            has_minitest_mock = True
        if "FakeChat" in text:
            has_fake_chat = True
        if "instance_method" in text and "define_method" in text:
            has_method_stubbing = True
        # detect any mock/stub pattern (exclude comments and generic strings)
        if re.search(r'\b(stub|mock|fake|double|spy)\b', text, re.IGNORECASE):
            has_any_mock = True
    return {
        "has_mocha": has_mocha,
        "has_webmock": has_webmock,
        "has_minitest_mock": has_minitest_mock,
        "has_fake_chat": has_fake_chat,
        "has_method_stubbing": has_method_stubbing,
        "has_any_mock": has_any_mock,
        "locations": mock_locations[:20],  # cap at 20
    }


def scan_error_handling(project_dir: Path) -> dict:
    """Search for rescue blocks around LLM calls (controllers and services only)."""
    rescues = []
    for subdir in ("app/controllers", "app/services"):
        target = project_dir / subdir
        if not target.exists():
            continue
        for f in target.rglob("*.rb"):
            text = read_file(f, max_bytes=200_000)
            if not text:
                continue
            for m in re.finditer(r'rescue\s+', text):
                line = text[:m.start()].count("\n") + 1
                rescues.append(f"{f.relative_to(project_dir)}:{line}")
    return {"rescue_count": len(rescues), "locations": rescues[:20]}


def scan_nested_subdirectory(project_dir: Path) -> dict:
    """Check whether the app was generated inside a nested subdirectory."""
    app_dirs = list(project_dir.glob("*/app"))
    for d in app_dirs:
        if d.relative_to(project_dir).parts[0] not in ("app", "test", "config", "db", "lib", "public", "vendor", "tmp", "log", "storage", "coverage"):
            return {"nested": True, "subdir": d.relative_to(project_dir).parts[0]}
    return {"nested": False, "subdir": None}


def scan_env_committed(project_dir: Path) -> dict:
    """Check whether .env or secret files are committed."""
    env_files = list(project_dir.glob(".env*")) + list(project_dir.glob("**/.env*"))
    # exclude .env.example if it is documentation
    env_files = [f for f in env_files if not f.name.endswith(".example") and not f.name.endswith(".sample")]
    return {"has_env_committed": bool(env_files), "files": [str(f.relative_to(project_dir)) for f in env_files[:10]]}


def scan_csrf(project_dir: Path) -> dict:
    """Check whether CSRF was disabled globally."""
    controllers = list((project_dir / "app/controllers").rglob("*.rb")) if (project_dir / "app/controllers").exists() else []
    global_skips = []
    for f in controllers:
        text = read_file(f)
        if not text:
            continue
        for m in re.finditer(r'skip_before_action\s+:verify_authenticity_token', text):
            line = text[:m.start()].count("\n") + 1
            # check for restrictions (only:, except:) on the same line or nearby
            snippet = text[m.start():m.start()+200]
            if "only:" not in snippet and "except:" not in snippet:
                global_skips.append(f"{f.relative_to(project_dir)}:{line}")
    return {"csrf_globally_disabled": bool(global_skips), "locations": global_skips[:10]}


def scan_sanitize(project_dir: Path) -> dict:
    """Check for sanitize: false in LLM output views."""
    views = list((project_dir / "app/views").rglob("*.erb")) if (project_dir / "app/views").exists() else []
    bad_sanitizes = []
    for f in views:
        text = read_file(f)
        if not text:
            continue
        for m in re.finditer(r'sanitize:\s*false', text):
            line = text[:m.start()].count("\n") + 1
            bad_sanitizes.append(f"{f.relative_to(project_dir)}:{line}")
    return {"has_unsafe_sanitize": bool(bad_sanitizes), "locations": bad_sanitizes[:10]}


def scan_initializer(project_dir: Path) -> dict:
    """Check for the presence of ruby_llm.rb initializer."""
    init = project_dir / "config/initializers/ruby_llm.rb"
    return {"has_ruby_llm_initializer": init.exists()}


def scan_turbo_fetch_antipattern(project_dir: Path) -> dict:
    """Check whether fetch + innerHTML is used instead of Turbo Streams."""
    js_files = list((project_dir / "app/javascript").rglob("*.js")) if (project_dir / "app/javascript").exists() else []
    bad_patterns = []
    for f in js_files:
        text = read_file(f)
        if not text:
            continue
        if "fetch(" in text and "innerHTML" in text:
            bad_patterns.append(str(f.relative_to(project_dir)))
    return {"uses_fetch_innerhtml": bool(bad_patterns), "files": bad_patterns[:10]}


def scan_model_slug(project_dir: Path) -> dict:
    """Check whether the configured model slug is the latest Claude Sonnet."""
    init = project_dir / "config/initializers/ruby_llm.rb"
    if not init.exists():
        return {"model_slug": None, "is_latest_claude": False}
    text = read_file(init) or ""
    match = re.search(r'["\']([^"\']*claude[^"\']*)["\']', text, re.IGNORECASE)
    slug = match.group(1) if match else None
    # latest expected: anthropic/claude-sonnet-4 or similar 4.x variant
    is_latest = bool(slug and re.search(r'sonnet-4', slug, re.IGNORECASE))
    return {"model_slug": slug, "is_latest_claude": is_latest}


def scan_no_active_record(project_dir: Path) -> dict:
    """Check whether Active Record configs were removed."""
    database_yml = project_dir / "config/database.yml"
    # if database.yml exists and is not commented out, AR is likely still present
    has_database_yml = database_yml.exists()
    application_rb = project_dir / "config/application.rb"
    ar_comment = False
    if application_rb.exists():
        text = read_file(application_rb) or ""
        ar_comment = "require \"rails/all\"" in text or "require 'rails/all'" in text
    return {"has_database_yml": has_database_yml, "requires_rails_all": ar_comment}


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/benchmark_audit_scan.py results/<slug>", file=sys.stderr)
        sys.exit(1)

    result_dir = Path(sys.argv[1])
    result_json = result_dir / "result.json"
    project_dir = result_dir / "project"

    if not result_json.exists():
        print(json.dumps({"error": f"result.json not found in {result_dir}"}))
        sys.exit(1)

    result = json.loads(result_json.read_text())
    summary = result.get("project_summary", {})
    present = summary.get("present", {})

    # structural artifacts
    artifacts = {
        "result_status": result.get("status"),
        "finish_reason": result.get("finish_reason"),
        "file_count": summary.get("file_count", 0),
        "works_as_intended": summary.get("works_as_intended"),
        "elapsed_seconds": result.get("elapsed_seconds"),
        "gemfile": present.get("gemfile", False),
        "dockerfile": present.get("dockerfile", False),
        "docker_compose": present.get("docker_compose_yml", False) or present.get("docker_compose_yaml", False),
        "readme": present.get("readme_md", False),
        "routes": present.get("routes", False),
        "app_dir": present.get("app_dir", False),
        "views_dir": present.get("views_dir", False),
        "tests_dir": present.get("tests_dir", False),
    }

    # if project dir doesn't exist, return only the basic metadata
    if not project_dir.exists():
        print(json.dumps({"artifacts": artifacts, "project_exists": False}, indent=2))
        return

    gemfile = project_dir / "Gemfile"
    dockerfile = project_dir / "Dockerfile"
    readme = project_dir / "README.md"
    test_dir = project_dir / "test"
    app_dir = project_dir / "app"

    output = {
        "artifacts": artifacts,
        "project_exists": True,
        "gemfile": scan_gemfile(gemfile) if gemfile.exists() else None,
        "dockerfile": scan_dockerfile(dockerfile) if dockerfile.exists() else None,
        "readme": scan_readme(readme) if readme.exists() else None,
        "tests": count_test_methods(test_dir) if test_dir.exists() else {"files": 0, "methods": 0},
        "test_mocks": scan_test_mocks(test_dir) if test_dir.exists() else None,
        "rubyllm_patterns": scan_rubyllm_patterns(app_dir) if app_dir.exists() else None,
        "error_handling": scan_error_handling(project_dir) if app_dir.exists() else None,
        "nested_subdir": scan_nested_subdirectory(project_dir),
        "env_committed": scan_env_committed(project_dir),
        "csrf": scan_csrf(project_dir),
        "sanitize": scan_sanitize(project_dir),
        "initializer": scan_initializer(project_dir),
        "turbo_fetch_antipattern": scan_turbo_fetch_antipattern(project_dir),
        "model_slug": scan_model_slug(project_dir),
        "active_record_cleanup": scan_no_active_record(project_dir),
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

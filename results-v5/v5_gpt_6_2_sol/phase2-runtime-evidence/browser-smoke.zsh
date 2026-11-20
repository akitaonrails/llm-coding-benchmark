#!/usr/bin/env zsh
set -eu

evidence="${0:A:h}"
browser() {
  agent-browser --config "$evidence/browser-config.json" --session stillwater-phase2-gpt62sol "$@"
}
base=http://127.0.0.1:13682
curl -fsS -o /dev/null -w 'App health HTTP %{http_code}\n' "$base/up"
curl -fsS -o /dev/null -w 'Favicon HTTP %{http_code} %{content_type}\n' "$base/icon.svg"
browser --executable-path /usr/bin/chromium --headed false open "$base/"
browser wait --fn 'document.querySelector("turbo-cable-stream-source")?.hasAttribute("connected") === true'
browser snapshot -i
browser eval '(() => {
  window.runtimeSmoke = {frames: []};
  document.addEventListener("turbo:before-stream-render", ({target}) => {
    if (target.getAttribute("action") === "append" && /_reply$/.test(target.getAttribute("target"))) {
      window.runtimeSmoke.frames.push(performance.now());
    }
  });
  document.addEventListener("turbo:submit-start", () => {
    window.runtimeSmoke.started = performance.now();
  });
  document.addEventListener("turbo:submit-end", ({detail}) => {
    window.runtimeSmoke.submitted = {
      success: detail.success,
      status: detail.fetchResponse?.statusCode,
      at: performance.now()
    };
  });
  return true;
})()'
browser fill 'textarea[name=prompt]' "In three short sentences, explain why the sky looks blue. Start with the words Rayleigh scattering."
browser click 'button[aria-label="Send message"]'
browser wait --fn 'window.runtimeSmoke?.submitted?.status === 200 && /Rayleigh scattering/i.test(document.querySelector("#chat_messages .reply-text")?.textContent ?? "")'
browser eval '(() => {
  const {frames, started, submitted} = window.runtimeSmoke;
  const beforePost = frames.filter(at => at < submitted.at);
  if (beforePost.length < 2 || !submitted.success) throw new Error("Expected incremental browser updates and a successful POST");
  return {
    http: submitted.status,
    cableReplyAppendsBeforePost: beforePost.length,
    firstReplyAppendMs: Math.round(beforePost[0] - started),
    postMs: Math.round(submitted.at - started),
    title: document.querySelector("#conversation_title").textContent,
    reply: document.querySelector("#chat_messages .reply-text").innerText
  };
})()'
browser reload
browser wait --fn 'document.querySelector("turbo-cable-stream-source")?.hasAttribute("connected") === true'
browser wait --fn '/Rayleigh scattering/i.test(document.querySelector("#chat_messages .reply-text")?.textContent ?? "")'
browser get text '#chat_messages'
browser errors

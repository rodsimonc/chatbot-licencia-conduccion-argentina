/* Embeddable chat widget: "Argentina Driving License".
 * Use it on any page:
 *   <script src="https://YOUR-SERVER/widget.js" data-api="https://YOUR-SERVER" defer></script>
 */
(function () {
  var script = document.currentScript;
  var API = (script && script.getAttribute('data-api')) || window.location.origin;
  var TITLE = (script && script.getAttribute('data-title')) || 'Argentina Driving License';

  var CSS = `
  .lca-btn{position:fixed;bottom:22px;right:22px;width:60px;height:60px;border-radius:50%;
    background:#2f6fed;color:#fff;border:none;cursor:pointer;box-shadow:0 8px 24px rgba(0,0,0,.22);
    font-size:26px;z-index:2147483000;display:flex;align-items:center;justify-content:center}
  .lca-btn:hover{background:#2559c9}
  .lca-panel{position:fixed;bottom:94px;right:22px;width:370px;max-width:calc(100vw - 44px);
    height:520px;max-height:calc(100vh - 130px);background:#fff;border-radius:16px;z-index:2147483000;
    box-shadow:0 18px 50px rgba(0,0,0,.28);display:none;flex-direction:column;overflow:hidden;
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
  .lca-panel.open{display:flex}
  .lca-head{background:#2f6fed;color:#fff;padding:14px 16px;font-weight:600;display:flex;
    align-items:center;justify-content:space-between}
  .lca-head small{display:block;font-weight:400;opacity:.85;font-size:.75rem;margin-top:2px}
  .lca-x{background:none;border:none;color:#fff;font-size:20px;cursor:pointer;line-height:1}
  .lca-msgs{flex:1;overflow-y:auto;padding:14px;background:#f6f8fc}
  .lca-msg{margin-bottom:12px;display:flex}
  .lca-msg.user{justify-content:flex-end}
  .lca-bubble{max-width:82%;padding:10px 13px;border-radius:14px;font-size:.9rem;line-height:1.45;white-space:pre-wrap}
  .lca-msg.bot .lca-bubble{background:#fff;border:1px solid #e6e9ef;border-bottom-left-radius:4px;color:#1e2430}
  .lca-msg.user .lca-bubble{background:#2f6fed;color:#fff;border-bottom-right-radius:4px}
  .lca-src{font-size:.72rem;color:#7a8699;margin-top:6px}
  .lca-typing{color:#7a8699;font-size:.85rem;font-style:italic}
  .lca-input{display:flex;gap:8px;padding:10px;border-top:1px solid #eef0f4;background:#fff}
  .lca-input input{flex:1;border:1px solid #dfe3ea;border-radius:10px;padding:10px 12px;font:inherit;font-size:.9rem;outline:none}
  .lca-input input:focus{border-color:#2f6fed}
  .lca-input button{background:#2f6fed;color:#fff;border:none;border-radius:10px;padding:0 15px;cursor:pointer;font-weight:600}
  .lca-input button:disabled{opacity:.5;cursor:default}
  .lca-foot{font-size:.68rem;color:#9aa4b5;text-align:center;padding:6px}
  `;

  function el(html) { var d = document.createElement('div'); d.innerHTML = html.trim(); return d.firstChild; }

  var style = document.createElement('style'); style.textContent = CSS; document.head.appendChild(style);

  var btn = el('<button class="lca-btn" aria-label="Open chat">💬</button>');
  var panel = el(
    '<div class="lca-panel" role="dialog" aria-label="' + TITLE + '">' +
      '<div class="lca-head"><div>' + TITLE + '<small>Questions about the Driver\'s Manual (ANSV)</small></div>' +
        '<button class="lca-x" aria-label="Close">×</button></div>' +
      '<div class="lca-msgs"></div>' +
      '<div class="lca-input"><input type="text" placeholder="Type your question…" ' +
        'aria-label="Your question"><button>Send</button></div>' +
      '<div class="lca-foot">Answers based on the manual. May contain errors.</div>' +
    '</div>'
  );
  document.body.appendChild(btn); document.body.appendChild(panel);

  var msgs = panel.querySelector('.lca-msgs');
  var input = panel.querySelector('input');
  var sendBtn = panel.querySelector('.lca-input button');
  var started = false;

  function open() {
    panel.classList.add('open');
    if (!started) { started = true; addBot('Hi! I am the ' + TITLE + ' assistant. Ask me anything about the Driver\'s Manual: licenses, road safety, documentation, signs, etc.'); }
    input.focus();
  }
  function close() { panel.classList.remove('open'); }
  btn.addEventListener('click', function () { panel.classList.contains('open') ? close() : open(); });
  panel.querySelector('.lca-x').addEventListener('click', close);

  function addMsg(text, who, sources) {
    var wrap = el('<div class="lca-msg ' + who + '"><div class="lca-bubble"></div></div>');
    wrap.querySelector('.lca-bubble').textContent = text;
    if (sources && sources.length) {
      var s = el('<div class="lca-src"></div>');
      s.textContent = '📄 Manual, page' + (sources.length > 1 ? 's ' : ' ') + sources.join(', ');
      wrap.querySelector('.lca-bubble').appendChild(s);
    }
    msgs.appendChild(wrap); msgs.scrollTop = msgs.scrollHeight;
    return wrap;
  }
  function addBot(t, s) { return addMsg(t, 'bot', s); }
  function addUser(t) { return addMsg(t, 'user'); }

  async function send() {
    var q = input.value.trim(); if (!q) return;
    addUser(q); input.value = ''; input.disabled = true; sendBtn.disabled = true;
    var typing = el('<div class="lca-msg bot"><div class="lca-bubble"><span class="lca-typing">Typing…</span></div></div>');
    msgs.appendChild(typing); msgs.scrollTop = msgs.scrollHeight;
    try {
      var res = await fetch(API.replace(/\/$/, '') + '/api/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: q })
      });
      var data = await res.json();
      typing.remove();
      addBot(data.answer || 'I could not answer that.', data.sources || []);
    } catch (e) {
      typing.remove();
      addBot('I could not connect to the server. Check that the chatbot is running.');
    } finally {
      input.disabled = false; sendBtn.disabled = false; input.focus();
    }
  }
  sendBtn.addEventListener('click', send);
  input.addEventListener('keydown', function (e) { if (e.key === 'Enter') send(); });

  // Allow configuring the title from the backend (optional).
  fetch(API.replace(/\/$/, '') + '/api/info').then(function (r) { return r.json(); })
    .then(function (d) { if (d && d.botName) { panel.querySelector('.lca-head div').firstChild.textContent = d.botName; } })
    .catch(function () {});
})();

# Runbook page mechanics

Working code for the two interactive pieces every easy-mode page needs. Adapt
the styling freely — the design should suit the subject, per `artifact-design`.
What matters here is the behavior, which is easy to get subtly wrong.

## Copy buttons

### Markup

Put the value in a `<pre><code>` with an id, and a button carrying `data-copy`
pointing at that id:

```html
<div class="copybox">
<pre><code id="var-provider">projects/123456/locations/global/workloadIdentityPools/gh/providers/oidc</code></pre>
  <button class="copybtn" type="button" data-copy="var-provider">Copy</button>
</div>
```

Open the `<pre>` at column zero. Indenting it puts leading whitespace inside the
element, and that whitespace ends up in what gets copied.

### The CSS that protects the copy

```css
.copybox pre {
  overflow-x: auto;      /* long values scroll, they do not wrap */
  padding-bottom: 2.6rem; /* room for the button to sit inside */
}
.copybox code {
  white-space: pre;      /* critical: no soft wrapping */
}
```

`white-space: pre` with `overflow-x: auto` is the combination that keeps a long
single-line value single-line. If it soft-wraps instead, a user who selects the
text by hand gets line breaks in the middle of the value.

### The JavaScript

Clipboard access can be denied outright, so degrade twice: the async API, then
`execCommand`, then tell the user to select it manually. Silent failure is the
one outcome to avoid — they'd paste whatever was in the clipboard before.

```js
document.querySelectorAll(".copybtn").forEach(function (btn) {
  btn.addEventListener("click", function () {
    var text = document.getElementById(btn.dataset.copy).innerText;

    function done(ok) {
      btn.textContent = ok ? "Copied" : "Select manually";
      btn.classList.toggle("copied", ok);
      setTimeout(function () {
        btn.textContent = "Copy";
        btn.classList.remove("copied");
      }, 2000);
    }

    function fallback() {
      try {
        var ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        var ok = document.execCommand("copy");
        document.body.removeChild(ta);
        done(ok);
      } catch (e) {
        done(false);
      }
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { done(true); }, fallback);
    } else {
      fallback();
    }
  });
});
```

## Progress that survives leaving the page

`localStorage` throws in some contexts, not just returns empty — private windows,
blocked site data, thumbnail capture. Wrap every read and write, and render
correctly when there is no stored value.

```js
var KEY = "runbook-progress-v1";   // version it; a restructured page invalidates old state
var steps = Array.prototype.slice.call(document.querySelectorAll("li.step"));

function load() {
  try {
    var raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : {};
  } catch (e) {
    return {};
  }
}

function save(state) {
  try {
    localStorage.setItem(KEY, JSON.stringify(state));
  } catch (e) {
    /* progress just will not persist; the page still works */
  }
}

var state = load();

function render() {
  var done = 0;
  steps.forEach(function (li) {
    var on = !!state[li.dataset.id];
    if (on) done++;
    li.classList.toggle("done", on);
    li.querySelector(".step-head").setAttribute("aria-pressed", on ? "true" : "false");
    li.querySelector(".tick").textContent = on ? "✓" : String(steps.indexOf(li) + 1);
  });
  document.getElementById("fill").style.width = (done / steps.length * 100) + "%";
  document.getElementById("label").textContent = done + " / " + steps.length;
}

steps.forEach(function (li) {
  var head = li.querySelector(".step-head");
  function toggle() {
    state[li.dataset.id] = !state[li.dataset.id];
    save(state);
    render();
  }
  head.addEventListener("click", toggle);
  head.addEventListener("keydown", function (e) {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); }
  });
});

render();
```

Key state on a stable `data-id` per step rather than array position, so inserting
a step later doesn't silently shift everyone's saved progress onto the wrong rows.

Make the whole step header the toggle target — `role="button"`, `tabindex="0"`,
`aria-pressed` — rather than a small checkbox. Thumbs are imprecise.

## Verifying before publish

Extract each copy block the way `innerText` would produce it and check the
result. For a script:

```python
import html, re
src = open("runbook.html").read()
block = html.unescape(re.search(r'<code id="my-script">(.*?)</code>', src, re.S).group(1))
open("check.sh", "w").write(block)
# then: bash -n check.sh
```

If the block wraps an inner heredoc, check that inner script too — `bash -n` on
the outer paste treats heredoc contents as data and will happily pass a script
with a syntax error inside it.

For a single value, assert what you actually depend on:

```python
assert "\n" not in value and " " not in value, repr(value)
```

---
name: easy-mode
description: Turn a multi-step manual procedure into a published, tap-to-copy checklist the user can work through on their phone. Use this whenever the user has to do things by hand that you cannot do for them — clicking through cloud consoles, pasting commands into a shell, setting secrets in a dashboard, DNS records, one-time account setup — and especially when they say they are on mobile, ask you to "walk me through" something, ask for "the steps", or ask you to make something easy. Also use it when you are about to end a turn with a numbered list of manual steps in chat: that list is the trigger, not a substitute.
---

Some work you cannot finish for the user. Provisioning a cloud identity, pasting a secret into a dashboard, approving a billing prompt — these need their hands and their credentials. What you hand over at that boundary is the deliverable, and a numbered list in a terminal is a poor one. It scrolls away, it can't be tapped, and it makes them retype values you already know.

Easy mode replaces that list with a published page: every command one tap to copy, every link opening the exact console page, progress that survives putting the phone down.

## The one rule that matters most

**Never make the user transcribe something you can compute.**

This is where handoffs actually break. A 97-character resource identifier printed into a terminal that wraps at 60 columns is a trap: copying across the wrap drags in a line break, mid-word, invisible. The system then rejects it with an error about the value's *format*, which reads like a configuration problem and sends the user hunting in the wrong place.

So before writing a step that says "paste the value it printed", stop and ask whether you can determine that value yourself — from config files in the repo, from earlier command output in the conversation, from the project's own identifiers. Usually you can. Then put the finished string in a copy block and let the terminal output be confirmation rather than a source.

When a value genuinely can't be known ahead of time (a generated token, something only their console will show), say explicitly that it must be pasted as a single line with no spaces or breaks, and name the error they'll see if it isn't.

## Pick the easiest route, not the most pasteable one

The page exists to make the procedure easy. It does not exist to make everything
a copy block, and those two goals come apart more often than you would expect.

Plenty of console tasks are genuinely trivial in the UI — click *Add site*, type
a name, click *Create* — and genuinely awkward from a shell, needing a CLI
install, an auth flow, a project flag and an incantation that fails in ways the
UI simply doesn't have. Reaching for the command line there produces a longer,
more fragile step that is *worse* for the person following it, purely because a
command is something you can put a Copy button on. That is the tail wagging the
dog.

So for each step, ask which route you would honestly tell a friend to take, then
write that one. "Open this page, click *Add another site*, enter
`a9-tracker`" is an excellent step: it is one deep link, one button and one copy
block for the only part worth copying.

The command line earns its place when it is genuinely better: many operations at
once, something with no UI at all, exact values that are painful to type
correctly, or anything worth re-running identically later. A single form with
two fields is none of those.

A good tell is length. If the shell version of a step needs installs, flags and
error handling to do what three taps would do, the UI is the answer and the
elaborate script was you optimizing for the format instead of the person.

## What the page needs to do

Build it as an artifact, following `artifact-design` like any other page. These are the functional requirements on top of that; `references/mechanics.md` has the copy-button and progress-persistence code, which is fiddly enough to be worth not rewriting.

**Tap to copy, and make the copy clean.** Every command and every value gets a copy button. Render them in `<pre>` with `white-space: pre` so a long value scrolls sideways rather than wrapping — wrapped text can leak line breaks into what gets copied. Clipboard access can be blocked, so fall back to `execCommand` and then to telling the user to select manually.

**One paste, not twelve.** A sequence of shell commands is a sequence of chances to paste half of one. Wrap the whole thing in a single `cat > script.sh <<'EOF' … EOF` block followed by the run command, so it's one copy, one paste, one return.

**Deep-link every step.** Link to the specific console page — the App Check tab, the Actions secrets page, the exact settings pane — never the product homepage. Finding the right page by navigation is most of the work on a small screen.

**Let them stop and come back.** These procedures span apps and get interrupted. Persist checkbox state to `localStorage` (wrapped in try/catch — it throws in some contexts) and show progress, so a phone call in the middle doesn't cost them their place.

**Number the steps only if order is real.** If step 4 depends on step 3's output, numbering is information. If the steps are independent, numbering is decoration — drop it.

**When a value can't be known, ask for it once.** Sometimes an identifier is genuinely unavailable to you — an account number, a chosen name, a generated id — and it recurs in eight different commands. Rather than leaving eight placeholders for them to edit by hand, put a small "fill this in once" panel at the top: they type it once, and every command, link and code block on the page rewrites to match. Persist those inputs the same way you persist progress.

This is worth reaching for whenever the same unknown appears more than two or three times. Hand-editing a placeholder inside a copied command is precisely the error-prone transcription the page exists to eliminate — and it fails silently, because a command with a stale placeholder still looks plausible. Keep the panel small and put it above the first step, since nothing below it is correct until it's filled.

## Write for the moment of failure

Assume every step will fail for someone. The difference between a good runbook and a bad one is what happens then.

**Put each warning where it fires, not in a preamble.** A caution about a debug token belongs in the debug token step. Nobody re-reads the intro.

**Name the failure signature.** These systems produce misleading errors: a freshly created account reported as *does not exist* because of propagation lag; App Check misconfiguration showing up as an app that loads perfectly and displays no data. Say "if you see X, it means Y" — that sentence saves more time than anything else on the page.

**Say whether re-running is safe.** Make the scripts you hand over idempotent — check before creating, retry on transient failure — and then say so on the page. "Safe to run again" turns a scary error into a shrug.

**Tell them what a good result looks like.** Not just "run it", but what output means it worked, and what to check afterwards.

## Getting it right before publishing

Two checks worth doing every time, because both catch real breakage:

**Verify the copy blocks produce valid content.** Extract each block from the file exactly as `innerText` would yield it, HTML-unescape it, and check it — syntax-check a script with `bash -n`, confirm a value is a single line with no stray whitespace. A page that looks perfect and copies broken text is worse than no page.

**Walk the order once as the user.** Does every value referenced in step 5 exist by step 5? Is anything needed before the first step they'd only discover at step 3? Front-load prerequisites — required permissions especially, since discovering a missing role halfway through means starting over.

## Keeping it alive

The procedure will change as they work through it, and the page is the deliverable — so update and republish it rather than issuing corrections in chat. When they hit an error the page didn't anticipate, fix the page as well as answering the question. That is the difference between a runbook and a transcript.

Give the chat reply the immediate answer — what to do right now, in a sentence or two — and let the page carry the durable version. Don't make them re-read a wall of text to find the one line that unblocks them.

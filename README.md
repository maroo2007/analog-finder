# analog-finder
Finding places on Earth that match the ground on the Moon and Mars. NASA Space Apps 2026.

## Setup

Mac and Linux: use `environment.yml`. Windows: `environment-lock.yml`
reproduces the exact build.

Rebuild the Python environment:

```bash
conda env create -f environment.yml
conda activate analog
```

Check Earth Engine works:

```bash
python src/check_ee.py
```

On a laptop, run `earthengine authenticate` once first. In a cloud container
there is no browser, so set `GEE_SERVICE_ACCOUNT_KEY` to a service account key
instead; `src/config.py` picks whichever is available.

Fresh cloud containers need two extra steps, because the preinstalled
`cryptography` is broken in a way that stops `import ee`:

```bash
pip install --ignore-installed cffi cryptography
pip install earthengine-api
```

`check_ee.py` recognises both failures and prints the fix.

## Chatbot

A Gemini chatbot that answers questions about our results (which places on
Earth match which NASA site, and why) and general background, which it
labels "General background". Every number it gives comes from
`web/public/data/`, through the lookups in `src/chat_data.py`.

Get a Gemini API key from Google AI Studio and put it in an environment
variable, never in a file in this repository. Windows PowerShell:

```powershell
$env:GEMINI_API_KEY = "<your key>"
```

Mac and Linux: `export GEMINI_API_KEY=...`. Then, in the `analog`
environment (or `conda install -n analog google-genai streamlit` on an
environment built before 13 November):

```bash
streamlit run src/chat_app.py    # chat page in the browser
python src/chatbot.py            # or chat in the terminal
```

What the bot knows about the method is in `src/chatbot_knowledge.md`; edit
that file to correct or extend it. `GEMINI_MODEL` forces one model; by
default it tries `gemini-3.8-flash`, then `gemini-3.5-flash`, then
`gemini-3.5-flash-lite`, moving on when one is busy.

## Daily workflow

Every time you start working (Windows PowerShell shown; quote the path, it has
spaces):

```powershell
conda activate analog
cd "C:\Users\Marwan\Desktop\Nasa Space Apps 2026"   # your own clone's folder
git pull
jupyter lab
```

JupyterLab opens in your browser. Stop it with Ctrl+C in the terminal, then
`git push` your work.

## Team workflow

- Run `git pull` before you start work.
- Run `git push` when you're done.
- For bigger changes, work on your own branch (one per person) and open a pull
  request.
- Never commit anything in `data/`, or any key, password or service account
  file.

Setting up a new laptop:

```bash
git clone https://github.com/maroo2007/analog-finder
cd analog-finder
conda env create -f environment.yml
conda activate analog
earthengine authenticate
```

Install the GitHub CLI and log in once, so pull requests can be opened and
merged from the terminal. On Windows (open a new terminal after installing):

```bash
winget install --id GitHub.cli
gh auth login
```

On Mac, `brew install gh`; on Linux, see https://cli.github.com. During
`gh auth login` choose GitHub.com, HTTPS and "Login with a web browser".

On Windows 11, turn off Smart App Control first, or it blocks parts of pandas
and other compiled libraries. See `CLAUDE.md`.

## Third-party code in this repository

`.claude/skills/impeccable/` (and the `impeccable-*` agents in
`.claude/agents/`) is [Impeccable](https://github.com/pbakaus/impeccable) by
Paul Bakaus, used under the Apache License 2.0; its `LICENSE` and
`NOTICE.md` are in that folder. We used it to design the website.

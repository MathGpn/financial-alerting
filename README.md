# financial_alerting
Track SP500, gold, bitcoin crashes

# test the app
- git clone the repo
- Create & fill the `.env` file at the root with the correct values (ask MGN for the credentials) following the ".env.example" template
- uv sync
- source .venv/bin/activate
- uv run main.py

# mise en place du scheduler (2 options)
- github actions (test possible avec le bouton "run workflow" depuis l'interface github)
- mise en place du cronjob (tous les jours à 16h) : `crontab -e` puis `30 15 * * * /usr/bin/python3 ./main.py --- 30 22 * * * /usr/bin/python3 ./main.py`

# coding init
- git clone the repo
- uv init
- uv venv
- source .venv/bin/activate
- uv run main.py
- uv add ... (for every no module named...)

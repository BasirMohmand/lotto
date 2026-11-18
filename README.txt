LottoStat Enterprise 3.15 – Sequential Rolling Number Reveal

This update keeps the game-specific generation button, one-line default,
analytics, backtesting, historical draw data, and saved-ticket database behavior.

Changes:
- The generation button reads GENERATE LOTTO MAX or GENERATE LOTTO 6/49,
  depending on the selected game.
- Numbers roll in from the left, one at a time.
- The complete Statistical Edge selection is revealed first, then Contrarian
  Maximizer, then Statistical Blend.
- The default remains one line per strategy. Ticket values and saved-ticket
  contents are unchanged by the animation.

Install:
1. Extract this ZIP into a NEW folder.
2. Open Command Prompt in that folder.
3. Run: py -m venv .venv
4. Run: .venv\\Scripts\\python.exe -m pip install -r requirements.txt
5. Run: .venv\\Scripts\\python.exe -m streamlit run app.py

Important: Keep your existing app folder and its saved_tickets.sqlite3 file.
This ZIP does not contain a database. To retain previously saved ticket batches
when moving to this folder, copy your existing saved_tickets.sqlite3 file into
the new folder before launching the app.

Lottery numbers are random. Historical analysis does not predict winning numbers.

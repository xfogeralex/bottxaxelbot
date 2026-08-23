AxelBot MAX – PythonAnywhere

1. Załóż konto na https://www.pythonanywhere.com (plan Beginner – FREE).

2. Wejdź w zakładkę "Files" i utwórz folder, np.:
   /home/twoja_nazwa/AxelBot_MAX/

3. Wgraj tam pliki:
   - bot.py
   - requirements.txt
   - README_PythonAnywhere.txt (opcjonalnie)

4. Wejdź w "Consoles" → "Bash" i wpisz:
   pip install --user pyTelegramBotAPI

5. W pliku bot.py:
   - wstaw swój TOKEN w miejsce:
     TOKEN = "TU_WSTAW_TOKEN"
   - upewnij się, że LOG_CHANNEL_ID ma wartość:
     -1004410834577

6. Wejdź w "Tasks" → "Add a new task":
   Command:
     python3 /home/twoja_nazwa/AxelBot_MAX/bot.py
   Type:
     Always-on task

7. Zapisz task – bot będzie działał 24/7.

Restart:
- jeśli zmienisz kod, zatrzymaj task i uruchom go ponownie.

Logi:
- w "Tasks" możesz podejrzeć logi procesu.
- dodatkowo bot wysyła logi moderacji do kanału o ID -1004410834577.

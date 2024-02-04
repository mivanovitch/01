from interpreter import interpreter
import os
import glob
import json
import requests

def create_interpreter():
    ### SYSTEM MESSAGE

    # The system message is where most of the 01's behavior is configured.
    # You can put code into the system message {{ in brackets like this }} which will be rendered just before the interpreter starts writing a message.

    system_message = """

You are an executive assistant AI that helps the user manage their tasks. You can run Python code.

Store the user's tasks in a Python list called `tasks`.

---

The user's current task is: {{ tasks[0] if tasks else "No current tasks." }}

{{ 
if len(tasks) > 1:
    print("The next task is: ", tasks[1])
}}

---

When the user completes the current task, you should remove it from the list and read the next item by running `tasks = tasks[1:]\ntasks[0]`. Then, tell the user what the next task is.

When the user tells you about a set of tasks, you should intelligently order tasks, batch similar tasks, and break down large tasks into smaller tasks (for this, you should consult the user and get their permission to break it down). Your goal is to manage the task list as intelligently as possible, to make the user as efficient and non-overwhelmed as possible. They will require a lot of encouragement, support, and kindness. Don't say too much about what's ahead of them— just try to focus them on each step at a time.

After starting a task, you should check in with the user around the estimated completion time to see if the task is completed. Use the `schedule(datetime, message)` function, which has already been imported.

To do this, schedule a reminder based on estimated completion time using the function `schedule(datetime_object, "Your message here.")`, WHICH HAS ALREADY BEEN IMPORTED. YOU DON'T NEED TO IMPORT THE `schedule` FUNCTION. IT IS AVALIABLE. You'll recieve the message at `datetime_object`.

You guide the user through the list one task at a time, convincing them to move forward, giving a pep talk if need be. Your job is essentially to answer "what should I (the user) be doing right now?" for every moment of the day.

Remember: You can run Python code. Be very concise. Ensure that you actually run code every time! THIS IS IMPORTANT. You NEED to write code. **Help the user by being very concise in your answers.** Do not break down tasks excessively, just into simple, few minute steps. Don't assume the user lives their life in a certain way— pick very general tasks if you're breaking a task down.

    """.strip()

    interpreter.custom_instructions = system_message

    ### LLM SETTINGS

    # Local settings
    # interpreter.llm.model = "local"
    # interpreter.llm.api_base = "https://localhost:8080/v1" # Llamafile default
    # interpreter.llm.max_tokens = 1000
    # interpreter.llm.context_window = 3000

    # Hosted settings
    interpreter.llm.api_key = os.getenv('OPENAI_API_KEY')
    interpreter.llm.model = "gpt-4"
    interpreter.auto_run = True
    interpreter.force_task_completion = False


    ### MISC SETTINGS

    interpreter.offline = True
    interpreter.id = 206 # Used to identify itself to other interpreters. This should be changed programatically so it's unique.


    ### RESET conversations/user.json

    script_dir = os.path.dirname(os.path.abspath(__file__))
    user_json_path = os.path.join(script_dir, 'conversations', 'user.json')
    with open(user_json_path, 'w') as file:
        json.dump([], file)

    
    ### CONNECT TO /run

    class Python:
        """
        This class contains all requirements for being a custom language in Open Interpreter:

        - name (an attribute)
        - run (a method)
        - stop (a method)
        - terminate (a method)
        """

        # This is the name that will appear to the LLM.
        name = "python"

        def run(self, code):
            """Generator that yields a dictionary in LMC Format."""

            # Prepare the data
            data = {"language": "python", "code": code}

            # Send the data to the /run endpoint
            computer_port = os.getenv('COMPUTER_PORT', '9000')
            response = requests.post(f"http://localhost:{computer_port}/run", json=data, stream=True)
            # Stream the response
            for chunk in response.iter_content(chunk_size=100000000):
                if chunk:  # filter out keep-alive new lines
                    yield json.loads(chunk.decode())

        def stop(self):
            """Stops the code."""
            # Not needed here, because e2b.run_code isn't stateful.
            pass

        def terminate(self):
            """Terminates the entire process."""
            # Not needed here, because e2b.run_code isn't stateful.
            pass

    interpreter.computer.languages = [Python]

    ### SKILLS

    script_dir = os.path.dirname(os.path.abspath(__file__))
    skills_dir = os.path.join(script_dir, 'skills')
    for file in glob.glob(os.path.join(skills_dir, '*.py')):
        with open(file, 'r') as f:
            for chunk in interpreter.computer.run("python", f.read()):
                print(chunk)

    ### RETURN INTERPRETER

    return interpreter
import os
import threading
import time

import geocoder

from .AI import AI
from .Audio import Audio
from .Commands import Commands
from .Controllers import MouseController
from .Gmail import Gmail
from .ScreenReader import ScreenReader
from .Weather import Weather


class Employer:
    _active_jobs: dict[str, threading.Thread] = {}

    def __init__(self, audio: bool = False) -> None:
        self.available_jobs = {
            "help": Employer.help,
            "ask_question": Employer.ask_question,
            "check_new_emails": Employer.check_new_emails,
            "start_checking_new_emails": Employer.start_checking_new_emails,
            "stop_checking_new_emails": Employer.stop_checking_new_emails,
            "weather": Employer.weather,
            "accept_game": Employer.accept_game,
            "idle_mouse": Employer.idle_mouse,
            "queue_up": Employer.queue_up,
            "close_computer": Employer.close_computer,
            "exit": Employer.exit,
        }
        self.available_functions = list(self.available_jobs.values())
        self.audio = audio

    def job_on_command(self, user_input: str) -> None:
        """
        Executes a job based on the given command.

        Args:
            command (str): The command to execute.

        Returns:
            None
        """

        bot_response = AI.get_function_to_call(user_input, self.available_functions)

        if bot_response is None:
            print("Error: Could not determine function to call.")

            return

        function_name = bot_response["name"]
        function_args = bot_response["args"]

        function_args["audio"] = self.audio

        if function_name in self.available_jobs:
            self.available_jobs[function_name](**function_args)

    @staticmethod
    def help(audio: bool = False, **kwargs) -> None:
        """
        Provides help information about available commands.

        Args:
            audio (bool): If True, the help information will be spoken using text-to-speech.
                          If False, the help information will be printed to the console.

        Returns:
            None
        """

        print("Getting all commands...")

        commands = Commands.get_all_commands()
        string_commends = ", ".join(commands)

        if audio:
            Audio.text_to_speech(f"Available commands are: {string_commends}.")
        else:
            print(f"Available commands are: {string_commends}.")

    @staticmethod
    def ask_question(question: str, audio: bool = False, **kwargs) -> None:
        """
        Asks a question and retrieves the answer from the AI assistant.

        Args:
            question (str): The question to ask.
            audio (bool): If True, the answer will be spoken using text-to-speech.
                          If False, the answer will be printed to the console.

        Returns:
            None
        """

        print("Asking question...")

        answer = AI.ask_question(question)

        if answer is None:
            print("Error: Could not retrieve an answer.")

            return

        if audio:
            Audio.text_to_speech(answer)
        else:
            print(answer)

    @staticmethod
    def check_new_emails(audio: bool = False, **kwargs) -> None:
        """
        Checks for new emails on Gmail and notifies the user either via audio or print.

        Args:
            audio (bool): If True, notifications will be given via text-to-speech.
                          If False, notifications will be printed to the console.

        Returns:
            None
        """

        print("Checking new emails...")

        messages = Gmail.get_new_messages()

        if audio:
            Audio.text_to_speech(f"You have {len(messages)} new messages.")
        else:
            print(f"You have {len(messages)} new messages.")

        for message in messages:
            formatted_message = Gmail.format_message(message)

            if audio:
                Audio.text_to_speech(formatted_message)
            else:
                print(formatted_message)

    @staticmethod
    def start_checking_new_emails(audio: bool = False, **kwargs) -> None:
        """
        Starts a background thread that checks for new emails at regular intervals.
        This function creates and starts a daemon thread that runs indefinitely,
        checking for new emails every 15 minutes. The check is performed by calling
        the `Employer.check_new_emails` method.

        Args:
            audio (bool, optional): If True, audio notifications will be enabled. Defaults to False.
            **kwargs: Additional keyword arguments to pass to the `Employer.check_new_emails` method.

        Returns:
            None
        """

        minutes = 15
        print(f"Checking new emails every {minutes} minutes...")

        def wrapper():
            while True:
                if "check_new_emails" not in Employer._active_jobs:
                    break

                Employer.check_new_emails(audio=audio)
                time.sleep(60 * minutes)

        if "check_new_emails" not in Employer._active_jobs:
            thread = threading.Thread(target=wrapper)
            thread.daemon = True
            thread.start()

            Employer._active_jobs["check_new_emails"] = thread

    @staticmethod
    def stop_checking_new_emails(**kwargs) -> None:
        """
        Stops the background thread that checks for new emails at regular intervals.
        This function stops the daemon thread that was started by the `Employer.infinitely_check_new_emails` method.

        Returns:
            None
        """

        print("Stopping checking new emails...")

        if "check_new_emails" in Employer._active_jobs:
            Employer._active_jobs["check_new_emails"].join()
            del Employer._active_jobs["check_new_emails"]

    @staticmethod
    def weather(city: str | None = None, audio: bool = False, **kwargs) -> None:
        """
        Retrieves and outputs the weather information for a given city. If no city is provided,
        it uses the user's current geolocation to determine the city.

        Args:
            city (str | None): The name of the city for which to retrieve the weather.
                                If None or empty string, the user's current geolocation is used.
            audio (bool): If True, the weather information is converted to speech. If False,
                          the weather information is printed to the console.

        Returns:
            None
        """

        print("Getting weather...")

        if city is None or city == "":
            my_geolocation = geocoder.ip("me")

            city = my_geolocation.city
            lat, lon = my_geolocation.latlng

        else:
            lat, lon = Weather.get_coordinates_for_city_name(city)

        if lat is None or lon is None:
            print("Error: Could not retrieve coordinates for the given city.")

            return

        weather = Weather.get_weather_for_coordinates(lat, lon)

        if weather is None:
            print("Error: Could not retrieve weather information.")

            return

        string_weather = f"The weather for {city} is {weather['weather'][0]['description']} with {weather['main']['temp']}°C."

        if audio:
            Audio.text_to_speech(string_weather)
        else:
            print(string_weather)

    @staticmethod
    def accept_game(**kwargs) -> None:
        """
        Accepts League of Legends queue pop.
        Starts a background thread that continuously takes screenshots and searches for the text "accept!".
        When the text is found, it moves the mouse to the center of the bounding box of the text and clicks the left mouse button.
        The function uses the following steps:
        1. Initializes a MouseController instance.
        2. Enters an infinite loop where it:
            a. Takes a grayscale screenshot using ScreenReader.
            b. Searches for the text "accept!" in the screenshot.
            c. If the text is found, moves the mouse to the center of the bounding box and clicks the left mouse button.
            d. Breaks the loop if the text is found.
            e. Sleeps for 5 seconds before taking another screenshot if the text is not found.
        3. Runs the above logic in a daemon thread.

        Note:
            This function is intended to be used in a game environment where the user needs to automatically accept a prompt.

        Returns:
            None
        """

        print("Accepting game...")

        def wrapper():
            mouse_controller = MouseController()

            while True:
                screenshot = ScreenReader.take_screenshot(gray=True)

                accept_object = ScreenReader.find_text_in_screenshot(
                    screenshot, "accept!"
                )

                if accept_object is not None:
                    mouse_controller.go_to_center_of_bbox(accept_object[0])
                    mouse_controller.click_left_button()

                    break

                time.sleep(5)

        thread = threading.Thread(target=wrapper)
        thread.daemon = True
        thread.start()

    @staticmethod
    def idle_mouse(**kwargs) -> None:
        """
        Simulates mouse idle activity by using the MouseController class to move the mouse.
        This function creates an instance of the MouseController class and calls its idle_mouse method to simulate mouse movement.

        Returns:
            None
        """

        print("Idling mouse...")

        mouse_controller = MouseController()
        mouse_controller.idle_mouse()

    @staticmethod
    def queue_up(**kwargs) -> None:
        """
        Opens the League of Legends application by starting the shortcut file located on the desktop.

        Returns:
            None
        """

        print("Queueing up...")

        os.startfile("C:/Users/Public/Desktop/League of Legends.lnk")

    @staticmethod
    def close_computer(audio: bool = False, **kwargs) -> None:
        """
        Shuts down the computer immediately after converting the text "o7" to speech.
        Executes the system command to shut down the computer forcefully and immediately.

        Returns:
            None
        """

        print("Closing computer...")

        if audio:
            Audio.text_to_speech("o7")
        else:
            print("o7")

        os.system("shutdown /s /f /t 0")

    @staticmethod
    def exit(audio: bool = False, **kwargs) -> None:
        """
        Terminates the process immediately without calling cleanup handlers, flushing stdio buffers, etc.
        This function is intended to be used for emergency exits only. It should not be used for normal program termination.

        Returns:
            None
        """

        print("Exiting program...")

        if audio:
            Audio.text_to_speech("o7")
        else:
            print("o7")

        os._exit(0)

import os
import subprocess
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

class BuildApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        # Add a dropdown spinner for platform selection
        self.spinner = Spinner(
            text="Select Platform",
            values=["Android (APK)", "iOS"],
            size_hint=(1, None),
            height=50
        )
        self.add_widget(self.spinner)

        # Add a button to trigger the build
        self.build_button = Button(
            text="Build",
            size_hint=(1, None),
            height=50
        )
        self.build_button.bind(on_press=self.build_app)
        self.add_widget(self.build_button)

        # Add a TextInput for log output
        self.log_output = TextInput(
            size_hint=(1, None),
            height=300,
            readonly=True
        )
        self.add_widget(self.log_output)

    def build_app(self, instance):
        platform = self.spinner.text
        if platform == "Select Platform":
            self.log_output.text += "Please select a platform before building.\n"
            return

        # Clear previous logs
        self.log_output.text = ""

        command = ""
        if platform == "Android (APK)":
            command = "buildozer android debug"
        elif platform == "iOS":
            command = "buildozer ios debug"

        # Run the command and capture output
        try:
            self.log_output.text += f"Starting build for {platform}...\n"
            process = subprocess.Popen(
                command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            for line in iter(process.stdout.readline, b""):
                self.log_output.text += line.decode("utf-8")
            process.wait()
            if process.returncode == 0:
                self.log_output.text += f"{platform} build completed successfully!\n"
            else:
                self.log_output.text += f"Error during {platform} build.\n"
        except Exception as e:
            self.log_output.text += f"An error occurred: {str(e)}\n"

class BuildAppGUI(App):
    def build(self):
        return BuildApp()

if __name__ == "__main__":
    BuildAppGUI().run()

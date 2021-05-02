#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Our implementation of the reaction test assignment.
Reactions are tested under two different conditions (simple, complex) with explanations for each.
The results of the reaction tests are logged to a .csv file.
The workload was evenly distributed across both team members.
authors: ev, lj
"""
import os
import random
import sys
import time

from PyQt5 import QtWidgets
from enum import Enum
from PyQt5 import uic, Qt, QtCore
from datetime import datetime
import pandas as pd

FIELDNAMES = ['ID', 'condition', 'shown_stimulus', 'pressed_key', 'is_correct_key', 'reaction_time_in_ms',
              'timestamp']  # csv header fields


class ApplicationState(Enum):
    """
    Enum used to keep track of the application state
    author: lj
    """
    EXPLANATION_ONE = 1
    EXPERIMENT_ONE = 2
    EXPLANATION_TWO = 3
    EXPERIMENT_TWO = 4
    FINISHED = 5


class ConditionType(Enum):
    CONDITION_SIMPLE = "simple"
    CONDITION_COMPLEX = "complex"


class SpaceRecorder(QtWidgets.QWidget):
    MIN_DELAY_MS = 5000  # minimum delay before the reaction stimulus appears
    MAX_DELAY_MS = 10000  # maximum delay before the reaction stimulus appears
    REPETITIONS = 10  # number of repetitions per condition type

    # the application state is used to hold the state of the application and display the correct explanations / stimuli
    applicationState = ApplicationState.EXPLANATION_ONE

    numbers = [1, 2, 3]  # possible numbers that can be displayed for the complex stimulus

    # Background styles used for experiment 1
    # TODO we can add more styles and then display a random color instead of only orange
    DEFAULT_STYLE = "background-color: white"
    SIMPLE_REACTION_STYLE = "background-color: orange"

    reaction_trigger = False  # set to true when the stimulus has been shown
    reaction_start_time_ms = 0  # value is overwritten when the stimulus is first shown
    reaction_end_time_ms = 0  # value is overwritten when the user pressed the button

    random_delay = 0
    timer = QtCore.QTimer()

    firstExperimentFinished = False
    secondExperimentFinished = False

    # below: variables used for logging
    participant_id = 0
    correct_key = ""
    condition = ""
    shown_stimulus = ""
    reaction_time = 0
    timestamp = 0

    counter = 0  # used to count how many repetitions the current experiment already ran for

    def __init__(self):
        super().__init__()
        self.counter = 0
        self.ui = uic.loadUi("experiment_ui.ui", self)
        self.set_participant_id()
        self.init_ui()
        self.set_first_experiment()

    def set_participant_id(self):
        """
        uses the passed argument and sets it as participant ID
        author: lj
        """
        try:
            self.participant_id = int(sys.argv[1])
        except (ValueError, IndexError):
            print("First argument must be an ID (integer)!")
            sys.exit(3)

    def set_first_experiment(self):
        """
        set the first experiment to either be the complex or simple one, depending on participant ID
        author: ev
        """
        if self.participant_id % 2:
            self.firstExperimentFinished = True
            self.applicationState = ApplicationState.EXPLANATION_ONE
            self.show_explanation_one()
        else:
            self.secondExperimentFinished = True
            self.applicationState = ApplicationState.EXPLANATION_TWO
            self.show_explanation_two()

    def show_explanation_one(self):
        self.ui.hintText.setVisible(True)
        self.ui.hintText.setText("Press Space when the background color changes! Press any key to start.")

    def show_explanation_two(self):
        self.ui.hintText.setVisible(True)
        self.ui.hintText.setText("For the next test, the display will show a randomly generated number between "
                                 "1 and 3. Press the correct number on your keyboard! "
                                 "Place your fingers on the numbers 1, 2, 3 and press any key when you are ready.")

    def show_finished_text(self):
        self.ui.hintText.setVisible(True)
        self.ui.hintText.setText("The experiment is complete. Thanks for participating! "
                                 "Please press any key to restart the experiment.")

    def start_experiment_one(self):
        """
        start the loop for the first experiment (simple stimulus)
        author :lj
        """
        if self.counter < self.REPETITIONS:
            self.ui.hintText.setVisible(False)
            self.random_delay = random.randrange(self.MIN_DELAY_MS, self.MAX_DELAY_MS)
            self.condition = ConditionType.CONDITION_SIMPLE
            self.shown_stimulus = "orange"
            self.correct_key = "Space"

            self.timer.singleShot(self.random_delay, lambda: self.trigger_stimulus_simple())

        else:
            if self.secondExperimentFinished:
                self.applicationState = ApplicationState.FINISHED
                self.show_finished_text()
            else:
                self.applicationState = ApplicationState.EXPLANATION_TWO
                self.show_explanation_two()

    def start_experiment_two(self):
        """
        start the loop for the second experiment (complex stimulus)
        author :lj
        """
        if self.counter < self.REPETITIONS:
            self.ui.hintText.setVisible(False)
            self.random_delay = random.randrange(self.MIN_DELAY_MS, self.MAX_DELAY_MS)
            self.condition = ConditionType.CONDITION_COMPLEX
            self.correct_key = random.choice(self.numbers)
            self.shown_stimulus = "Number " + str(self.correct_key)

            self.timer.singleShot(self.random_delay, lambda: self.trigger_stimulus_complex())

        else:
            if self.firstExperimentFinished:
                self.applicationState = ApplicationState.FINISHED
                self.show_finished_text()
            else:
                self.applicationState = ApplicationState.EXPLANATION_ONE
                self.show_explanation_one()

    def trigger_stimulus_simple(self):
        """
        trigger the simple stimulus
        author: ev
        """
        self.setStyleSheet(self.SIMPLE_REACTION_STYLE)
        self.reaction_trigger = True
        self.reaction_start_time_ms = round(time.time() * 1000)
        self.timestamp = datetime.now()

    def trigger_stimulus_complex(self):
        """
        trigger the complex stimulus
        author: ev
        """
        self.ui.complexText.setVisible(True)
        self.ui.complexText.setText(str(self.correct_key))
        self.reaction_trigger = True
        self.reaction_start_time_ms = round(time.time() * 1000)
        self.timestamp = datetime.now()

    def init_ui(self):
        self.ui.complexText.setVisible(False)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setStyleSheet(self.DEFAULT_STYLE)
        self.show()

    def keyPressEvent(self, ev):
        """
        listen for keypresses and decide how to react based on ApplicationState
        authors: ev, lj
        """

        if self.applicationState == ApplicationState.EXPLANATION_ONE:
            self.counter = 0
            self.applicationState = ApplicationState.EXPERIMENT_ONE
            self.start_experiment_one()
            return

        if self.applicationState == ApplicationState.EXPLANATION_TWO:
            self.counter = 0
            self.applicationState = ApplicationState.EXPERIMENT_TWO
            self.start_experiment_two()
            return

        if self.applicationState == ApplicationState.FINISHED:
            self.firstExperimentFinished = False
            self.secondExperimentFinished = False
            self.counter = 0
            self.participant_id += 1
            self.applicationState = ApplicationState.EXPLANATION_ONE
            self.set_first_experiment()
            return

        if self.reaction_trigger:
            self.handle_reaction(ev)

    def handle_reaction(self, ev):
        """
        react to a keypress after the stimulus was shown
        measures the reaction time in ms
        resets the ui components and boolean flags
        author: ev
        """
        self.reaction_end_time_ms = round(time.time() * 1000)
        print("Reaction Time: " + str(self.reaction_end_time_ms - self.reaction_start_time_ms))
        self.reaction_trigger = False
        self.counter += 1

        self.log_to_csv(ev.key())

        if self.applicationState == ApplicationState.EXPERIMENT_ONE:
            self.setStyleSheet(self.DEFAULT_STYLE)
            self.start_experiment_one()

        elif self.applicationState == ApplicationState.EXPERIMENT_TWO:
            self.ui.complexText.setVisible(False)
            self.start_experiment_two()

    def log_to_csv(self, pressed_key):
        """
        log the relevant data to our .csv file in the root folder
        each call appends a line to the already existing file
        author: lj
        """
        pressed_key = Qt.QKeySequence(pressed_key).toString()
        correct_key = str(self.correct_key)
        is_correct_key = pressed_key == correct_key
        reaction_time = self.reaction_end_time_ms - self.reaction_start_time_ms

        df = pd.DataFrame(columns=FIELDNAMES)
        df = df.append({
            'ID': self.participant_id,
            'condition': self.condition.value,
            'shown_stimulus': self.shown_stimulus,
            'pressed_key': pressed_key,
            'is_correct_key': is_correct_key,
            'reaction_time_in_ms': reaction_time,
            'timestamp': self.timestamp

        }, ignore_index=True)
        df.to_csv('logs.csv', mode='a', header=False, index=False)


def init_csv():
    """
    create our .csv log file if it does not exist already
    if the file is empty, write the csv header
    author: lj
    """
    open('logs.csv', 'a')
    if os.stat("logs.csv").st_size == 0:  # write csv header if file is empty
        df = pd.DataFrame(columns=FIELDNAMES)
        df.to_csv('logs.csv', index=False)
    # else:  this can be used to find the last logged ID in the file maybe we could use this later
    #     df = pd.read_csv("logs.csv")
    #     last_row = df.tail(1)
    #     last_used_id = last_row.iloc[0].ID


def main():
    init_csv()
    app = QtWidgets.QApplication(sys.argv)
    # variable is never used, class automatically registers itself for Qt main loop:
    space = SpaceRecorder()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

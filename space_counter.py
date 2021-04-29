#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import random
import sys
import time
import csv

from PyQt5 import QtGui, QtWidgets, QtCore
from enum import Enum
from PyQt5.QtWidgets import QMainWindow
from PyQt5 import uic, Qt, QtCore
from datetime import datetime
import pandas as pd

FIELDNAMES = ['ID', 'condition', 'shown_stimulus', 'pressed_key', 'is_correct_key', 'reaction_time_in_ms',
              'timestamp']  # csv header


class ApplicationState(Enum):
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
    REPETITIONS = 2  # number of repetitions per condition type

    # the application state is used to hold the state of the application and display the correct explanations / stimuli
    applicationState = ApplicationState.EXPLANATION_ONE

    numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    # Background styles used for experiment 1
    # TODO we can add more styles and then display a random color instead of only orange
    DEFAULT_STYLE = "background-color: white"
    SIMPLE_REACTION_STYLE = "background-color: orange"

    reaction_trigger = False  # set to true when the stimulus has been shown
    reaction_start_time_ms = 0  # value is overwritten when the stimulus is first shown
    reaction_end_time_ms = 0  # value is overwritten when the user pressed the button

    random_delay = 0
    timer = QtCore.QTimer()

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
        self.setParticipantId()
        self.initUI()
        self.showExplanationOne()  # upon startup, show the explanation for the first task

    def setParticipantId(self):
        try:
            self.participant_id = int(sys.argv[1])
        except (ValueError, IndexError):
            print("First argument must be an ID (integer)!")
            sys.exit(3)


    def showExplanationOne(self):
        self.ui.hintText.setVisible(True)
        self.ui.hintText.setText("Press Space when the background color changes! Press any key to start.")

    def showExplanationTwo(self):
        self.ui.hintText.setVisible(True)
        self.ui.hintText.setText("For the next test, the display will show a randomly generated number between "
                                 "0 and 9. Press the correct number on your keyboard! "
                                 "Press any key when you are ready.")

    def showFinishedText(self):
        self.ui.hintText.setVisible(True)
        self.ui.hintText.setText("The experiment is complete. Thanks for participating! "
                                 "Please press any key to restart the experiment.")


    def startLoop(self):
        if self.counter < self.REPETITIONS:
            self.ui.hintText.setVisible(False)
            self.random_delay = random.randrange(self.MIN_DELAY_MS, self.MAX_DELAY_MS)
            self.condition = ConditionType.CONDITION_SIMPLE
            self.shown_stimulus = "orange"
            self.correct_key = "Space"

            self.timer.singleShot(self.random_delay, lambda: self.triggerStimulusSimple())

        else:
            self.applicationState = ApplicationState.EXPLANATION_TWO
            self.showExplanationTwo()

    def startExperimentTwo(self):
        if self.counter < self.REPETITIONS:
            self.ui.hintText.setVisible(False)
            self.random_delay = random.randrange(self.MIN_DELAY_MS, self.MAX_DELAY_MS)
            self.condition = ConditionType.CONDITION_COMPLEX
            self.correct_key = random.choice(self.numbers)
            self.shown_stimulus = "Number " + str(self.correct_key)

            self.timer.singleShot(self.random_delay, lambda: self.triggerStimulusComplex())

        else:
            self.applicationState = ApplicationState.FINISHED
            self.showFinishedText()

    def triggerStimulusSimple(self):
        self.setStyleSheet(self.SIMPLE_REACTION_STYLE)
        self.reaction_trigger = True
        self.reaction_start_time_ms = round(time.time() * 1000)
        self.timestamp = datetime.now()

    def triggerStimulusComplex(self):
        self.ui.complexText.setVisible(True)
        self.ui.complexText.setText(str(self.correct_key))
        self.reaction_trigger = True
        self.reaction_start_time_ms = round(time.time() * 1000)
        self.timestamp = datetime.now()

    def initUI(self):
        self.ui.complexText.setVisible(False)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setStyleSheet(self.DEFAULT_STYLE)
        self.show()

    def keyPressEvent(self, ev):

        if self.applicationState == ApplicationState.EXPLANATION_ONE:
            self.applicationState = ApplicationState.EXPERIMENT_ONE
            self.startLoop()
            return

        if self.applicationState == ApplicationState.EXPLANATION_TWO:
            self.counter = 0
            self.applicationState = ApplicationState.EXPERIMENT_TWO
            self.startExperimentTwo()
            return

        if self.applicationState == ApplicationState.FINISHED:
            self.counter = 0
            self.participant_id += 1
            self.applicationState = ApplicationState.EXPLANATION_ONE
            self.showExplanationOne()
            return

        if self.reaction_trigger:
            self.handleReaction(ev)

    def handleReaction(self, ev):
        self.reaction_end_time_ms = round(time.time() * 1000)
        print("Reaction Time: " + str(self.reaction_end_time_ms - self.reaction_start_time_ms))
        self.reaction_trigger = False
        self.counter += 1

        self.log_to_csv(ev.key())

        if self.applicationState == ApplicationState.EXPERIMENT_ONE:
            self.setStyleSheet(self.DEFAULT_STYLE)
            self.startLoop()

        elif self.applicationState == ApplicationState.EXPERIMENT_TWO:
            self.ui.complexText.setVisible(False)
            self.startExperimentTwo()



    def log_to_csv(self, pressed_key):
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
    open('logs.csv', 'a')
    if os.stat("logs.csv").st_size == 0:  # write csv header if file is empty
        df = pd.DataFrame(columns=FIELDNAMES)
        df.to_csv('logs.csv', index=False)
    # else:  this can be used to find the last logged ID in the file
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

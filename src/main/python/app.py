import sys

import tweepy
import apiconnector
import sqlite3
from PySide2 import QtGui
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import QLabel, QApplication, QTabWidget, QWidget, QFormLayout, \
    QLineEdit, QPushButton, QPlainTextEdit, QComboBox, QSpinBox, QHBoxLayout, QProgressBar, QMessageBox, \
    QCalendarWidget, QDateTimeEdit, QTableView

from follow import FollowThread
from unfollow import UnfollowThread

from schedule import ScheduleThread


class application(QTabWidget):
    bot = 0

    def __init__(self, parent=None):
        super(application, self).__init__(parent)
        self.bot = None
        self.db = sqlite3.connect('database')
        # tabs
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()
        self.tab5 = QWidget()
        self.resize(640, 400)

        self.addTab(self.tab1, "Tab 1")
        self.addTab(self.tab2, "Tab 2")
        self.addTab(self.tab3, "Tab 3")
        self.addTab(self.tab4, "Tab 4")
        self.addTab(self.tab5, "Tab 5")

        # tab set keys
        self.h_box_key = QHBoxLayout()
        self.change_key_b = QPushButton("Edit keys")
        self.edit_1 = QLineEdit()
        self.edit_2 = QLineEdit()
        self.edit_3 = QLineEdit()
        self.edit_4 = QLineEdit()
        self.result = QLabel()
        self.set_button = QPushButton("Set keys")
        self.handle_info = QLabel()
        self.follower_info = QLabel()
        self.ready_lab = QLabel()

        # tab follow
        self.box_label = QLabel("Link to tweet")
        self.combo_label = QLabel("Mode")
        self.spin_label = QLabel("Limit before sleep")
        self.prog_bar = QProgressBar()
        self.combo_box = QComboBox()
        self.h_box = QHBoxLayout()
        self.spin_box = QSpinBox()
        self.link_box = QLineEdit()
        self.link_result = QLabel()
        self.follow_button = QPushButton("Follow Retweeters")
        self.cancel_button = QPushButton("Cancel")
        self.logger = QPlainTextEdit()
        self.h_box2 = QHBoxLayout()
        self.max_box = QSpinBox()
        self.max_label = QLabel("Max follows before stop")

        # tab unfollow
        self.unfollow_button = QPushButton("Unfollow Auto followers")
        self.unf_logger = QPlainTextEdit()
        self.unfollow_res = QLabel()
        self.prog_bar_unf = QProgressBar()
        self.unfollow_cancel = QPushButton("Cancel")
        self.unf_confirm = QMessageBox()

        # tab help
        self.help_box = QPlainTextEdit()
        self.help_label = QLabel("<a href='http://Optumsense.com/'>http://Optumsense.com/</a>")

        #tab schedule
        self.tweet_box = QPlainTextEdit()
        self.date_time = QDateTimeEdit(QDateTime.currentDateTime())
        self.schedule_but = QPushButton("Schedule Tweet")
        self.schedule_info = QLabel()
        self.schedule_table = QTableView()

        # threads
        self.follow_thread = None
        self.unfollow_thread = None
        self.schedule_thread = None

        # tabs
        self.tab1UI()
        self.tab2UI()
        self.tab3UI()
        self.tab4UI()
        self.tab5UI()

        self.setWindowTitle("Optumize")
        self.setWindowIcon(QtGui.QIcon('assets/oo.png'))

        # db
        cursor = self.db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keys(one TEXT, two TEXT, three TEXT, four TEXT)''')
        self.db.commit()

    def tab1UI(self):
        layout = QFormLayout()
        layout.addRow(self.h_box)
        self.h_box.addWidget(self.combo_label)
        self.combo_label.setAlignment(Qt.AlignRight)
        self.h_box.addWidget(self.combo_box)
        self.combo_box.addItem("Follow Retweeters")
        self.combo_box.addItem("Follow Followers")
        self.combo_box.currentIndexChanged.connect(self.selection_change)

        self.h_box.addWidget(self.spin_label)
        self.spin_label.setAlignment(Qt.AlignRight)
        self.h_box.addWidget(self.spin_box)
        self.spin_box.setMinimum(1)
        self.spin_box.setValue(30)

        layout.addRow(self.box_label, self.link_box)
        self.link_result.setAlignment(Qt.AlignCenter)
        layout.addRow(self.link_result)
        layout.addRow(self.follow_button)
        self.follow_button.clicked.connect(self.follow_ret)


        layout.addRow(self.cancel_button)
        self.cancel_button.clicked.connect(self.cancel_onclick)
        layout.addRow(self.h_box2)
        self.h_box2.addWidget(self.max_label)
        self.h_box2.addWidget(self.max_box)
        self.max_box.setFixedWidth(100)
        self.max_label.setAlignment(Qt.AlignRight)
        self.max_box.setMaximum(1000000)
        self.max_box.setValue(100)
        self.max_label.hide()
        self.max_box.hide()
        layout.addRow(self.logger)


        self.logger.setReadOnly(True)
        layout.addRow(self.prog_bar)
        self.prog_bar.setAlignment(Qt.AlignCenter)
        self.setTabText(0, "Follow")
        self.setTabIcon(0, QtGui.QIcon('assets/check_mark.png'))
        self.tab1.setLayout(layout)

    def selection_change(self, i):
        if i == 0:
            self.box_label.setText("Link to tweet")
            self.follow_button.setText("Follow Retweeters")
            self.link_result.setText("")
            self.max_label.hide()
            self.max_box.hide()
            self.follow_button.clicked.connect(self.follow_ret)
        else:
            self.box_label.setText("Handle of user")
            self.follow_button.setText("Follow Followers")
            self.link_result.setText("")
            self.max_label.show()
            self.max_box.show()
            self.max_label.setText("Max follows before stop")
            self.follow_button.clicked.connect(self.follow_fol)

    def cancel_onclick(self):
        if self.follow_thread is None:
            pass
        elif self.follow_thread.isRunning():
            self.prog_bar.setValue(0)
            self.logger.appendPlainText("Cancelled script")
            self.follow_thread.terminate()
            self.follow_thread = None

    def follow_ret(self):
        self.prog_bar.setValue(0)
        self.follow_button.setEnabled(False)
        self.link_result.setText("")
        self.logger.clear()
        limit = self.spin_box.value()
        if self.bot is None:
            self.link_result.setText("<font color='red'>Configure access keys in set keys tab</font>")
            return
        if self.follow_thread is not None:
            return
        link = self.link_box.text()
        id_tweet = link.split("/")[-1]
        try:
            tweet = self.bot.api.get_status(id_tweet)

            self.logger.appendPlainText(f"following retweeters from link: {link}...")
            self.follow_thread = FollowThread(self.bot, id_tweet, limit, 1, 0)
            self.follow_thread.start()
            self.connect(self.follow_thread, SIGNAL("finished()"), self.done)
            self.connect(self.follow_thread, SIGNAL("setup_prog(QString)"), self.setup_prog)
            self.connect(self.follow_thread, SIGNAL("post_follow(QString)"), self.post_follow)
        except tweepy.error.TweepError:
            self.follow_button.setEnabled(True)
            self.link_result.setText("<font color='red'>Could not find tweet</font>")

    def setup_prog(self, msg):
        self.prog_bar.setMaximum(int(msg))

    def follow_fol(self):
        self.prog_bar.setValue(0)
        self.follow_button.setEnabled(False)
        self.link_result.setText("")
        self.logger.clear()
        limit = self.spin_box.value()
        if self.bot is None:
            self.link_result.setText("<font color='red'>Configure access keys in set keys tab</font>")
            return
        if self.follow_thread is not None:
            return
        handle = self.link_box.text()
        if handle == '':
            self.link_result.setText("<font color='red'>Enter a handle above</font>")
            return
        elif handle[0] == '@':
            id_user = handle[1:]
        else:
            id_user = handle
        try:
            man = self.bot.api.get_user(id_user)
            self.logger.appendPlainText(f"following followers of {man.screen_name}...")
            self.logger.appendPlainText(f"Collecting")
            self.follow_thread = FollowThread(self.bot, id_user, limit, 2, self.max_box.value())
            self.follow_thread.start()
            self.connect(self.follow_thread, SIGNAL("finished()"), self.done)
            self.connect(self.follow_thread, SIGNAL("setup_prog(QString)"), self.setup_prog)
            self.connect(self.follow_thread, SIGNAL("post_follow(QString)"), self.post_follow)
        except tweepy.error.TweepError:
            self.follow_button.setEnabled(True)
            self.link_result.setText("<font color='red'>Could not find user</font>")

    def post_follow(self, message):
        if message == "bad":
            self.logger.appendPlainText("Rate limit exceeded... sleeping for cooldown")
        else:
            self.logger.appendPlainText(message)
            self.prog_bar.setValue(self.prog_bar.value() + 1)

    def done(self):
        self.follow_thread = None
        self.follow_button.setEnabled(True)

    def tab2UI(self):
        layout = QFormLayout()
        layout.addRow(self.unfollow_button)
        layout.addRow(self.unfollow_cancel)
        layout.addRow(self.unfollow_res)
        self.unfollow_res.setAlignment(Qt.AlignCenter)
        self.unfollow_button.clicked.connect(self.unfollow_fol)
        self.unfollow_cancel.clicked.connect(self.unfollow_can)
        layout.addWidget(self.unf_logger)
        self.unf_logger.setReadOnly(True)
        layout.addRow(self.prog_bar_unf)
        self.prog_bar_unf.setAlignment(Qt.AlignCenter)
        self.setTabText(1, "Unfollow")
        self.setTabIcon(1, QtGui.QIcon('assets/cross.png'))
        self.tab2.setLayout(layout)

    def unfollow_fol(self):
        self.unfollow_button.setEnabled(False)
        self.unfollow_thread = UnfollowThread(self.bot)
        self.unfollow_thread.start()
        self.connect(self.unfollow_thread, SIGNAL("post_unfol(QString)"), self.post_unfol)
        self.connect(self.unfollow_thread, SIGNAL("finished()"), self.done_unf)

    def done_unf(self):
        self.unfollow_thread = None
        self.unf_logger.appendPlainText("Done")
        self.unfollow_button.setEnabled(True)

    def post_unfol(self, msg):
        if msg == "bad":
            self.unf_logger.appendPlainText("rate limit exceeded, resting for 15 minutes")
        else:
            self.unf_logger.appendPlainText(f"Unfollowing {msg}")

    def unfollow_can(self):
        if self.unfollow_thread is None:
            pass
        elif self.unfollow_thread.isRunning():
            self.unf_logger.appendPlainText("Cancelled script")
            self.unfollow_thread.terminate()
            self.unfollow_thread = None

    def tab3UI(self):
        layout = QFormLayout()
        layout.addWidget(self.tweet_box)
        self.tweet_box.setMaximumHeight(150)
        self.tweet_box.setPlaceholderText("Tweet contents")
        layout.addRow(self.date_time)
        self.date_time.setCalendarPopup(True)
        layout.addRow(self.schedule_info)
        layout.addRow(self.schedule_but)
        self.schedule_but.clicked.connect(self.schedule_tweet)
        layout.addWidget(self.schedule_table)
        self.setTabText(2, "Schedule Tweet")
        self.setTabIcon(2, QtGui.QIcon('assets/calendar.png'))
        self.tab3.setLayout(layout)

    def schedule_tweet(self):
        tweet_contents = self.tweet_box.toPlainText()
        if (len(tweet_contents) == 0):
            print("length of tweet is 0")
            self.schedule_info.setText("length of tweet is 0")
            return
        elif (len(tweet_contents) >= 280):
            self.schedule_info.setText("Tweet char limit exceeded")
            return
        if self.bot is None:
            self.schedule_info.setText("<font color='red'>Configure access keys in set keys tab</font>")
            return
        datetime = self.date_time.text()
        try:
            print("done")
            self.schedule_thread.start()
            self.schedule_thread.add_tweet(tweet_contents, datetime)
        except:
            self.follow_button.setEnabled(True)
            self.link_result.setText("<font color='red'>Could not find user</font>")

    def done_schedule(self):
        print("done scheduler")

    def tab4UI(self):
        layout = QFormLayout()
        layout.addRow("API key", self.edit_1)
        layout.addRow("API key secret", self.edit_2)
        layout.addRow("Auth token", self.edit_3)
        layout.addRow("Auth token secret", self.edit_4)
        self.set_button.clicked.connect(self.set_keys)
        l = self.read_file()
        if l is not None:
            if len(l) == 4:
                self.edit_1.setText(l[0])
                self.edit_2.setText(l[1])
                self.edit_3.setText(l[2])
                self.edit_4.setText(l[3])
                self.set_keys()
        layout.addRow(self.result)
        self.result.setAlignment(Qt.AlignCenter)
        layout.addRow(self.h_box_key)
        self.h_box_key.addWidget(self.change_key_b)
        self.h_box_key.addWidget(self.set_button)
        self.change_key_b.clicked.connect(self.change_keys)
        layout.addRow(self.handle_info)
        self.handle_info.setAlignment(Qt.AlignCenter)
        layout.addRow(self.follower_info)
        self.follower_info.setAlignment(Qt.AlignCenter)
        layout.addRow(self.ready_lab)
        self.ready_lab.setAlignment(Qt.AlignCenter)
        self.setTabText(3, "Settings")
        self.setTabIcon(3, QtGui.QIcon('assets/settings.png'))
        self.tab4.setLayout(layout)

    def change_keys(self):
        self.set_button.setEnabled(True)

    def set_keys(self):
        self.set_button.setEnabled(False)
        self.result.setText("")
        one = self.edit_1.text()
        two = self.edit_2.text()
        three = self.edit_3.text()
        four = self.edit_4.text()
        try:
            self.bot = apiconnector.ApiConnector(one, two, three, four)
            me = self.bot.add_keys(one, two, three, four)
            self.handle_info.setText("Handle: @" + me.screen_name)
            self.follower_info.setText("Followers: " + str(me.followers_count))
            self.ready_lab.setText("<font color='green'>Ready!</font>")
            cursor = self.db.cursor()
            cursor.execute('DELETE FROM keys;',);
            cursor.execute('''INSERT INTO keys(one, two, three, four)
                  VALUES(?,?,?,?)''', (one, two, three, four))
            self.db.commit()
            self.schedule_thread = ScheduleThread(self.bot)
        except:
            print("Could not authenticate you")
            self.result.setText("<font color='red'>Could not authenticate you</font>")

    def read_file(self):
        result = []
        try:
            cursor = self.db.cursor()
            cursor.execute('''SELECT one, two, three, four FROM keys''')
            all_rows = cursor.fetchall()
            for row in all_rows:
                result.append(row[0])
                result.append(row[1])
                result.append(row[2])
                result.append(row[3])
            return result

        except:
            return None

    def tab5UI(self):
        layout = QFormLayout()
        layout.addRow("Website", self.help_label)
        self.help_label.setOpenExternalLinks(True)
        self.setTabText(4, "Help")
        self.setTabIcon(4, QtGui.QIcon('assets/help.png'))
        self.tab5.setLayout(layout)


def main():
    app = QApplication(sys.argv)
    ex = application()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

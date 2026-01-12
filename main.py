# ///////////////////////////////////////////////////////////////
#
# BY: WANDERSON M.PIMENTA
# PROJECT MADE WITH: Qt Designer and PySide6
# V: 1.0.0
#
# This project can be used freely for all uses, as long as they maintain the
# respective credits only in the Python scripts, any information in the visual
# interface (GUI) can be modified without any implication.
#
# There are limitations on Qt licenses if you want to use your products
# commercially, I recommend reading them on the official website:
# https://doc.qt.io/qtforpython/licenses.html
#
# ///////////////////////////////////////////////////////////////

import sys
import os
import platform

# IMPORT / GUI AND MODULES AND WIDGETS
# ///////////////////////////////////////////////////////////////
from app.ui.bindings import set_confirm_state, set_worker_status
from app.world.general_manager import GeneralManager
from app.world.wiring import WorldWiring
from app.ui_vendor.modules import *
from app.ui_vendor.widgets import *
os.environ["QT_FONT_DPI"] = "96" # FIX Problem for High DPI and Scale above 100%

# SET AS GLOBAL WIDGETS
# ///////////////////////////////////////////////////////////////
widgets = None

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        # SET AS GLOBAL WIDGETS
        # ///////////////////////////////////////////////////////////////
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        global widgets
        widgets = self.ui

        # USE CUSTOM TITLE BAR | USE AS "False" FOR MAC OR LINUX
        # ///////////////////////////////////////////////////////////////
        Settings.ENABLE_CUSTOM_TITLE_BAR = True

        # APP NAME
        # ///////////////////////////////////////////////////////////////
        title = "agent_chat"
        description = ""
        # APPLY TEXTS
        self.setWindowTitle(title)
        widgets.titleRightInfo.setText(description)

        # TOGGLE MENU
        # ///////////////////////////////////////////////////////////////
        widgets.toggleButton.clicked.connect(lambda: UIFunctions.toggleMenu(self, True))

        # SET UI DEFINITIONS
        # ///////////////////////////////////////////////////////////////
        UIFunctions.uiDefinitions(self)
        self._setup_agent_ui()
        self._setup_world_wiring()

        # QTableWidget PARAMETERS
        # ///////////////////////////////////////////////////////////////
        widgets.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # BUTTONS CLICK
        # ///////////////////////////////////////////////////////////////

        # LEFT MENUS
        widgets.btn_home.clicked.connect(self.buttonClick)
        widgets.btn_widgets.clicked.connect(self.buttonClick)
        widgets.btn_new.clicked.connect(self.buttonClick)
        widgets.btn_save.clicked.connect(self.buttonClick)

        # EXTRA LEFT BOX
        def openCloseLeftBox():
            UIFunctions.toggleLeftBox(self, True)
        widgets.toggleLeftBox.clicked.connect(openCloseLeftBox)
        widgets.extraCloseColumnBtn.clicked.connect(openCloseLeftBox)

        # EXTRA RIGHT BOX
        def openCloseRightBox():
            UIFunctions.toggleRightBox(self, True)
        widgets.settingsTopBtn.clicked.connect(openCloseRightBox)

        # SHOW APP
        # ///////////////////////////////////////////////////////////////
        self.show()

        # SET CUSTOM THEME
        # ///////////////////////////////////////////////////////////////
        useCustomTheme = False
        themeFile = os.path.join("app", "ui_vendor", "themes", "py_dracula_light.qss")

        # SET THEME AND HACKS
        if useCustomTheme:
            # LOAD AND APPLY STYLE
            UIFunctions.theme(self, themeFile, True)

            # SET HACKS
            AppFunctions.setThemeHack(self)

        # SET HOME PAGE AND SELECT MENU
        # ///////////////////////////////////////////////////////////////
        widgets.stackedWidget.setCurrentWidget(widgets.home)
        widgets.btn_home.setStyleSheet(UIFunctions.selectMenu(widgets.btn_home.styleSheet()))
        widgets.btn_home.setText("Chat")
        widgets.btn_widgets.setText("Jobs")
        widgets.btn_new.setText("Workers")
        widgets.btn_save.setText("Logs")


    # BUTTONS CLICK
    # Post here your functions for clicked buttons
    # ///////////////////////////////////////////////////////////////
    def buttonClick(self):
        # GET BUTTON CLICKED
        btn = self.sender()
        btnName = btn.objectName()

        # SHOW HOME PAGE
        if btnName == "btn_home":
            widgets.stackedWidget.setCurrentWidget(widgets.home)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # SHOW WIDGETS PAGE
        if btnName == "btn_widgets":
            widgets.stackedWidget.setCurrentWidget(widgets.home)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # SHOW NEW PAGE
        if btnName == "btn_new":
            widgets.stackedWidget.setCurrentWidget(widgets.home) # SET PAGE
            UIFunctions.resetStyle(self, btnName) # RESET ANOTHERS BUTTONS SELECTED
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet())) # SELECT MENU

        if btnName == "btn_save":
            widgets.stackedWidget.setCurrentWidget(widgets.home)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
            print("Logs BTN clicked!")

        # PRINT BTN NAME
        print(f'Button "{btnName}" pressed!')

    def _setup_agent_ui(self):
        self.ui.home.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self.ui.home)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Left sidebar (sessions/options)
        left_sidebar = QFrame()
        left_sidebar.setObjectName("leftSidebar")
        left_sidebar.setFrameShape(QFrame.StyledPanel)
        left_sidebar.setMinimumWidth(200)
        left_sidebar.setMaximumWidth(260)
        left_sidebar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        left_layout = QVBoxLayout(left_sidebar)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(8)
        left_title = QLabel("Sessions")
        left_title.setStyleSheet("font-weight: 600;")
        left_layout.addWidget(left_title)
        session_list = QListWidget()
        session_list.addItem("Chat-1 (active)")
        session_list.addItem("Chat-2")
        session_list.addItem("Chat-3")
        left_layout.addWidget(session_list, 1)
        options_title = QLabel("Options")
        options_title.setStyleSheet("font-size: 11px; color: #888;")
        left_layout.addWidget(options_title)
        options_panel = QWidget()
        options_layout = QVBoxLayout(options_panel)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(4)
        opt_autoscroll = QCheckBox("Auto-scroll")
        opt_show_tools = QCheckBox("Show tool logs")
        opt_compact = QCheckBox("Compact mode")
        for opt in (opt_autoscroll, opt_show_tools, opt_compact):
            opt.setEnabled(False)
        options_layout.addWidget(opt_autoscroll)
        options_layout.addWidget(opt_show_tools)
        options_layout.addWidget(opt_compact)
        left_layout.addWidget(options_panel)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Chat panel
        chat_panel = QFrame()
        chat_panel.setObjectName("chatPanel")
        chat_panel.setFrameShape(QFrame.StyledPanel)
        chat_layout = QVBoxLayout(chat_panel)
        chat_layout.setContentsMargins(10, 10, 10, 10)
        chat_layout.setSpacing(8)
        chat_title = QLabel("Chat")
        chat_title.setStyleSheet("font-weight: 600;")
        chat_layout.addWidget(chat_title)
        chat_log = QPlainTextEdit()
        chat_log.setReadOnly(True)
        chat_log.setPlaceholderText("Chat history...")
        chat_layout.addWidget(chat_log, 1)
        chat_input_row = QHBoxLayout()
        chat_input = QLineEdit()
        chat_input.setPlaceholderText("Type a message...")
        chat_send = QPushButton("Send")
        chat_input_row.addWidget(chat_input, 1)
        chat_input_row.addWidget(chat_send)
        chat_layout.addLayout(chat_input_row)

        # Job panel
        job_panel = QFrame()
        job_panel.setObjectName("jobPanel")
        job_panel.setFrameShape(QFrame.StyledPanel)
        job_layout = QVBoxLayout(job_panel)
        job_layout.setContentsMargins(10, 10, 10, 10)
        job_layout.setSpacing(8)
        job_title = QLabel("Job Panel")
        job_title.setStyleSheet("font-weight: 600;")
        job_layout.addWidget(job_title)
        job_tabs = QTabWidget()
        job_chat = QPlainTextEdit()
        job_chat.setReadOnly(True)
        job_chat.setPlaceholderText("Job chat...")
        job_log = QPlainTextEdit()
        job_log.setReadOnly(True)
        job_log.setPlaceholderText("Tool logs...")
        job_tabs.addTab(job_chat, "Job Chat")
        job_tabs.addTab(job_log, "Tool Logs")
        job_layout.addWidget(job_tabs, 1)
        confirm_title = QLabel("Confirm Options (state-driven)")
        confirm_title.setStyleSheet("font-size: 11px; color: #888;")
        job_layout.addWidget(confirm_title)
        confirm_stack = QStackedWidget()
        confirm_stack.setObjectName("confirmStack")
        confirm_stack.setContentsMargins(0, 0, 0, 0)
        confirm_stack.setMinimumHeight(70)

        confirm_idle = QWidget()
        idle_layout = QVBoxLayout(confirm_idle)
        idle_layout.setContentsMargins(8, 8, 8, 8)
        idle_layout.setSpacing(4)
        idle_label = QLabel("No confirmation required.")
        idle_label.setStyleSheet("color: #777;")
        idle_layout.addWidget(idle_label)

        confirm_lock = QWidget()
        lock_layout = QHBoxLayout(confirm_lock)
        lock_layout.setContentsMargins(8, 8, 8, 8)
        lock_layout.setSpacing(6)
        lock_title = QLabel("Lock state options")
        lock_title.setStyleSheet("font-size: 11px; color: #999;")
        lock_layout.addWidget(lock_title)
        lock_layout.addStretch(1)

        confirm_approve = QWidget()
        approve_layout = QHBoxLayout(confirm_approve)
        approve_layout.setContentsMargins(8, 8, 8, 8)
        approve_layout.setSpacing(6)
        approve_title = QLabel("Approval state options")
        approve_title.setStyleSheet("font-size: 11px; color: #999;")
        approve_layout.addWidget(approve_title)
        approve_layout.addStretch(1)

        btn_wait = QPushButton("Wait")
        btn_cancel = QPushButton("Cancel")
        btn_stop = QPushButton("Stop Other")
        btn_approve = QPushButton("Approve")
        btn_reject = QPushButton("Reject")
        for btn in (btn_wait, btn_cancel, btn_stop, btn_approve, btn_reject):
            btn.setEnabled(False)
        lock_layout.addWidget(btn_wait)
        lock_layout.addWidget(btn_cancel)
        lock_layout.addWidget(btn_stop)
        approve_layout.addWidget(btn_approve)
        approve_layout.addWidget(btn_reject)

        confirm_stack.addWidget(confirm_idle)
        confirm_stack.addWidget(confirm_lock)
        confirm_stack.addWidget(confirm_approve)
        confirm_stack.setCurrentIndex(0)
        job_layout.addWidget(confirm_stack)

        splitter.addWidget(chat_panel)
        splitter.addWidget(job_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 4)

        # Dashboard panel
        dashboard_panel = QFrame()
        dashboard_panel.setObjectName("dashboardPanel")
        dashboard_panel.setFrameShape(QFrame.StyledPanel)
        dashboard_panel.setMinimumWidth(240)
        dashboard_panel.setMaximumWidth(320)
        dashboard_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        dash_layout = QVBoxLayout(dashboard_panel)
        dash_layout.setContentsMargins(10, 10, 10, 10)
        dash_layout.setSpacing(8)
        dash_title = QLabel("Dashboard")
        dash_title.setStyleSheet("font-weight: 600;")
        dash_layout.addWidget(dash_title)
        dash_list = QListWidget()
        dash_list.addItem("worker-1: idle")
        dash_list.addItem("worker-2: idle")
        dash_list.addItem("worker-3: idle")
        dash_layout.addWidget(dash_list, 1)

        # Expose widgets for later wiring
        self.ui.chat_log = chat_log
        self.ui.chat_input = chat_input
        self.ui.job_chat = job_chat
        self.ui.job_log = job_log
        self.ui.dashboard_list = dash_list
        self.ui.btn_wait = btn_wait
        self.ui.btn_cancel = btn_cancel
        self.ui.btn_stop = btn_stop
        self.ui.btn_approve = btn_approve
        self.ui.btn_reject = btn_reject
        self.ui.confirm_stack = confirm_stack
        self.ui.confirm_idle = confirm_idle
        self.ui.confirm_lock = confirm_lock
        self.ui.confirm_approve = confirm_approve
        self.ui.session_list = session_list
        self.ui.options_panel = options_panel
        self.ui.left_sidebar = left_sidebar

        set_confirm_state(self.ui, "idle")

        layout.addWidget(left_sidebar)
        layout.addWidget(splitter, 1)
        layout.addWidget(dashboard_panel)

    def _setup_world_wiring(self):
        specs_path = os.path.join("app", "toolbox", "specs", "tools.yaml")
        self.world = WorldWiring(specs_path=specs_path, adapters={})
        self.world.start_workers()
        self.gm = GeneralManager(self.world)
        self._bind_event_bus()

    def _bind_event_bus(self):
        def on_job_state(payload):
            worker_id = payload.get("job_id", "job")
            state = payload.get("state", "running")
            set_worker_status(self.ui, {worker_id: state})

            if state == "waiting_confirm":
                set_confirm_state(self.ui, "approve")
            elif state == "waiting_lock":
                set_confirm_state(self.ui, "lock")
            else:
                set_confirm_state(self.ui, "idle")

        def on_job_log(payload):
            logs = payload.get("logs", [])
            if logs:
                self.ui.job_log.setPlainText("\n".join(logs[-200:]))

        def on_job_done(payload):
            worker_id = payload.get("job_id", "job")
            set_worker_status(self.ui, {worker_id: "done"})

        def on_job_failed(payload):
            worker_id = payload.get("job_id", "job")
            set_worker_status(self.ui, {worker_id: "failed"})

        self.world.event_bus.subscribe("job_state", on_job_state)
        self.world.event_bus.subscribe("job_log", on_job_log)
        self.world.event_bus.subscribe("job_done", on_job_done)
        self.world.event_bus.subscribe("job_failed", on_job_failed)


    # RESIZE EVENTS
    # ///////////////////////////////////////////////////////////////
    def resizeEvent(self, event):
        # Update Size Grips
        UIFunctions.resize_grips(self)

    # MOUSE CLICK EVENTS
    # ///////////////////////////////////////////////////////////////
    def mousePressEvent(self, event):
        # SET DRAG POS WINDOW
        self.dragPos = event.globalPos()

        # PRINT MOUSE EVENTS
        if event.buttons() == Qt.LeftButton:
            print('Mouse click: LEFT CLICK')
        if event.buttons() == Qt.RightButton:
            print('Mouse click: RIGHT CLICK')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join("app", "ui_vendor", "icon.ico")))
    window = MainWindow()
    sys.exit(app.exec_())

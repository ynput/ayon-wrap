from qtpy import QtCore, QtWidgets, QtGui

from ayon_core import style, resources
from ayon_core.tools.utils import (
    PlaceholderLineEdit,
    MessageOverlayObject,
)

from ayon_core.tools.workfiles.control import BaseWorkfileController
from ayon_core.tools.utils import (
    GoToCurrentButton,
    RefreshButton,
    FoldersWidget,
    TasksWidget,
)
# from .files_widget import FilesWidget
from .control import WorkfileToolController
from .widgets.files_widget_workarea import MultiWorkAreaFilesWidget


class WorkfilesToolWindow(QtWidgets.QDialog):
    """WorkFiles Window.

    Main windows of workfiles tool.

    Args:
        controller (AbstractWorkfilesFrontend): Frontend controller.
        parent (Optional[QtWidgets.QWidget]): Parent widget.
    """

    title = "Work Files"

    def __init__(self, controller=None, parent=None, launch_data=None):
        super(WorkfilesToolWindow, self).__init__(parent=parent)

        self.setWindowTitle(self.title)
        icon = QtGui.QIcon(resources.get_ayon_icon_filepath())
        self.setWindowIcon(icon)
        flags = self.windowFlags() | QtCore.Qt.Window
        self.setWindowFlags(flags)

        self._default_window_flags = flags

        self._folders_widget = None
        self._folder_filter_input = None

        self._files_widget = None

        self._first_show = True
        self._controller_refreshed = False
        self._context_to_set = None
        # Host validation should happen only once
        self._host_is_valid = None

        if controller is None:
            controller = WorkfileToolController(launch_data=launch_data)

        self._controller = controller

        # Create pages widget and set it as central widget
        pages_widget = QtWidgets.QStackedWidget(self)

        home_page_widget = QtWidgets.QWidget(pages_widget)
        home_body_widget = QtWidgets.QWidget(home_page_widget)

        templates_widget = self._create_templates_widget(
            controller, home_body_widget
        )

        workfile_widget = self._create_workfiles_widget(
            controller, home_body_widget)

        pages_widget.addWidget(home_page_widget)

        btns_widget = QtWidgets.QWidget(self)

        workarea_btns_widget = QtWidgets.QWidget(btns_widget)
        workarea_btn_create = QtWidgets.QPushButton(
            "Create New", workarea_btns_widget)
        workarea_btn_open = QtWidgets.QPushButton(
            "Open", workarea_btns_widget)

        workarea_btns_layout = QtWidgets.QHBoxLayout(workarea_btns_widget)
        workarea_btns_layout.setContentsMargins(450, 0, 0, 0)
        workarea_btns_layout.addWidget(workarea_btn_create, 1)
        workarea_btns_layout.addWidget(workarea_btn_open, 1)

        workarea_btn_open.clicked.connect(self._on_workarea_open_clicked)
        workarea_btn_create.clicked.connect(self._on_workarea_create_clicked)

        # Build home
        home_page_layout = QtWidgets.QVBoxLayout(home_page_widget)
        home_page_layout.addWidget(home_body_widget)
        home_page_layout.addWidget(workarea_btns_widget)

        # Build home - body
        body_layout = QtWidgets.QVBoxLayout(home_body_widget)
        split_widget = QtWidgets.QSplitter(home_body_widget)
        split_widget.addWidget(templates_widget)
        split_widget.addWidget(workfile_widget)

        split_widget.setSizes([175, 275])

        body_layout.addWidget(split_widget)

        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.addWidget(pages_widget, 1)

        show_timer = QtCore.QTimer()
        show_timer.setSingleShot(True)
        show_timer.setInterval(50)

        show_timer.timeout.connect(self._on_show)

        controller.register_event_callback(
            "open_workfile.finished",
            self._on_open_finished
        )
        controller.register_event_callback(
            "controller.reset.started",
            self._on_controller_refresh_started,
        )
        controller.register_event_callback(
            "controller.reset.finished",
            self._on_controller_refresh_finished,
        )

        self._home_page_widget = home_page_widget
        self._pages_widget = pages_widget
        self._home_body_widget = home_body_widget
        self._split_widget = split_widget

        self._workarea_btn_open = workarea_btn_open
        self._workarea_btn_create = workarea_btn_create

        self._show_timer = show_timer

        self._post_init()

    def _post_init(self):

        # Force focus on the open button by default, required for Houdini.
        # self._files_widget.setFocus()

        self.resize(1260, 600)

    def _create_templates_widget(self, controller, parent):
        col_widget = QtWidgets.QWidget(parent)

        templates_widget = QtWidgets.QListWidget(col_widget)

        controller.fill_templates(templates_widget)

        col_layout = QtWidgets.QVBoxLayout(col_widget)
        col_layout.setContentsMargins(0, 0, 0, 0)
        col_layout.addWidget(templates_widget, 0)

        templates_widget.currentItemChanged.connect(self._on_template_change)

        self._templates_widget = templates_widget

        return col_widget

    def _create_workfiles_widget(self, controller, parent):
        col_widget = QtWidgets.QWidget(parent)

        header_widget = QtWidgets.QWidget(col_widget)

        files_filter_input = PlaceholderLineEdit(header_widget)
        files_filter_input.setPlaceholderText("Filter files..")

        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(files_filter_input, 1)

        files_widget = MultiWorkAreaFilesWidget(controller, col_widget)

        col_layout = QtWidgets.QVBoxLayout(col_widget)
        col_layout.setContentsMargins(0, 0, 0, 0)
        col_layout.addWidget(header_widget, 0)
        col_layout.addWidget(files_widget, 1)

        files_filter_input.textChanged.connect(
            self._on_file_text_filter_change)

        self._files_filter_input = files_filter_input

        self._files_widget = files_widget

        return col_widget

    def set_window_on_top(self, on_top):
        """Set window on top of other windows.

        Args:
            on_top (bool): Show on top of other windows.
        """

        flags = self._default_window_flags
        if on_top:
            flags |= QtCore.Qt.WindowStaysOnTopHint
        if self.windowFlags() != flags:
            self.setWindowFlags(flags)

    def ensure_visible(self, use_context=True, save=True, on_top=False):
        """Ensure the window is visible.

        This method expects arguments for compatibility with previous variant
            of Workfiles tool.

        Args:
            use_context (Optional[bool]): DEPRECATED: This argument is
                ignored.
            save (Optional[bool]): Allow to save workfiles.
            on_top (Optional[bool]): Show on top of other windows.
        """

        save = True if save is None else save
        on_top = False if on_top is None else on_top

        is_visible = self.isVisible()
        self._controller.set_save_enabled(save)
        self.set_window_on_top(on_top)

        self.show()
        self.raise_()
        self.activateWindow()
        if is_visible:
            self.refresh()

    def refresh(self):
        """Trigger refresh of workfiles tool controller."""

        self._controller.reset()

    def showEvent(self, event):
        super(WorkfilesToolWindow, self).showEvent(event)
        self._show_timer.start()
        if self._first_show:
            self._first_show = False
            self.setStyleSheet(style.load_stylesheet())

    def keyPressEvent(self, event):
        """Custom keyPressEvent.

        Override keyPressEvent to do nothing so that Maya's panels won't
        take focus when pressing "SHIFT" whilst mouse is over viewport or
        outliner. This way users don't accidentally perform Maya commands
        whilst trying to name an instance.
        """

        pass

    def _on_show(self):
        self.refresh()

    def _on_template_change(self, template_item):
        data = {
            "template_name": template_item.text(),
            "folder_id": self._controller.current_folder_id,
            "task_name": self._controller.current_task_name,
            "task_type": self._controller.current_task_type,
        }
        self._controller.emit_event(
            "template_changed.started",
            data=data
        )
        self._controller._current_template_name = template_item.text()

    def _on_file_text_filter_change(self, text):
        self._files_widget.set_text_filter(text)

    def _on_refresh_clicked(self):
        self.refresh()

    def _on_controller_refresh_started(self):
        self._controller_refreshed = True

    def _on_controller_refresh_finished(self):
        pass

    def _on_open_finished(self, event):
        if event["failed"]:
            self._overlay_messages_widget.add_message(
                "Failed to open workfile",
                "error",
            )
        else:
            self.close()

    def _on_workarea_open_clicked(self):
        path = self._files_widget.get_selected_path()
        if not path:
            return
        self._controller.open_workfile(path)

    def _on_workarea_create_clicked(self):
        created_filepath = self._controller.create_new_workfile()

from qtpy import QtCore, QtWidgets, QtGui

from ayon_core import style
from ayon_core.resources import get_ayon_icon_filepath
from ayon_core.tools.utils import (
    PlaceholderLineEdit,
)

from ayon_wrap.workfiles import WorkfileToolController

from .files_widget_workarea import MultiWorkAreaFilesWidget


class WorkfilesToolWindow(QtWidgets.QDialog):
    """WorkFiles Window.

    Main windows of workfiles tool.

    Args:
        controller (AbstractWorkfilesFrontend): Frontend controller.
        parent (Optional[QtWidgets.QWidget]): Parent widget.

    """
    def __init__(self, controller=None, parent=None, launch_data=None):
        super().__init__(parent=parent)

        self.setWindowTitle("Work Files")
        self.setWindowIcon(QtGui.QIcon(get_ayon_icon_filepath()))
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)

        self._first_show = True

        if controller is None:
            controller = WorkfileToolController(launch_data=launch_data)

        self._controller = controller

        # Splitter
        split_widget = QtWidgets.QSplitter(self)

        # List of templates
        templates_widget = QtWidgets.QListWidget(split_widget)

        # Existing workfiles in workarea
        files_wrapper_widget = QtWidgets.QWidget(split_widget)

        # - header with filtering
        files_header_widget = QtWidgets.QWidget(files_wrapper_widget)

        files_filter_input = PlaceholderLineEdit(files_header_widget)
        files_filter_input.setPlaceholderText("Filter files..")

        header_layout = QtWidgets.QHBoxLayout(files_header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(files_filter_input, 1)

        # - list of workfiles
        files_widget = MultiWorkAreaFilesWidget(
            controller, files_wrapper_widget
        )

        files_wrapper_layout = QtWidgets.QVBoxLayout(files_wrapper_widget)
        files_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        files_wrapper_layout.addWidget(files_header_widget, 0)
        files_wrapper_layout.addWidget(files_widget, 1)

        # - add widgets to splitter
        split_widget.addWidget(templates_widget)
        split_widget.addWidget(files_widget)
        split_widget.setSizes([175, 275])

        btns_widget = QtWidgets.QWidget(self)
        workarea_btn_create = QtWidgets.QPushButton(
            "Create New", btns_widget
        )
        workarea_btn_open = QtWidgets.QPushButton(
            "Open", btns_widget
        )

        btns_layout = QtWidgets.QHBoxLayout(btns_widget)
        btns_layout.addStretch(1)
        btns_layout.addWidget(workarea_btn_create, 0)
        btns_layout.addWidget(workarea_btn_open, 0)

        # Window layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(split_widget, 1)
        main_layout.addWidget(btns_widget, 0)

        show_timer = QtCore.QTimer()
        show_timer.setInterval(0)

        show_timer.timeout.connect(self._on_show_timer)
        templates_widget.currentItemChanged.connect(self._on_template_change)
        workarea_btn_open.clicked.connect(self._on_workarea_open_clicked)
        workarea_btn_create.clicked.connect(self._on_workarea_create_clicked)

        files_filter_input.textChanged.connect(
            self._on_file_text_filter_change)

        controller.register_event_callback(
            "controller.reset.finished",
            self._on_controller_refresh_finished,
        )

        self._split_widget = split_widget

        self._files_filter_input = files_filter_input
        self._files_widget = files_widget

        self._templates_widget = templates_widget

        self._workarea_btn_open = workarea_btn_open
        self._workarea_btn_create = workarea_btn_create

        self._show_timer = show_timer
        self._show_timer_count = 0
        self._show_reset_needed = False

        self.resize(1260, 600)

    def refresh(self):
        """Trigger refresh of workfiles tool controller."""
        self._show_reset_needed = False
        self._controller.reset()

    def showEvent(self, event):
        super().showEvent(event)
        self._start_show_timer()
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

    def _start_show_timer(self):
        self._show_timer_count = 0
        self._show_timer.start()
        self._show_reset_needed = True

    def _on_show_timer(self):
        self._show_timer_count += 1
        if self._show_timer_count < 3:
            return
        self._show_timer.stop()
        if self._show_reset_needed:
            self.refresh()

    def _on_template_change(self, template_item):
        self._controller.set_template(template_item.text())

    def _on_file_text_filter_change(self, text):
        self._files_widget.set_text_filter(text)

    def _on_refresh_clicked(self):
        self.refresh()

    def _on_controller_refresh_finished(self):
        self._show_reset_needed = False
        visible_items = self._files_widget.has_visible_items()
        self._workarea_btn_open.setEnabled(visible_items)
        self._workarea_btn_create.setEnabled(not visible_items)
        self._fill_templates()

    def _fill_templates(self):
        template_names = self._controller.get_template_names()
        templates_widget = self._templates_widget
        existing_items = {}
        for idx in range(len(template_names)):
            item = templates_widget.item(idx)
            if not item:
                break
            existing_items[item.text()] = item

        for template_name in template_names:
            if template_name in existing_items:
                continue
            item = QtWidgets.QListWidgetItem(template_name, templates_widget)
            existing_items[template_name] = item

        for template_name, item in existing_items.items():
            if template_name not in template_names:
                templates_widget.removeItemWidget(item)

        if (
            templates_widget.count() > 0
            and templates_widget.currentRow() == -1
        ):
            templates_widget.setCurrentRow(0)

    def _on_workarea_open_clicked(self):
        path = self._files_widget.get_selected_path()
        if not path:
            return
        self._controller.open_workfile(path)
        self.close()

    def _on_workarea_create_clicked(self):
        self._controller.create_new_workfile()
        self.close()

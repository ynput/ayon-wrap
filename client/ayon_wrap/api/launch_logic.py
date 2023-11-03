import os
import sys
import logging
import traceback

from openpype.pipeline import install_host
from openpype.tools.utils import host_tools, get_openpype_qt_app
from openpype.lib import get_openpype_execute_args, run_detached_process

from ayon_wrap.api import WrapHost


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def safe_excepthook(*args):
    traceback.print_exception(*args)


def main(subprocess_args):
    """Main entrypoint to Wrap launching, called from pre hook."""
    log.debug("launch_main")
    sys.excepthook = safe_excepthook

    subprocess_args.pop(0)  # remove launch_logic

    host = WrapHost(subprocess_args[-1])
    install_host(host)

    os.environ["OPENPYPE_LOG_NO_COLORS"] = "False"
    app = get_openpype_qt_app()

    host_tools.show_tool_by_name("sceneinventory")

    app.exec_()
    run_detached_process(subprocess_args)


if __name__ == "__main__":
    main(sys.argv)

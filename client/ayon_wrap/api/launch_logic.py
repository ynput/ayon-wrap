import os
import sys
import subprocess
import collections
import logging
import asyncio
import functools
import traceback


from qtpy import QtCore

from openpype.lib import Logger
from openpype.tests.lib import is_in_tests
from openpype.pipeline import install_host, legacy_io
from openpype.modules import ModulesManager
from openpype.tools.utils import host_tools, get_openpype_qt_app



log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def safe_excepthook(*args):
    traceback.print_exception(*args)


def main(*subprocess_args):
    """Main entrypoint to Wrap launching, called from pre hook."""
    log.debug("launch_main")
    sys.excepthook = safe_excepthook
    sys.path.insert(0, "C:/test_ayon/ayon-wrap/client/ayon_wrap")
    import ayon_wrap

    host = ayon_wrap.api.WrapHost()
    install_host(host)

    os.environ["OPENPYPE_LOG_NO_COLORS"] = "False"
    app = get_openpype_qt_app()
    app.setQuitOnLastWindowClosed(False)

    host_tools.show_tool_by_name("workfiles", save=True)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main(sys.argv)

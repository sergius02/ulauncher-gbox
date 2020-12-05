import logging
import re
from datetime import datetime
from os.path import expanduser

from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

logger = logging.getLogger(__name__)


class GBox(Extension):

    def __init__(self):
        super(GBox, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

    def get_config_block(self, lines, index: int):
        result = {}
        i = index + 1
        block_line = lines[i]
        while block_line != "\n":
            prop = block_line.split("=")
            property_name = prop[0]
            property_value = prop[1]
            result[property_name] = property_value.rstrip()
            i += 1
            if i == len(lines):
                break
            block_line = lines[i]

        return result

    def searchBoxes(self, search_str):
        results = []
        pattern = re.compile(re.escape("[") + "display")

        config_lines = []
        qemu_path = self.preferences.get("gbox_sessions_path")
        with open(expanduser(qemu_path)) as boxesFile:
            config_lines = boxesFile.readlines()

        config_blocks = []
        for i, line in enumerate(config_lines):
            for match in re.finditer(pattern, line):
                config_blocks.append(self.get_config_block(config_lines, i))

        for block in config_blocks:
            if search_str == "Start typing..." \
                    or block["last-seen-name"].__contains__(search_str) \
                    or block["uuid"].__contains__(search_str):
                last_access = datetime.fromtimestamp(int(block["access-last-time"]) / 1000000)
                results.append(
                    ExtensionResultItem(
                        icon='images/icon.png',
                        name=block["last-seen-name"],
                        description="UUID: " + block["uuid"] +
                                    "\n" + block["access-ntimes"] + " access, last " + last_access.__str__(),
                        on_enter=RunScriptAction(
                            'gnome-boxes --open-uuid %s &' % block["uuid"],
                            []
                        ),
                        on_alt_enter=CopyToClipboardAction(block["uuid"])
                    )
                )

        return results


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        items = []
        text = event.get_argument() or "Start typing..."
        return RenderResultListAction(extension.searchBoxes(text))


if __name__ == '__main__':
    GBox().run()

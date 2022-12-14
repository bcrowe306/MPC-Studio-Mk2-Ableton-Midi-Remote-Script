#Embedded file name: /Users/versonator/Jenkins/live/output/Live/mac_64_static/Release/python-bundle/MIDI Remote Scripts/ATOM/channel_strip.py
from __future__ import absolute_import, print_function, unicode_literals
from ableton.v2.base import liveobj_valid, listens
from ableton.v2.control_surface.control import ButtonControl
from ableton.v2.control_surface.components import ChannelStripComponent as ChannelStripComponentBase

class ChannelStripComponent(ChannelStripComponentBase):
    empty_color = u'Mixer.EmptyTrack'
    input_routing_channel_button = ButtonControl()

    def __init__(self, *a, **k):
        super(ChannelStripComponent, self).__init__(*a, **k)
        
    def _update_select_button(self):
        if liveobj_valid(self._track) and self.song.view.selected_track == self._track:
            self.select_button.color = u'Mixer.Selected'
        else:
            self.select_button.color = u'Mixer.EmptyTrack'
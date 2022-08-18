from __future__ import absolute_import, print_function, unicode_literals
from ableton.v2.base import const, inject, listens, liveobj_valid
from ableton.v2.control_surface import ControlSurface, Layer, PercussionInstrumentFinder
from ableton.v2.control_surface.components import ArmedTargetTrackComponent, BackgroundComponent, SessionNavigationComponent, SessionOverviewComponent, SessionRingComponent, SimpleTrackAssigner, AutoArmComponent
from ableton.v2.control_surface.mode import AddLayerMode, LayerMode, ModesComponent, MomentaryBehaviour
from ableton.v2.control_surface.control.button import ButtonControl
from . import midi
from .channel_strip import ChannelStripComponent
from .drum_group import DrumGroupComponent
from .elements import Elements, SESSION_HEIGHT, SESSION_WIDTH
from .keyboard import KeyboardComponent
from .lighting import LightingComponent
from .mixer import MixerComponent
from .session import SessionComponent
from .skin import skin
from .translating_background import TranslatingBackgroundComponent
from .view_toggle import ViewToggleComponent
from .undo import  NewUndoComponent
from .jog_wheel import TrackSelectComponent
from .transport import TransportComponent
from .touch_strip import TouchStrip
from .session_recording import SessionRecordingComponent
import logging
logger = logging.getLogger(__name__)

class MPCStudioMk2(ControlSurface):

    def __init__(self, *a, **k):
        (super(MPCStudioMk2, self).__init__)(*a, **k)
        with self.component_guard():
            with inject(skin=(const(skin))).everywhere():
                self._elements = Elements()
        with self.component_guard():
            with inject(element_container=(const(self._elements))).everywhere():
                self._set_button_colors()
                self._create_lighting()
                self._create_undo()
                self._create_view_toggle()
                self._create_background()
                self._create_jog_wheel()
                self._create_auto_arm()
                self._create_session()
                self._create_touch_strip()
                self._create_touch_strip_modes()
                self._create_mixer()
                self._create_session_navigation_modes()
                self._create_keyboard()
                self._create_drum_group()
                self._create_note_modes()
                self._create_pad_modes()
                self._create_transport()
                self._create_record_modes()
                self._target_track = ArmedTargetTrackComponent(name='Target_Track')
                self.__on_target_track_changed.subject = self._target_track
        self._drum_group_finder = self.register_disconnectable(PercussionInstrumentFinder(device_parent=(self._target_track.target_track)))
        self.__on_drum_group_changed.subject = self._drum_group_finder
        self.__on_drum_group_changed()
        self.__on_main_view_changed.subject = self.application.view
        self._enable_session_ring()
        self.__on_selected_mode_change.subject = self._pad_modes
        self.show_message('---MPC Studio Mk2: Active')

    def _set_button_colors(self):
        self._elements.sample_start_button.color = 'UpDownButton.Off'

    def disconnect(self):
        self._set_pad_led_disabled()
        super(MPCStudioMk2, self).disconnect()

    def _create_jog_wheel(self):
        self._track_select = TrackSelectComponent(
            name='TrackSelect', 
            is_enabled=False, 
            layer=Layer(
                jog_wheel_button='jog_wheel',
                jog_wheel_press='jog_wheel_button'))
        self._track_select.set_enabled(True)

    def _create_auto_arm(self):
        self._auto_arm = AutoArmComponent(is_enabled=False)
        self._auto_arm.set_enabled(True)

    def _create_lighting(self):
        self._lighting = LightingComponent(name='Lighting',
          is_enabled=False,
          layer=Layer(shift_button='shift_button', zoom_button='zoom_button'))
        self._lighting.set_enabled(True)

    def _create_transport(self):
        self._transport = TransportComponent(name='Transport',
          is_enabled=False,
          layer=Layer(priority=5, 
          play_button='play_button',
          loop_button='play_start_button',
          stop_button='stop_button',
          metronome_button='tune_button',
          tap_tempo_button='tap_tempo_button'))
        self._transport.set_enabled(True)
        self._transport.set_seek_forward_button(self._elements.seek_forward_button)
        self._transport.set_seek_backward_button(self._elements.seek_back_button)
        self._transport.set_arrangement_overdub_button(self._elements.overdub_button)
        self._transport.set_punch_in_button(self._elements.nudge_left_button)
        self._transport.set_punch_out_button(self._elements.nudge_right_button)

    def _create_record_modes(self):
        self._session_record = SessionRecordingComponent(name='Session_Record',
          is_enabled=False,
          layer=Layer(record_button='record_button',
          automation_button='automation_rw_button'))
        self._record_modes = ModesComponent(name='Record_Modes')
        self._record_modes.add_mode('session', self._session_record)
        self._record_modes.add_mode('arrange', AddLayerMode((self._transport), layer=Layer(record_button='record_button')))
        self.__on_main_view_changed()

    def _create_undo(self):
        self._undo = NewUndoComponent(name='Undo',
          is_enabled=False,
          layer=Layer(undo_button='undo_button', redo_button='undo_button_with_shift'))
        self._undo.set_enabled(True)

    def _create_view_toggle(self):
        self._view_toggle = ViewToggleComponent(name='View_Toggle',
          is_enabled=False,
          layer=Layer(
            detail_view_toggle_button='program_select_button',
            main_view_toggle_button='main_button',
            browser_view_toggle_button='browse_button'))
        self._view_toggle.set_enabled(True)

    def _create_background(self):
        self._background = BackgroundComponent(name='Background',
          is_enabled=False,
          add_nop_listeners=True,
          layer=Layer(set_loop_button='locate_button',
          nudge_button='level_16_button',
          bank_button='copy_button'))
        self._background.set_enabled(True)

    def _create_session(self):
        self._session_ring = SessionRingComponent(name='Session_Ring',
          is_enabled=False,
          num_tracks=SESSION_WIDTH,
          num_scenes=SESSION_HEIGHT)
        self._session = SessionComponent(name='Session', session_ring=(self._session_ring))
        self._session_navigation = SessionNavigationComponent(name='Session_Navigation',
          is_enabled=False,
          session_ring=(self._session_ring),
          layer=Layer(left_button='minus_button', right_button='plus_button'))
        self._session_navigation.set_enabled(True)
        self._session_overview = SessionOverviewComponent(name='Session_Overview',
          is_enabled=False,
          session_ring=(self._session_ring),
          enable_skinning=True,
          layer=Layer(button_matrix='pads_with_zoom'))
    
    def _create_touch_strip(self):
        self._touch_strip = TouchStrip(is_enabled=True)

    def _create_mixer(self):
        self._mixer = MixerComponent(name='Mixer',
          auto_name=True,
          tracks_provider=(self._session_ring),
          track_assigner=(SimpleTrackAssigner()),
          invert_mute_feedback=True,
          channel_strip_component_type=ChannelStripComponent)

    def _create_touch_strip_modes(self):
        self._touch_strip_modes = ModesComponent(name='touch_strip_modes', enable_skinning=True)
        self._touch_strip_modes.add_mode('volume', AddLayerMode(self._touch_strip, Layer(volume_control='touch_strip_control')))
        self._touch_strip_modes.add_mode('pan', AddLayerMode(self._touch_strip, Layer(pan_control='touch_strip_control')))
        self._touch_strip_modes.add_mode('send_a', AddLayerMode(self._touch_strip, Layer(send_a_control='touch_strip_control')))
        self._touch_strip_modes.add_mode('send_b', AddLayerMode(self._touch_strip, Layer(send_b_control='touch_strip_control')))
        self._touch_strip_modes.selected_mode = 'volume'

    def _create_session_navigation_modes(self):
        self._session_navigation_modes = ModesComponent(name='Session_Navigation_Modes',
          is_enabled=False,
          layer=Layer(cycle_mode_button='mode_button'))

        self._session_navigation_modes.add_mode('default',
            AddLayerMode((self._session_navigation),
                layer=Layer(up_button='sample_start_button', down_button='sample_end_button')),
                cycle_mode_button_color='DefaultButton.Off')

        self._session_navigation_modes.add_mode('paged',
            AddLayerMode((self._session_navigation),
                layer=Layer(page_up_button='sample_start_button',
                page_down_button='sample_end_button',
                page_left_button='minus_button',
                page_right_button='plus_button')),
                cycle_mode_button_color='DefaultButton.On')
        self._session_navigation_modes.selected_mode = 'default'

    def _create_keyboard(self):
        self._keyboard = KeyboardComponent((midi.KEYBOARD_CHANNEL),
          name='Keyboard',
          is_enabled=False,
          layer=Layer(matrix='pads',
          scroll_up_button='sample_start_button',
          scroll_down_button='sample_end_button'))

    def _create_drum_group(self):
        self._drum_group = DrumGroupComponent(name='Drum_Group',
          is_enabled=False,
          translation_channel=(midi.DRUM_CHANNEL),
          layer=Layer(matrix='pads',
          scroll_page_up_button='sample_start_button',
          scroll_page_down_button='sample_end_button'))

    def _create_note_modes(self):
        self._note_modes = ModesComponent(name='Note_Modes', is_enabled=False)
        self._note_modes.add_mode('keyboard', self._keyboard)
        self._note_modes.add_mode('drum', self._drum_group)
        self._note_modes.selected_mode = 'keyboard'
        
    def _create_pad_modes(self):
        self._pad_modes = ModesComponent(name='Pad_Modes',
            enable_skinning=True,
            is_enabled=False,
            layer=Layer(
                session_button='pad_bank_ae_button',
                note_button='pad_bank_bf_button',
                channel_button='pad_bank_cg_button',
                touch_strip_modes_button='touch_strip_button'))

        self._pad_modes.add_mode('session', (
            AddLayerMode(self._background, Layer(unused_pads='pads_with_shift')),
            AddLayerMode(self._session, Layer(
                clip_launch_buttons='pads',
                scene_launch_buttons=(self._elements.pads_with_shift.submatrix[3:, :]))),
            self._session_overview,
            self._session_navigation_modes))

        self._pad_modes.add_mode('note', self._note_modes)

        self._pad_modes.add_mode('channel', (
            self._elements.pads.reset,
            AddLayerMode(self._mixer, 
                Layer(
                    track_select_buttons=( self._elements.pads.submatrix[:, :1] ),
                    arm_buttons=( self._elements.pads.submatrix[:, 3:] ),
                    solo_buttons=( self._elements.pads.submatrix[:, 2:3] ),
                    mute_buttons=( self._elements.pads.submatrix[:, 1:2] )
                    ),),
                self._session_navigation_modes
                ),
        )
        # AddLayerMode(self._session, Layer(stop_track_clip_buttons=(self._elements.pads.submatrix[:, :1]))),

        self._pad_modes.add_mode('touch_strip_modes',
          (LayerMode(self._touch_strip_modes, Layer(
            volume_button=(self._elements.pads_raw[0][0]),
            pan_button=(self._elements.pads_raw[0][1]),
            send_a_button=(self._elements.pads_raw[0][2]),
            send_b_button=(self._elements.pads_raw[0][3]))),
         AddLayerMode(self._background, Layer(unused_pads=(self._elements.pads.submatrix[:, 1:])))),
          behaviour=(MomentaryBehaviour()))
        self._pad_modes.selected_mode = 'session'
        self._pad_modes.set_enabled(True)

    def _set_pad_led_disabled(self):

        # Set all pads to black rgb color:
        for pad in range(15):
            self._send_midi( (240, 71, 71, 74, 101, 0, 4, pad, 0, 0, 0, 247) )

    @listens('is_view_visible', 'Session')
    def __on_main_view_changed(self):
        if self.application.view.is_view_visible('Session'):
            self._record_modes.selected_mode = 'session'
        else:
            self._record_modes.selected_mode = 'arrange'
    
    @listens('selected_mode')
    def __on_selected_mode_change(self, value):
        pass
        # logger.warn(value)
        # logger.warn(self._pad_modes.get_mode(value)._modes[1]._layer._element_to_names)

    @listens('target_track')
    def __on_target_track_changed(self):
        self._drum_group_finder.device_parent = self._target_track.target_track

    @listens('instrument')
    def __on_drum_group_changed(self):
        drum_group = self._drum_group_finder.drum_group
        self._drum_group.set_drum_group_device(drum_group)
        self._note_modes.selected_mode = 'drum' if liveobj_valid(drum_group) else 'keyboard'

    def _enable_session_ring(self):
        self._session_ring.set_enabled(True)
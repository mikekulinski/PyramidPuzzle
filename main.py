# common imports
import sys

sys.path.append("..")
from common.core import BaseWidget, run
from common.gfxutil import (
    topleft_label,
    Cursor3D,
    AnimGroup,
    KFAnim,
    scale_point,
    CEllipse,
)
from common.synth import Synth
from common.audio import Audio

from kivy.core.window import Window
import numpy as np
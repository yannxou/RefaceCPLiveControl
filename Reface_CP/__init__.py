from __future__ import absolute_import, print_function, unicode_literals
import Live
from _Framework.Capabilities import *
from .RefaceCPControlSurface import RefaceCPControlSurface
from .RefaceCP import VENDOR_ID, PRODUCT_ID, MODEL_NAME

def create_instance(c_instance):
    return RefaceCPControlSurface(c_instance)

def get_capabilities():
    return {CONTROLLER_ID_KEY: (controller_id(vendor_id=RefaceCP.VENDOR_ID,
                          product_ids=[RefaceCP.PRODUCT_ID],
                          model_name=[RefaceCP.MODEL_NAME])),
     
     PORTS_KEY: [
                 inport(props=[NOTES_CC, REMOTE, SCRIPT]),
                 outport(props=[NOTES_CC, REMOTE, SCRIPT])]}
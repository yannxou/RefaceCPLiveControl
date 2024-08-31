from __future__ import absolute_import, print_function, unicode_literals
import Live
from _Framework.Capabilities import *
from .RefaceCPControlSurface import RefaceCPControlSurface

def create_instance(c_instance):
    return RefaceCPControlSurface(c_instance)

def get_capabilities():
    return {CONTROLLER_ID_KEY: (controller_id(vendor_id=5667,
                          product_ids=[1177],
                          model_name=["reface CP"])),
     
     PORTS_KEY: [
                 inport(props=[NOTES_CC, REMOTE, SCRIPT]),
                 outport(props=[NOTES_CC, REMOTE, SCRIPT])]}
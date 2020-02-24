# -*- coding: utf-'8' "-*-"
import platform
import os
import socket


def is_production_server():

    if platform.system() != 'Linux':
        return False

    if not os.path.exists('/opt/online'):
        return False

    if not os.path.exists('/opt/online/online_tools'):
        return False

    if not os.path.exists('/var/log/online'):
        return False

    if 'online' not in socket.gethostname():
        return False

    return True

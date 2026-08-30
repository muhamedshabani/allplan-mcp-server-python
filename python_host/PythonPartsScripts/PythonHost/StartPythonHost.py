
from __future__ import annotations
import sys
import os
import json
import traceback
import clr

from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import List

import NemAll_Python_IFW_Input as AllplanIFW

from .PythonHostHandler import RequestHandler
from .security import (
    BridgeAuthError,
    BridgeSecurityPolicy,
    generate_token,
    write_token,
)
from BuildingElement import BuildingElement
from BuildingElementComposite import BuildingElementComposite
from BuildingElementControlProperties import BuildingElementControlProperties
from BuildingElementPaletteService import BuildingElementPaletteService
from StringTableService import StringTableService
from TypeCollections.ModificationElementList import ModificationElementList

from System import Object, Func, TimeSpan
from System.Windows import Application
from System.Windows.Threading import DispatcherTimer

os.environ["LIBRARY_ROOTS"] = ";".join(sys.path)


print("Load StartPythonHost.py")

def check_allplan_version(_build_ele: BuildingElement,
                          _version  : str):
    """ Check the current Allplan version

    Args:
        _build_ele: the building element.
        _version:   the current Allplan version

    Returns:
        True/False if version is supported by this script
    """

    return True

def invoke_in_ui_thread(func):
    """ Executes provided function on UI thread

    Args:
        func: Function to execute

    Returns:
        The same object that func returns
    """

    return Application.Current.Dispatcher.Invoke(Func[Object](func))


# http POST handler

class WebRequestHandler(BaseHTTPRequestHandler):
    """ Implementation that handles requests from HTTP server

    Args:
        BaseHTTPRequestHandler: base HTTP handler
    """

    request_handler : RequestHandler
    security_policy : BridgeSecurityPolicy

    def send_json(self, status: int, payload: dict):
        """ Sends one JSON response

        Args:
            status:  HTTP status code
            payload: JSON serializable body
        """

        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        """ Handles HTTP POST request
        """

        try:
            self.security_policy.authorize(self.headers)
        except BridgeAuthError as error:
            self.send_json(error.status, {"ok": False, "error": str(error)})
            return

        try:
            content_len = int(self.headers.get("Content-Length") or 0)
            request = None

            if (content_len > 0):
                request_json = self.rfile.read(content_len)
                request = json.loads(request_json)

            result = invoke_in_ui_thread(
                lambda: self.request_handler.handle(self.path, request)
            )
        except:
            error = traceback.format_exc()
            self.send_json(500, {"ok": False, "error": str(error)})
        else:
            self.send_json(200, result if result is not None else {})

    def log_message(self, format, *args):
        """ Routes access logs to the Allplan trace window
        """

        print("PythonHost %s - %s" % (self.address_string(), format % args))

# entry point

def create_interactor(coord_input             : AllplanIFW.CoordinateInput,
                      pyp_path                : str,
                      global_str_table_service: StringTableService,
                      build_ele_list          : List[BuildingElement],
                      build_ele_composite     : BuildingElementComposite,
                      control_props_list      : List[BuildingElementControlProperties],
                      modification_ele_list   : ModificationElementList) -> PythonHostInteractor:
    """ Create the interactor

    Args:
        coord_input:              API object for the coordinate input, element selection, ... in the Allplan view
        pyp_path:                 path of the pyp file
        global_str_table_service: global string table service
        build_ele_list:           list with the building elements
        build_ele_composite:      building element composite with the building element constraints
        control_props_list:       control properties list
        modification_ele_list:    list with the UUIDs of the modified elements

    Returns:
          Created interactor object
    """

    return PythonHostInteractor(coord_input, 
                                pyp_path, 
                                global_str_table_service,
                                build_ele_list, 
                                build_ele_composite, 
                                control_props_list, 
                                modification_ele_list)


class PythonHostInteractor():
    """ Definition of class PythonHostInteractor
    """
    
    def __init__(self,
                 coord_input             : AllplanIFW.CoordinateInput,
                 pyp_path                : str,
                 global_str_table_service: StringTableService,
                 build_ele_list          : List[BuildingElement],
                 build_ele_composite     : BuildingElementComposite,
                 control_props_list      : List[BuildingElementControlProperties],
                 modification_ele_list   : ModificationElementList):
        """ Create the interactor

        Args:
            coord_input:              API object for the coordinate input, element selection, ... in the Allplan view
            pyp_path:                 path of the pyp file
            global_str_table_service: global string table service
            build_ele_list:           list with the building elements
            build_ele_composite:      building element composite with the building element constraints
            control_props_list:       control properties list
            modification_ele_list:    UUIDs of the existing elements in the modification mode

        Returns:
            Created interactor object
        """
        
        self.coord_input = coord_input
        self.build_ele_list = build_ele_list
        self.build_ele_composite = build_ele_composite
        self.control_props_list = control_props_list

        # show the palette
        self.palette_service = BuildingElementPaletteService(self.build_ele_list,
                                                             self.build_ele_composite,
                                                             None,
                                                             self.control_props_list,
                                                             "StartPythonHost.pyp")
        
        build_ele = self.build_ele_list[0]
        self.palette_service.show_palette(build_ele.script_name)

        # start http server
        address = "127.0.0.1"
        port = 5679

        # mint a per-session token and publish it for local MCP clients
        self.token = generate_token()
        self.token_path = write_token(self.token)

        self.server = HTTPServer((address, port), WebRequestHandler)
        self.server.allow_reuse_address = True
        self.server.RequestHandlerClass.request_handler = RequestHandler(self.coord_input)
        self.server.RequestHandlerClass.security_policy = BridgeSecurityPolicy(token=self.token)

        thread = Thread(target=self.start_server)
        thread.daemon = True
        thread.start()

        print("Python Host is started")
        print(f"Bridge token written to {self.token_path}")
        
        # this timer pushes python thread to process requests if user minimized main window
        self.timer = DispatcherTimer()
        self.timer.Interval = TimeSpan.FromMilliseconds(50)
        self.timer.Tick += self.push_python_thread
        self.timer.Start()
    
    @staticmethod
    def push_python_thread(sender, args):
        # do nothing
        return

    def start_server(self):
        """ Starts HTTP server
        """

        try:
            self.server.serve_forever()
        except Exception as err:
            print(f"Python Host failed to start:\n{err}")
               
    def on_cancel_function(self) -> bool:
        """ Handles the cancel function event (e.g. by ESC, ...)

        Returns:
            True/False for success.
        """
        
        self.server.server_close()
        self.palette_service.close_palette()
        self.timer.Stop()

        try:
            self.token_path.unlink()
        except OSError:
            pass
        print("Python Host is stopped")

        return True
    
    def process_mouse_msg(self, mouse_msg, pnt, msg_info) -> bool:     
        return True
    
    def on_preview_draw(self):
        return
            
    def on_mouse_leave(self):
        return
    

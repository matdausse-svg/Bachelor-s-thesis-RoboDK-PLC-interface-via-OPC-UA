# Generisch4: OPC UA client that runs as a Python program inside a RoboDK station.
# It exchanges program selection, start/stop commands and IO states with a
# CODESYS PLC (OPC UA server, endpoint opc.tcp://localhost:4840).
# English version of the comments; the logic is the one used in the thesis.

from robodk import robolink
from robodk.robolink import ITEM_TYPE_PROGRAM, ITEM_TYPE_PROGRAM_PYTHON
from opcua import Client, ua
import time

print("=== START RoboDK / OPC UA SCRIPT ===")

# ============================================================
# RoboDK connection
# ------------------------------------------------------------
# Connects to the RoboDK station that is currently open.
# Through this interface, programs are started, parameters are
# read/written and IO states are queried.
# ============================================================
RDK = robolink.Robolink()

# ============================================================
# OPC UA connection (CODESYS PLC)
# ------------------------------------------------------------
# Connects to the OPC UA server of the CODESYS runtime.
# This server exposes all PLC variables needed to communicate
# with RoboDK.
# ============================================================
client = Client("opc.tcp://localhost:4840")
client.connect()
print("OPC UA connected")

# ============================================================
# OPC UA nodes (PLC variables)
# ------------------------------------------------------------
# All relevant PLC variables are referenced once here,
# through their node path.
# ============================================================
node_names = client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.GVL.Comb_names")
node_nb = client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.GVL.Nb_Programs")
node_sel = client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.GVL.Selected_Index")
node_trigger = client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.GVL.Trigger")
node_stop = client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.GVL.Stop")

# IO commands from the PLC (start IOs)
node_io_cmd = client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.GVL.IO_")

# Feedback: a program is running (real status read from RoboDK)
node_io_run = client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.GVL.IO_Run")

# Program currently running
node_cur = client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.GVL.Current_Program")

# ============================================================
# Constants
# ------------------------------------------------------------
# Maximum number of supported programs / IOs
# ============================================================
MAX = 50

# ============================================================
# Internal states (Python script only)
# ------------------------------------------------------------
# These variables are used for clean edge detection and
# for the internal sequence control.
# ============================================================
prev_trigger = False                   # Trigger edge detection
prev_io_cmd = [False] * MAX            # IO edge detection

program_running = False                # internal running state
current_program_item = None            # current RoboDK program object
current_program_is_python = False      # program type (standard / Python)

# ============================================================
# Initialization
# ------------------------------------------------------------
# All IOs are explicitly set to 0 at startup to guarantee
# a defined initial state.
# ============================================================
for i in range(1, MAX + 1):
    RDK.setParam(f"IO_{i}", "0")

# ============================================================
# Main loop
# ------------------------------------------------------------
# Cyclic processing:
# - update the program list
# - evaluate PLC inputs
# - synchronize IOs
# - start / stop programs
# ============================================================
while True:
    try:
        # ====================================================
        # Read the program list from RoboDK
        # ----------------------------------------------------
        # All programs whose parameter name starts with "CMD_"
        # are considered controllable programs.
        # ====================================================
        params = RDK.getParams()
        cmd_programs = [n for n, v in params if n.startswith("CMD_")]

        names = cmd_programs + [""] * (MAX - len(cmd_programs))
        node_names.set_value(ua.Variant(names, ua.VariantType.String))
        node_nb.set_value(ua.Variant(len(cmd_programs), ua.VariantType.Int16))

        # ====================================================
        # Read PLC variables
        # ====================================================
        sel = node_sel.get_value()
        trigger = node_trigger.get_value()
        stop_cmd = node_stop.get_value()
        io_cmd = list(node_io_cmd.get_value())

        # ====================================================
        # PLC -> RoboDK: IO_n (rising edge only)
        # ----------------------------------------------------
        # This prevents IOs from being overwritten cyclically
        # or set several times.
        # ====================================================
        for i in range(1, MAX + 1):
            plc_val = bool(io_cmd[i - 1])

            if plc_val and not prev_io_cmd[i - 1]:
                print(f"[PLC->RDK] Rising edge IO_{i}")
                RDK.setParam(f"IO_{i}", "1")

            prev_io_cmd[i - 1] = plc_val

        # ====================================================
        # RoboDK -> PLC: IO feedback
        # ----------------------------------------------------
        # The real IO state from RoboDK is reported back to the
        # PLC (no virtual feedback).
        # ====================================================
        io_feedback = [False] * MAX

        for i in range(1, MAX + 1):
            val = RDK.getParam(f"IO_{i}")
            try:
                io_feedback[i - 1] = bool(int(val))
            except:
                io_feedback[i - 1] = False

        node_io_cmd.set_value(ua.Variant(io_feedback, ua.VariantType.Boolean))

        # ====================================================
        # IO_Run
        # ----------------------------------------------------
        # IO_Run is set exclusively by the RoboDK programs
        # themselves (standard and Python).
        # This script only reads the state.
        # ====================================================
        io_run_raw = RDK.getParam("IO_Run")
        io_run = bool(int(io_run_raw)) if io_run_raw else False
        node_io_run.set_value(io_run)

        # ====================================================
        # STOP command from the PLC
        # ====================================================
        if stop_cmd:
            print("STOP received")

            try:
                if current_program_item and current_program_item.Valid():
                    current_program_item.Stop()
            except:
                pass

            # Reset all IOs
            for i in range(1, MAX + 1):
                RDK.setParam(f"IO_{i}", "0")

            RDK.setParam("IO_Run", "0")

            node_io_cmd.set_value(ua.Variant([False] * MAX, ua.VariantType.Boolean))
            node_cur.set_value("")
            node_stop.set_value(False)

            program_running = False
            current_program_item = None
            current_program_is_python = False

        # ====================================================
        # START command
        # ====================================================
        if trigger and not prev_trigger and not program_running:
            if 1 <= sel <= len(cmd_programs):
                prog_name = names[sel - 1].replace("CMD_", "")

                prog = RDK.Item(prog_name)
                if not prog.Valid():
                    raise Exception("RoboDK program not found")

                # Show the current program in the PLC
                node_cur.set_value(prog_name)
                print(prog_name)

                if prog.Type() == ITEM_TYPE_PROGRAM_PYTHON:
                    current_program_is_python = True
                    RDK.setParam("running", "1")
                    RDK.RunCode(prog_name)
                else:
                    current_program_is_python = False
                    prog.RunProgram()

                program_running = True
                current_program_item = prog
                node_trigger.set_value(False)

        prev_trigger = trigger

        # ====================================================
        # Detect the end of the program
        # ====================================================
        if program_running:
            if current_program_is_python:
                io_running = RDK.getParam("running")
                finished = not bool(int(io_running)) if io_running else True
            else:
                finished = not current_program_item.Busy()

            if finished:
                print("Program finished")

                program_running = False
                current_program_item = None
                current_program_is_python = False
                node_cur.set_value("")

        time.sleep(0.09)
    except Exception as e:
        print("ERROR:", e)
        time.sleep(0.5)

"""cableutils
"""

# ***************************************************************************
# *   Copyright 2025 SargoDevel <sargo-devel at o2 dot pl>                  *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENSE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Lesser General Public License for more details.                   *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************/


import FreeCAD
from freecad.cables import wireutils


def attach_in_place(obj_list):
    """It makes attachment of objects without changing their current global
    position.
    The global position is converted into Attachment Offset.
    Last element in the obj_list is treated as the Attachment Support for other
    objects in the list. The Map Mode is always "ObjectXY"
    """
    att_supp = obj_list[-1]
    for s in obj_list[:-1]:
        att_off = att_supp.Placement.inverse().multiply(s.Placement)
        s.AttachmentSupport = [(att_supp, ('',))]
        s.MapMode = "ObjectXY"
        s.AttachmentOffset = att_off


def deactivate_attachment(obj_list):
    """It deactivates attachment of objects in obj_list
    """
    if obj_list:
        for s in obj_list:
            s.MapMode = "Deactivated"


def detect_selected_wire_side(sel_list, vect):
    """It calculates selected wire side before attachment to terminal.
    Returns: "start", "end" or None
    """
    if sel_list is None or len(sel_list) < 2:
        FreeCAD.Console.PrintError("attach_wire_to_terminal",
                                   "Not enough objects selected\n")
        return None
    try:
        if type(sel_list[0][0].Proxy).__name__ == "WireFlex":
            wire = sel_list[0][0]
        else:
            raise TypeError
    except TypeError:
        FreeCAD.Console.PrintError("attach_wire_to_terminal",
                                   "Wrong objects selected\n")
        return None
    if vect is not None and not isSubwireOfCable(wire) and \
       wireutils.getWireHalf(wire.Shape.Wires[0], vect) == 1:
        return "start"
    else:
        return "end"


def attach_wire_to_terminal(sel_list, side):
    """It attaches wire end to terminal
    """
    if sel_list is None or len(sel_list) < 2:
        FreeCAD.Console.PrintError("attach_wire_to_terminal",
                                   "Not enough objects selected\n")
        return
    try:
        if type(sel_list[0][0].Proxy).__name__ == "WireFlex":
            wire = sel_list[0][0]
        else:
            raise TypeError
        if type(sel_list[1][0].Proxy).__name__ == "CableTerminal":
            terminal = sel_list[1][0]
            tvrtx = sel_list[1][1]
        else:
            raise TypeError
    except TypeError:
        FreeCAD.Console.PrintError("attach_wire_to_terminal",
                                   "Wrong objects selected\n")
        return
    if side == "start":
        # selected point is in a first half of wire
        update_wire_points(wire, "s")
        wire_v1 = "Vertex2"
        wire_v2 = "Vertex1"
    else:
        # select wire end
        update_wire_points(wire, 'e')
        wire_v1 = "Vertex" + str(len(wire.Shape.Vertexes)-1)
        wire_v2 = "Vertex" + str(len(wire.Shape.Vertexes))
    if tvrtx:
        # get selected pair of terminal vertices
        term_v1 = tvrtx
        nr = int(tvrtx.strip("Vertx"))
        conn_nr = nr//2 + nr % 2
        occupied_lst = [int(c.split(":")[0]) for c in terminal.ConnectedWires]
        free_conn_lst = sorted(set(range(1, terminal.NumberOfConnections+1)
                                   ).difference(set(occupied_lst)))
        if conn_nr not in free_conn_lst:
            FreeCAD.Console.PrintError(
                "attach_wire_to_terminal", f"{terminal.Label}, connection " +
                f"{conn_nr} is already occupied\n")
            return
        if nr <= terminal.NumberOfConnections*2:
            if nr % 2:
                term_v2 = "Vertex" + str(nr+1)
            else:
                term_v2 = "Vertex" + str(nr-1)
    else:
        # auto detection of free terminal vertices
        conn = get_free_terminal_connection(terminal)
        if conn is not None:
            term_v1 = "Vertex" + str(conn[0])
            term_v2 = "Vertex" + str(conn[1])
        else:
            term_v1 = None
            term_v2 = None
    if term_v1 and term_v2:
        wireutils.assignPointAttachment([(wire, wire_v1), (terminal, term_v1)])
        wireutils.assignPointAttachment([(wire, wire_v2), (terminal, term_v2)])
        terminal.touch()


def detach_wire_from_terminal(obj_list, verbose=False):
    """It detaches wire end from terminal
    """
    if len(obj_list) < 2:
        FreeCAD.Console.PrintError("detach_wire_from_terminal",
                                   "Not enough objects selected\n")
        return
    try:
        for w in obj_list[:-1]:
            if type(w.Proxy).__name__ != "WireFlex":
                raise TypeError
        if type(obj_list[-1].Proxy).__name__ != "CableTerminal":
            raise TypeError
    except TypeError:
        FreeCAD.Console.PrintError("attach_wire_to_terminal",
                                   "Wrong objects selected\n")
        return
    term = obj_list[-1]
    wires = obj_list[:-1]
    for w in wires:
        if w.Vrtx_start and w.Vrtx_start[0] == term:
            v1 = "Vertex1"
            v2 = "Vertex2"
            wireutils.removePointAttachment([(w, v1)])
            wireutils.removePointAttachment([(w, v2)])
            if verbose:
                FreeCAD.Console.PrintWarning(
                    "detach_wire_from_terminal", f"{w.Label} removed from " +
                    f"{term.Label}\n")
        if w.Vrtx_end and w.Vrtx_end[0] == term:
            v1 = "Vertex" + str(len(w.Shape.Vertexes)-1)
            v2 = "Vertex" + str(len(w.Shape.Vertexes))
            wireutils.removePointAttachment([(w, v1)])
            wireutils.removePointAttachment([(w, v2)])
            if verbose:
                FreeCAD.Console.PrintWarning(
                    "detach_wire_from_terminal", f"{w.Label} removed from " +
                    f"{term.Label}\n")
    term.recompute()


def get_free_terminal_connection(term):
    """It returns a free pair of available vertex numbers
    """
    nr_all = term.NumberOfConnections
    occupied_lst = [int(c.split(":")[0]) for c in term.ConnectedWires]
    free_lst = sorted(set(range(1, nr_all+1)).difference(set(occupied_lst)))
    if not free_lst:
        FreeCAD.Console.PrintError(
            "get_free_terminal_connection", f"terminal {term.Label} is " +
            "already occupied\n")
        return None
    free_nr = free_lst[0]
    return [2*free_nr-1, 2*free_nr]


def update_wire_points(wire, tip):
    """It adds a point at the beginning (tip='s') or at the end (tip='e')
    of the wire if number of points is < 4.
    """
    def _add_point(wire, tip):
        if tip == 's':
            wireutils.addPointToWire([(wire, 'Edge1')])
        if tip == 'e':
            nr = len(wire.Shape.Edges)
            wireutils.addPointToWire([(wire, 'Edge'+str(nr))])
        FreeCAD.ActiveDocument.recompute()

    if len(wire.Points) < 4:
        _add_point(wire, tip)
        if len(wire.Points) < 4:
            _add_point(wire, tip)


def isSubwireOfCable(wire):
    """It checks if wire is one of cable subwires.
    If yes it returns True, otherwise False
    """
    cable = False
    for obj in wire.InList:
        try:
            if hasattr(obj, "Proxy") and \
               type(obj.Proxy).__name__ == "ArchCable":
                if wire in obj.SubWires:
                    cable = True
                    break
        except AttributeError:
            pass
    return cable

import FreeCAD, FreeCADGui, Part
from PySide import QtGui

translate = FreeCAD.Qt.translate


_DEFAULT_WIDTH = 18.0   # mm — matches typical 3/4" plywood / shelf thickness
_DEFAULT_DEPTH = 6.0    # mm — about 1/3 of an 18 mm host panel

_AXIS_NAMES = ("X", "Y", "Z")


def _get_selected_face():
    sel = FreeCADGui.Selection.getSelectionEx()
    if not sel:
        return None, None
    s = sel[0]
    if not s.SubObjects:
        return None, None
    sub = s.SubObjects[0]
    if sub.ShapeType != "Face":
        return None, None
    return s.Object, sub


def _planar_face_normal(face):
    """Outward normal of a planar face. Returns FreeCAD.Vector or None."""
    surf = face.Surface
    axis = getattr(surf, "Axis", None)
    if axis is None:
        return None
    # Surface.Axis points along the surface's intrinsic normal; the face may
    # be flipped (Orientation == "Reversed") in which case the outward normal
    # is the opposite direction.
    if face.Orientation == "Reversed":
        return FreeCAD.Vector(-axis.x, -axis.y, -axis.z)
    return FreeCAD.Vector(axis.x, axis.y, axis.z)


def _dominant_axis(vec):
    """Return 0/1/2 for the axis (X/Y/Z) with the largest absolute component."""
    abs_components = (abs(vec.x), abs(vec.y), abs(vec.z))
    return abs_components.index(max(abs_components))


def _show_info(text):
    QtGui.QMessageBox.information(None, translate("jointDado", "jointDado"), text)


def _show_dialog(host, face, normal, normal_axis, in_plane_axes):
    dialog = QtGui.QDialog()
    dialog.setWindowTitle(translate("jointDado", "Cut Dado"))
    layout = QtGui.QFormLayout(dialog)

    direction_box = QtGui.QComboBox()
    for axis in in_plane_axes:
        direction_box.addItem(
            translate("jointDado", "Along {axis}").format(axis=_AXIS_NAMES[axis]),
            axis,
        )

    width_edit = QtGui.QLineEdit(str(_DEFAULT_WIDTH))
    depth_edit = QtGui.QLineEdit(str(_DEFAULT_DEPTH))
    position_edit = QtGui.QLineEdit("center")

    layout.addRow(translate("jointDado", "Dado runs:"), direction_box)
    layout.addRow(translate("jointDado", "Dado width (mm):"), width_edit)
    layout.addRow(translate("jointDado", "Dado depth (mm):"), depth_edit)
    layout.addRow(
        translate("jointDado", "Position from edge (mm) or 'center':"),
        position_edit,
    )

    buttons = QtGui.QDialogButtonBox(
        QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec_() != QtGui.QDialog.Accepted:
        return

    try:
        width = float(width_edit.text())
        depth = float(depth_edit.text())
    except ValueError:
        _show_info(translate("jointDado", "Width and depth must be numbers (mm)."))
        return

    if width <= 0 or depth <= 0:
        _show_info(translate("jointDado", "Width and depth must be positive."))
        return

    pos_str = position_edit.text().strip().lower()
    if pos_str in ("", "center", "centre"):
        offset = None
    else:
        try:
            offset = float(pos_str)
        except ValueError:
            _show_info(
                translate("jointDado", "Position must be a number or 'center'.")
            )
            return

    run_axis = direction_box.currentData()
    perp_axis = next(a for a in in_plane_axes if a != run_axis)

    _cut_dado(host, face, normal, normal_axis, run_axis, perp_axis, width, depth, offset)


def _cut_dado(host, face, normal, normal_axis, run_axis, perp_axis,
              width, depth, offset):
    bbox = host.Shape.BoundBox
    bbox_min = [bbox.XMin, bbox.YMin, bbox.ZMin]
    bbox_max = [bbox.XMax, bbox.YMax, bbox.ZMax]
    bbox_size = [bbox.XLength, bbox.YLength, bbox.ZLength]

    cut_size = [0.0, 0.0, 0.0]
    cut_pos = [0.0, 0.0, 0.0]

    # Cut depth runs along the face normal, INTO the host.
    cut_size[normal_axis] = depth + 0.001  # tiny extension to avoid coincident-face artifacts
    if (normal[0], normal[1], normal[2])[normal_axis] > 0:
        cut_pos[normal_axis] = bbox_max[normal_axis] - depth
    else:
        cut_pos[normal_axis] = bbox_min[normal_axis]

    # Dado spans the full host along the run axis, with a small overhang at each end.
    cut_size[run_axis] = bbox_size[run_axis] + 1.0
    cut_pos[run_axis] = bbox_min[run_axis] - 0.5

    # Width along the perpendicular in-plane axis; offset from bbox_min on that axis
    # (or centered on the selected face if offset is None).
    cut_size[perp_axis] = width
    if offset is None:
        face_center = (face.CenterOfMass.x, face.CenterOfMass.y, face.CenterOfMass.z)
        cut_pos[perp_axis] = face_center[perp_axis] - width / 2.0
    else:
        cut_pos[perp_axis] = bbox_min[perp_axis] + offset - width / 2.0

    doc = host.Document
    doc.openTransaction("jointDado")
    try:
        cutter = doc.addObject("Part::Box", "DadoCutter")
        cutter.Label = "DadoCutter"
        cutter.Length = cut_size[0]
        cutter.Width = cut_size[1]
        cutter.Height = cut_size[2]
        cutter.Placement.Base = FreeCAD.Vector(*cut_pos)

        cut = doc.addObject("Part::Cut", host.Name + "_dado")
        cut.Base = host
        cut.Tool = cutter
        cut.Label = host.Label + " (dado)"

        if FreeCAD.GuiUp and hasattr(cutter, "ViewObject"):
            cutter.ViewObject.Visibility = False
        doc.recompute()
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        raise


def main():
    host, face = _get_selected_face()
    if host is None:
        _show_info(translate(
            "jointDado",
            "Select one planar face on the panel where the dado should be cut, "
            "then run jointDado again. The dado will be a rectangular groove "
            "cut into the host along that face.",
        ))
        return

    normal = _planar_face_normal(face)
    if normal is None:
        _show_info(translate(
            "jointDado",
            "Selected face is not planar. jointDado supports planar faces only "
            "(typical Part::Box panels).",
        ))
        return

    normal_axis = _dominant_axis(normal)
    in_plane_axes = [i for i in range(3) if i != normal_axis]
    _show_dialog(host, face, normal, normal_axis, in_plane_axes)


if FreeCAD.GuiUp:
    main()

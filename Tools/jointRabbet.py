import FreeCAD, FreeCADGui, Part
from PySide import QtGui

translate = FreeCAD.Qt.translate


_DEFAULT_A = 8.0   # mm — first cross-section size of the rabbet
_DEFAULT_B = 8.0   # mm — second cross-section size

_AXIS_LETTERS = ("x", "y", "z")
_DIM_PROPS = ("Length", "Width", "Height")


def _show_info(text):
    QtGui.QMessageBox.information(None, translate("jointRabbet", "jointRabbet"), text)


def _selected_edge():
    sel = FreeCADGui.Selection.getSelectionEx()
    if not sel:
        return None, None
    s = sel[0]
    if not s.SubObjects:
        return None, None
    sub = s.SubObjects[0]
    if sub.ShapeType != "Edge":
        return None, None
    return s.Object, sub


def _edge_run_axis(edge):
    """Return 0/1/2 for the axis (X/Y/Z) along which an axis-aligned edge runs."""
    v1, v2 = edge.Vertexes[0].Point, edge.Vertexes[1].Point
    delta = (abs(v2.x - v1.x), abs(v2.y - v1.y), abs(v2.z - v1.z))
    return delta.index(max(delta))


def _ensure_params_sheet(doc):
    obj = doc.getObject("Params")
    if obj is not None and obj.TypeId == "Spreadsheet::Sheet":
        return obj
    sheet = doc.addObject("Spreadsheet::Sheet", "Params")
    sheet.set("A1", "PARAMS")
    return sheet


def _last_filled_row(sheet, max_scan=1000):
    last = 0
    for row in range(1, max_scan + 1):
        try:
            content = sheet.getContents(f"A{row}")
        except Exception:
            break
        if content:
            last = row
    return last


def _add_rabbet_aliases(sheet, cutter_name, a_mm, b_mm):
    rows = [
        (f"rabbet.{cutter_name}.a", f"{cutter_name}_a", f"{a_mm} mm"),
        (f"rabbet.{cutter_name}.b", f"{cutter_name}_b", f"{b_mm} mm"),
    ]
    next_row = max(1, _last_filled_row(sheet) + 2)
    aliases = {}
    for off, (label, alias, value) in enumerate(rows):
        row = next_row + off
        sheet.set(f"A{row}", label)
        sheet.set(f"B{row}", value)
        sheet.setAlias(f"B{row}", alias)
        aliases[alias.rsplit("_", 1)[-1]] = alias
    return aliases


def _show_dialog(host, edge, run_axis):
    cross_axes = [i for i in range(3) if i != run_axis]

    dialog = QtGui.QDialog()
    dialog.setWindowTitle(translate("jointRabbet", "Cut Rabbet"))
    layout = QtGui.QFormLayout(dialog)

    a_edit = QtGui.QLineEdit(str(_DEFAULT_A))
    b_edit = QtGui.QLineEdit(str(_DEFAULT_B))

    layout.addRow(
        translate("jointRabbet", "Cut size along {axis} (mm):").format(
            axis=_AXIS_LETTERS[cross_axes[0]].upper()
        ),
        a_edit,
    )
    layout.addRow(
        translate("jointRabbet", "Cut size along {axis} (mm):").format(
            axis=_AXIS_LETTERS[cross_axes[1]].upper()
        ),
        b_edit,
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
        a = float(a_edit.text())
        b = float(b_edit.text())
    except ValueError:
        _show_info(translate("jointRabbet", "Both sizes must be numbers in mm."))
        return
    if a <= 0 or b <= 0:
        _show_info(translate("jointRabbet", "Both sizes must be positive."))
        return

    _cut_rabbet(host, edge, run_axis, cross_axes, a, b)


def _cut_rabbet(host, edge, run_axis, cross_axes, a_size, b_size):
    bbox = host.Shape.BoundBox
    bbox_min = [bbox.XMin, bbox.YMin, bbox.ZMin]
    bbox_max = [bbox.XMax, bbox.YMax, bbox.ZMax]
    bbox_size = [bbox.XLength, bbox.YLength, bbox.ZLength]
    bbox_mid = [(bbox_min[i] + bbox_max[i]) / 2.0 for i in range(3)]

    edge_center = edge.CenterOfMass
    edge_pos = (edge_center.x, edge_center.y, edge_center.z)

    cross_a, cross_b = cross_axes
    a_at_max = edge_pos[cross_a] > bbox_mid[cross_a]
    b_at_max = edge_pos[cross_b] > bbox_mid[cross_b]

    cut_size = [0.0, 0.0, 0.0]
    cut_pos = [0.0, 0.0, 0.0]

    cut_size[run_axis] = bbox_size[run_axis] + 1.0
    cut_pos[run_axis] = bbox_min[run_axis] - 0.5

    cut_size[cross_a] = a_size
    cut_pos[cross_a] = (bbox_max[cross_a] - a_size) if a_at_max else bbox_min[cross_a]

    cut_size[cross_b] = b_size
    cut_pos[cross_b] = (bbox_max[cross_b] - b_size) if b_at_max else bbox_min[cross_b]

    doc = host.Document
    doc.openTransaction("jointRabbet")
    try:
        cutter = doc.addObject("Part::Box", "RabbetCutter")
        cutter.Label = "RabbetCutter"
        cutter.Length = cut_size[0]
        cutter.Width = cut_size[1]
        cutter.Height = cut_size[2]
        cutter.Placement.Base = FreeCAD.Vector(*cut_pos)

        sheet = _ensure_params_sheet(doc)
        aliases = _add_rabbet_aliases(sheet, cutter.Name, a_size, b_size)

        # Cross-section dimensions are always parametric.
        cutter.setExpression(_DIM_PROPS[cross_a], f"Params.{aliases['a']}")
        cutter.setExpression(_DIM_PROPS[cross_b], f"Params.{aliases['b']}")

        # When the host is a Part::Box, also wire positions and run-axis dim
        # to host expressions so resizing the host updates the rabbet.
        if host.TypeId == "Part::Box":
            if a_at_max:
                expr_a = (
                    f"{host.Name}.Placement.Base.{_AXIS_LETTERS[cross_a]} "
                    f"+ {host.Name}.{_DIM_PROPS[cross_a]} "
                    f"- Params.{aliases['a']}"
                )
            else:
                expr_a = f"{host.Name}.Placement.Base.{_AXIS_LETTERS[cross_a]}"
            cutter.setExpression(f"Placement.Base.{_AXIS_LETTERS[cross_a]}", expr_a)

            if b_at_max:
                expr_b = (
                    f"{host.Name}.Placement.Base.{_AXIS_LETTERS[cross_b]} "
                    f"+ {host.Name}.{_DIM_PROPS[cross_b]} "
                    f"- Params.{aliases['b']}"
                )
            else:
                expr_b = f"{host.Name}.Placement.Base.{_AXIS_LETTERS[cross_b]}"
            cutter.setExpression(f"Placement.Base.{_AXIS_LETTERS[cross_b]}", expr_b)

            cutter.setExpression(
                _DIM_PROPS[run_axis],
                f"{host.Name}.{_DIM_PROPS[run_axis]} + 1 mm",
            )
            cutter.setExpression(
                f"Placement.Base.{_AXIS_LETTERS[run_axis]}",
                f"{host.Name}.Placement.Base.{_AXIS_LETTERS[run_axis]} - 0.5 mm",
            )

        cut = doc.addObject("Part::Cut", host.Name + "_rabbet")
        cut.Base = host
        cut.Tool = cutter
        cut.Label = host.Label + " (rabbet)"

        if FreeCAD.GuiUp and hasattr(cutter, "ViewObject"):
            cutter.ViewObject.Visibility = False
        doc.recompute()
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        raise


def main():
    host, edge = _selected_edge()
    if host is None:
        _show_info(translate(
            "jointRabbet",
            "Select one edge of the host panel where the rabbet should run, "
            "then run jointRabbet again. The rabbet is an L-shaped recess along "
            "that edge, removing material from the two adjacent faces.",
        ))
        return

    try:
        run_axis = _edge_run_axis(edge)
    except Exception:
        _show_info(translate(
            "jointRabbet",
            "Could not determine the edge direction. Pick a straight, "
            "axis-aligned edge on a Part::Box host.",
        ))
        return

    _show_dialog(host, edge, run_axis)


if FreeCAD.GuiUp:
    main()

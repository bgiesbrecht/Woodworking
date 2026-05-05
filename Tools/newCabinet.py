import FreeCAD, FreeCADGui
from PySide import QtGui

translate = FreeCAD.Qt.translate


_DEFAULTS = {
    "name":      "Cabinet",
    "width":     600.0,
    "height":    800.0,
    "depth":     350.0,
    "thickness": 18.0,
}

_UNITS = "mm"


def _create_params_sheet(doc, project_name, width, height, depth, thickness, units):
    sheet = doc.addObject("Spreadsheet::Sheet", "Params")

    rows = [
        ("PROJECT",                "",                     None),
        ("project.name",           project_name,           "project_name"),
        ("project.units",          units,                  "project_units"),
        ("",                       "",                     None),
        ("DIMENSIONS",             "",                     None),
        ("dim.overall_width",      f"{width} {units}",     "overall_width"),
        ("dim.overall_height",     f"{height} {units}",    "overall_height"),
        ("dim.overall_depth",      f"{depth} {units}",     "overall_depth"),
        ("dim.material_thickness", f"{thickness} {units}", "material_thickness"),
    ]

    for row, (label, value, alias) in enumerate(rows, start=1):
        if label:
            sheet.set(f"A{row}", str(label))
        if value != "":
            sheet.set(f"B{row}", str(value))
        if alias:
            sheet.setAlias(f"B{row}", alias)

    return sheet


def _create_panel(doc, name, length_expr, width_expr, height_expr,
                  x_expr=None, y_expr=None, z_expr=None):
    box = doc.addObject("Part::Box", name)
    box.Label = name
    box.setExpression("Length", length_expr)
    box.setExpression("Width",  width_expr)
    box.setExpression("Height", height_expr)
    if x_expr is not None:
        box.setExpression("Placement.Base.x", x_expr)
    if y_expr is not None:
        box.setExpression("Placement.Base.y", y_expr)
    if z_expr is not None:
        box.setExpression("Placement.Base.z", z_expr)
    return box


def createCabinet(name, width, height, depth, thickness, units=_UNITS):
    """Create a new document with a parametric 4-panel cabinet carcass.

    The carcass uses a face-frame convention: top and bottom span the full
    width and depth; left and right sides nest between them with height
    equal to ``overall_height - 2 * material_thickness``.

    Coordinate convention: X = width, Y = depth, Z = height.
    All geometry is driven by aliases on the ``Params`` spreadsheet.
    """
    doc = FreeCAD.newDocument(name)
    _create_params_sheet(doc, name, width, height, depth, thickness, units)
    doc.recompute()

    W = "Params.overall_width"
    H = "Params.overall_height"
    D = "Params.overall_depth"
    T = "Params.material_thickness"
    side_height = f"{H} - 2 * {T}"

    _create_panel(doc, "Top",       W, D, T, z_expr=f"{H} - {T}")
    _create_panel(doc, "Bottom",    W, D, T)
    _create_panel(doc, "SideLeft",  T, D, side_height, z_expr=T)
    _create_panel(doc, "SideRight", T, D, side_height,
                  x_expr=f"{W} - {T}", z_expr=T)

    doc.recompute()

    if FreeCAD.GuiUp:
        try:
            FreeCADGui.SendMsgToActiveView("ViewFit")
        except Exception:
            pass
    return doc


def _show_dialog():
    dialog = QtGui.QDialog()
    dialog.setWindowTitle(translate("newCabinet", "New Cabinet"))

    layout = QtGui.QFormLayout(dialog)

    name_edit      = QtGui.QLineEdit(_DEFAULTS["name"])
    width_edit     = QtGui.QLineEdit(str(_DEFAULTS["width"]))
    height_edit    = QtGui.QLineEdit(str(_DEFAULTS["height"]))
    depth_edit     = QtGui.QLineEdit(str(_DEFAULTS["depth"]))
    thickness_edit = QtGui.QLineEdit(str(_DEFAULTS["thickness"]))

    layout.addRow(translate("newCabinet", "Project name:"),            name_edit)
    layout.addRow(translate("newCabinet", "Width (mm):"),              width_edit)
    layout.addRow(translate("newCabinet", "Height (mm):"),             height_edit)
    layout.addRow(translate("newCabinet", "Depth (mm):"),              depth_edit)
    layout.addRow(translate("newCabinet", "Material thickness (mm):"), thickness_edit)

    buttons = QtGui.QDialogButtonBox(
        QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec_() != QtGui.QDialog.Accepted:
        return

    try:
        name      = name_edit.text().strip() or _DEFAULTS["name"]
        width     = float(width_edit.text())
        height    = float(height_edit.text())
        depth     = float(depth_edit.text())
        thickness = float(thickness_edit.text())
    except ValueError:
        QtGui.QMessageBox.critical(
            None,
            translate("newCabinet", "Invalid input"),
            translate("newCabinet", "All dimensions must be numbers in millimeters."),
        )
        return

    if min(width, height, depth, thickness) <= 0:
        QtGui.QMessageBox.critical(
            None,
            translate("newCabinet", "Invalid input"),
            translate("newCabinet", "Dimensions must be positive."),
        )
        return

    createCabinet(name, width, height, depth, thickness)


if FreeCAD.GuiUp:
    _show_dialog()

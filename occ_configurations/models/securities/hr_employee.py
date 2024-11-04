# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError, AccessError


class HREmployee(models.Model):
    _inherit = "hr.employee"
    _snakecased_name = "hr_employee"
    _model_path_name = "occ_configurations.model_hr_employee"

    work_location_type = fields.Selection(
        selection=[("onsite", "On-Site"), ("wfh", "Work From Home")],
        string="Work Location Type",
        default="onsite",
        tracking=True,
        required=True,
    )

    @api.model
    def _update_user_work_location_groups(self, user, location_type):
        if not user:
            return

        wfh_group = self.env.ref("occ_configurations.group_wfh_employee")
        onsite_group = self.env.ref("occ_configurations.group_onsite_employee")

        if location_type == "wfh":
            user.sudo().write({"groups_id": [(3, onsite_group.id), (4, wfh_group.id)]})
        else:
            user.sudo().write({"groups_id": [(3, wfh_group.id), (4, onsite_group.id)]})

    @api.constrains("work_location_type")
    def _check_work_location_manager(self):
        if self.env.user.has_group("occ_configurations.group_work_location_manager"):
            return True
        raise AccessError(
            _("Only Work Location Managers can modify employee work location types.")
        )

    def write(self, vals):
        if "work_location_type" in vals:
            # Check for work location manager rights
            if not self.env.user.has_group(
                "occ_configurations.group_work_location_manager"
            ):
                raise AccessError(
                    _(
                        "Only Work Location Managers can modify employee work location types."
                    )
                )

            # Track the change for audit purposes
            self.env["hr.work.location.change.log"].create(
                {
                    "employee_id": self.id,
                    "old_location": self.work_location_type,
                    "new_location": vals["work_location_type"],
                    "changed_by": self.env.user.id,
                }
            )

        res = super(HREmployee, self).write(vals)

        if "work_location_type" in vals and self.user_id:
            self._update_user_work_location_groups(
                self.user_id, vals["work_location_type"]
            )

        return res

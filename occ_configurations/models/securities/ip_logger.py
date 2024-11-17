# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class IPLogger(models.Model):
    _name = "ip.logger"
    _snakecased_name = "ip_logger"
    _model_path_name = "occ_configurations.model_ip_logger"
    _description = "IP Logger"
    
    name = fields.Char(
        string="Name",
        default=False,
        required=True,
    )

    name_compute = fields.Char(
        store=False,
        compute="_compute_name",
    )
    
    user_agent = fields.Char(
        string="Useragent",
        default=False,
    )
    
    device_name = fields.Char(
        string="Device",
        default=False,
    )

    browser_name = fields.Char(
        string="Browser",
        default=False,
    )
    
    os_name = fields.Char(
        string="OS",
        default=False,
    )

    ip_address = fields.Char(
        string="IP Address",
        default=False,
        required=True,
    )
    
    lattitude = fields.Float(
        string="Lattitude",
        default=False,
    )

    longitude = fields.Float(
        string="Longitude",
        default=False,
    )
    
    country = fields.Char(
        string="Country",
        default=False,
    )
    
    region = fields.Char(
        string="Region",
        default=False,
    )
    
    city = fields.Char(
        string="City",
        default=False,
    )   
    
    zip_code = fields.Char(
        string="Zip Code",
        default=False,
    )
    
    currency = fields.Char(
        string="Currency",
        default=False,
    )
    
    timezone = fields.Char(
        string="Timezone",
        default=False,
    )

    location_name = fields.Char(
        string="Location",
        default=False,
    )
    
    login_date = fields.Datetime(
        string="Login Date",
        default=fields.Datetime.now,
    )
    
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        default=lambda self: self.env.user,
    )
    
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        default=lambda self: self.env.user.employee_id
    )
    
    @api.depends("browser_name", "ip_address", "os_name", "device_name")
    def _compute_name(self):
        for rec in self:
            name = rec.name
            
            name_fields = [
                rec.ip_address,
                rec.browser_name,
                rec.os_name,
                rec.device_name,
            ]
            
            name = " | ".join([f for f in name_fields if f])
            
            rec.name = name
            rec.name_compute = name
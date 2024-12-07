# -*- coding: utf-8 -*-
# Native Python modules
import ast, calendar, json, re
from datetime import datetime, date
from time import sleep
from typing import Any, Optional
from collections import defaultdict

# Local python modules
from .logger import temp_log

# Custom python modules
from psycopg2 import sql, DatabaseError

# from benedict import benedict
# from icecream import ic
import pytz

# Odoo modules
from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError
from odoo.osv.expression import AND, OR
import odoo.addons.decimal_precision as dp
from odoo.tools import float_round, frozendict, mute_logger, date_utils
from odoo.tools.misc import clean_context, format_date
from odoo.tools.safe_eval import safe_eval


class CMDUtilities(models.AbstractModel):
    _name = "cmd.utilities"
    _snakecased_name = "cmd_utilities"

    def temp_log(
        self, output: Any, variable: str = "Not Provided", prefix: str = "occ"
    ):
        log = temp_log(output, variable, prefix)
        print(log)

    def get_ctx(self, ctx=None, process_ctx: str = "default"):
        if not ctx:
            ctx = self.env.context

        return self.process_context(ctx, process_ctx)

    def get_xml_record(self, xml_id):
        try:
            return self.env.ref(xml_id)
        except ValueError:
            return False
        except AttributeError:
            return False

    def process_context(self, context_str, process_type="default"):
        eval_dict = {
            "default": lambda ctx: dict(safe_eval(ctx)),
            "clean_context": lambda ctx: clean_context(safe_eval(ctx)),
            "safe_eval": lambda ctx: safe_eval(ctx),
        }
        return eval_dict.get(process_type, eval_dict["default"])(context_str)

    def get_xml_ids(
        self,
        view_id: Optional[str] = False,
        action_id: Optional[str] = False,
        server_id: Optional[str] = False,
        report_id: Optional[str] = False,
        email_id: Optional[str] = False,
        menu_id: Optional[str] = False,
        category_id: Optional[str] = False,
        group_id: Optional[str] = False,
    ):
        xml_dict = {
            "view_id": self.env.ref(view_id) if self.get_xml_record(view_id) else False,
            "action_id": (
                self.env.ref(action_id) if self.get_xml_record(action_id) else False
            ),
            "server_id": (
                self.env.ref(server_id) if self.get_xml_record(server_id) else False
            ),
            "report_id": (
                self.env.ref(report_id) if self.get_xml_record(report_id) else False
            ),
            "email_id": (
                self.env.ref(email_id) if self.get_xml_record(email_id) else False
            ),
            "menu_id": self.env.ref(menu_id) if self.get_xml_record(menu_id) else False,
            "category_id": (
                self.env.ref(category_id) if self.get_xml_record(category_id) else False
            ),
            "group_id": (
                self.env.ref(group_id) if self.get_xml_record(group_id) else False
            ),
        }

        return xml_dict

    def get_xml_values(
        self,
        process_context: str = "default",
        view_id: Optional[str] = False,
        action_id: Optional[str] = False,
        server_id: Optional[str] = False,
        report_id: Optional[str] = False,
        email_id: Optional[str] = False,
    ):

        process_context_dict = {
            "default": "default",
            "clean": "clean_context",
            "safe": "safe_eval",
        }

        process_context = process_context_dict.get(process_context, "default")

        view_xml = self.env.ref(view_id).id if self.get_xml_record(view_id) else False
        action_xml = (
            self.env.ref(action_id).read()[0]
            if self.get_xml_record(action_id)
            else False
        )
        server_xml = (
            self.env.ref(server_id).read()[0]
            if self.get_xml_record(server_id)
            else False
        )
        report_xml = (
            self.env.ref(report_id).read()[0]
            if self.get_xml_record(report_id)
            else False
        )
        email_xml = (
            self.env.ref(email_id).read()[0] if self.get_xml_record(email_id) else False
        )

        if action_xml and action_xml.get("context") and process_context:
            action_xml["context"] = self.process_context(
                action_xml["context"], process_context
            )

        if report_xml and report_xml.get("datas"):
            report_xml["datas"] = self.process_context(
                report_xml["datas"], process_context
            )

        return (view_xml, action_xml, server_xml, report_xml, email_xml)

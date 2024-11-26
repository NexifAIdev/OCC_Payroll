# -*- coding: utf-8 -*-

import ast, calendar, json, re
import inspect, os, re, time
from pathlib import Path
from datetime import datetime
from typing import Optional, Union, Any, Dict, List, Tuple
from functools import lru_cache
import pytz

from time import sleep
from collections import defaultdict


def temp_log(output: Any, variable: str = "Not Provided", prefix: str = "istudio"):
    frame = inspect.currentframe().f_back
    file_path = frame.f_code.co_filename
    class_name = (
        frame.f_locals.get("self", None).__class__.__name__
        if "self" in frame.f_locals
        else ""
    )
    method_name = frame.f_code.co_name
    output_variable_type = type(output).__name__
    pht_timezone = pytz.timezone("Asia/Manila")
    current_time = datetime.now(pht_timezone).strftime("%Y-%m-%d %H:%M:%S")

    temp_log = f"""
========================================================================
{current_time}
{file_path}
class: {class_name if class_name else 'N/A'}
method: {method_name if method_name else 'N/A'}
variable_name: {variable}
output: {output}
type: {output_variable_type}
========================================================================
    """

    tmp_path = f"{Path.home()}/.tmp/odoo_tmp_logs"
    Path(tmp_path).mkdir(parents=True, exist_ok=True)

    with open(f"{tmp_path}/{prefix}_temp_log.txt", "a") as f:
        f.write(temp_log + "\n")

    return temp_log

# Pentaho - Odoo Report Integration

## Outstanding
- This module is tested and functional with SQL Reports in version 17.
- Report Designer compatibility confirmed for version 8.3.

## Overview
This module integrates Pentaho’s reporting engine with Odoo, based on work inspired by other Odoo reporting addons.

Report Designer and Java Component
For report designer setup, refer to: [Pentaho Report Designer v8.3](https://github.com/ambientelivre/legacy-pentaho-ce/releases/download/prd-ce-8.3.0.0-371/prd-ce-8.3.0.0-371.zip). 

For java component building, refer to: [Pentaho Odoo](https://github.com/WilldooIT/Pentaho-Odoo). 

## Report Types
Reports can use either:
- SQL Data Sources: Offers flexibility in data selections, supports advanced SQL features, and does not respect Odoo record rules.
- Odoo Object Data Sources: Uses data directly from Odoo models.

## Report Parameters
-----------------
Prompted and hidden parameters are supported, as are mandatory values.

A number of reserved parameters are automatically passed, but the report needs to define these parameters in order
to receive and use them. Reserved parameters currently passed are:

* *ids*: the context ids when the report action is called. This is almost always needed for object based reports
  to be meaningful.
* *user_id*: the id of the user running the report.
* *user_name*: the display name of the user running the report.
* *context_lang*: the language in effect when the report action is executed.
* *context_tz*: the timezone in effect when the report action is executed.

This list of reserved parameters is available for use is all data sources, even those which return possible
parameter selections, therefore allowing meaningful selections for other parameters.

Most Pentaho report parameter types and features have been mapped, where practicable, to something which makes
sense to an Odoo environment. This means that a number of Java data types don't necessarily differentiate.
For example, (Integer / Long / Short / BigInteger / et al) will all be treated as integers.

Default values can be passed for the parameters, and may default value formulae work.

Hidden parameters must obviously receive and work with a default value of some sort. This default can be the
Pentaho default, or can be sent to the report in the context in the format:

    **{'pentaho_defaults': { .... }}**

where the passed dictionary contains the parameter names as keys. See below for guidance on where to set this up.

Pentaho Display Types have been consolidated.  Drop Down, Single Value List, etc, all display as Odoo selection
pull downs. Some Pentaho multi value selection types, such as Check Box, etc, are implemented as single value
selection pull downs. Date Picker uses the standard Odoo date/time widget.  Pentaho multi value lists are
implemented as many2manytag widgets, and support integer, string, and numeric data types.

Other Pentaho parameter features should be considered unsupported, such as Post-Processing Formula, Display Value
Formula, Visible Items, Validate Values, et al.


## Setup
-----
Some parameters may be required in **Settings / Parameters / System Parameters**.

The address of the Pentaho server which is used to render the report is defined with the parameter:

    **pentaho.server.url**

For SQL query based data sources, the Pentaho server will use the following parameters:

* pentaho.postgres.host
* pentaho.postgres.port
* pentaho.postgres.login
* pentaho.postgres.password


## Report Actions
--------------
Reports are defined to Odoo under **Settings / Technical / Actions / Reports**.  This is the place
where standard Odoo report actions are defined. Selecting the appropriate checkbox can convert existing report
actions to Pentaho Report Actions.

Reports can be handled by Odoo in two ways. They can be linked to a menu, or they can be linked to a model.

* Model linked reports will appear in the right hand toolbar as per standard reports, or they can be specifically
  called with an action, such as a button. A record or number of records needs to be selected before the action
  will be invoked, and the ids of the selected records will be passed to the report as a list parameter called
  "ids". A report invoked this way will not prompt for any additional parameters. A front end custom wizard can be
  created if desired to invoke the action, but that wizard and the report would be very closely tied and need to
  be developed in conjunction with one other.

* Menu linked reports will appear somewhere in a menu. They will pop up a window prompting for a report output
  type, and any additional (visible) parameters that are defined. Object ids passed to these reports are not
  meaningful, as no object or ids are guaranteed to be in effect when the action is called, so selection of data
  needs to be based on other parameters. Other reserved parameters, such as user id, may be meaningful in the
  context of prompting for parameters or ultimate data selection.

Report actions can override existing Odoo actions (such as invoice prints) or can be new actions.

The service name is only important if it is overriding an existing service, or if the report is to be invoked from
coded actions like buttons or wizards. For menu linked actions or generic object linked actions, the service name
is incidental.

Output types specified here are defaults, and can be overridden by either a custom wizard or by menu linked
reports. They will not be changeable for model linked reports which don't have specific coding.

The prpt (Pentaho report definition) file selected is stored in the database. Changing the report using the
designer will require the report to be re-loaded.

A prpt file and action can easily be defined as part of a module and distributed this way. Be aware, though, if
the module is upgraded from within odoo it could potentially reload the distributed report and may lose
changes that were uploaded manually after module installation.

Security groups entered against the action will be respected in regard to action visibility - they play no role in
the report execution.

If a context value is required to set a default value, it needs to be set against the created action. It comes up
under Settings/Customization/Low Level Actions/Actions/Window Actions. It will already have a Context Value with
the service_name defined, which should be left intact.


## Limitations
At the moment, there is one known limitation. Object reports need to log in as another concurrent session with
the same user who is running the report. If the password encryption feature of Odoo has been enabled (it is
by default) then the object based report cannot be run.  A fix is in the pipeline.



cam_hr_overtime
====================
This module requires a patch so that the RML Timesheet report can be printed correctly.

The patch "rml_report.patch" has to be applied to the file 
"server/openerp/report/preprocess.py".

This patch allows the dynamically processing of "<td>"-Tags within RML reports.

e.g. 
cd server/openerp/report
patch -b -p0 < ../../custom-addons/cam_hr_overtime/rml_report.patch
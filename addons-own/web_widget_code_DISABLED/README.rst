Web Widget: Code
================

This addon defines widget 'code' that could be used for text fields.

This is dependency addon, and intended to be used by other addons,
that need to be able to display or edit code with code highlighting.

Also this addons adds widget 'code' to ``Server action`` view


How to use
==========

For example, there is field

.. code:: python

    my_code = fields.Text('My code')

so this field could be defined in a view in following way

.. code:: xml

    <field name="my_code" widget="code" ace-mode="python"/>

Also it is possible to specify theme to be used for code editor:

.. code:: python

    <field name="my_code" widget="code" ace-mode="xml" ace-theme="twilight"

Under the hood
==============

Internaly this widget uses `Ace editor <https://ace.c9.io/#nav=about>`__

Enabled modes and themes
========================

By default following modes enabled:

- python
- xml
- html
- json
- javascript
- sh

By default following themes enabled:

- tomorrow (default)
- github

If you want to enable more modes / themes, then you should add them like:

.. code:: xml

    <template id="assets_backend"
              name="web_editor assets for backend"
              inherit_id="web.assets_backend">
        <xpath expr="." position="inside">
            <!-- add mode (language) 'Java' -->
            <script src="/web_widget_code/static/lib/ace-builds/src-min-noconflict/mode-java.js"

            <!-- add theme 'monokai' -->
            <script src="/web_widget_code/static/lib/ace-builds/src-min-noconflict/theme-monokai.js"
        </xpath>
    </template>

References
==========

- `Available ace themes <https://github.com/ajaxorg/ace/tree/master/lib/ace/theme>`__


# TODO: Test if any custom field value can be written to a custom field
Test if we can assign values to custom fields that are not in the values definiton of the custom field

# TODO: Handle Status of Contacts (PersonEmailGruppe) and Subscription Settings of Campaigns (zGruppeDetail)
Should we export contacts in all status or only some of them - what to do if the subscription setting of the 
campaign is not matching the GetResponse Subscription Setting?

# TODO: Store Export and Import errors in the binding records
Add extra fields for errors - that should be cleard on .bind() again
Maybe add a state field to the binding models to easily see any problems

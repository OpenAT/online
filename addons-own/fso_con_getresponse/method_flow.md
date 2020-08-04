# Order of the import


Basically we first get an instance of the importer class e.g. ZgruppedetailDirectBatchImporter() and start the method run()
The importer class ZgruppedetailDirectBatchImporter() sets the '_model_name = ['getresponse.frst.zgruppedetail']' and is based by inheritance on three other classes:
'DirectBatchImporter' which is based on 'BatchImporter' which is based on 'Importer':

ZgruppedetailDirectBatchImporter(DirectBatchImporter(BatchImporter(Importer)))

The last three classes belong to the 'generic' GetResponse import synchronizer so they have no specific code for 'getresponse.frst.zgruppedetail'.
BUT the specific adapter, mapper, and binder will be used since we set 
'_model_name = ['getresponse.frst.zgruppedetail']'! in the first class ZgruppedetailDirectBatchImporter()

These three basic importer classes implement 'run()' and '_import_record()'
_import_record() will finally call the function 'import_record()'

So the first start of run() 'ZgruppedetailDirectBatchImporter(DirectBatchImporter(BatchImporter(Importer))) > run()'
will start the method run() in BatchImporter() which will search for all campaigns in GetResponse and call DirectBatchImporter() > _import_record() for every found campaing

_import_record() will then start the function 'import_record()'
The import_record() function will then get an instance of the class GetResponseImporter() and will call the GetResponseImporter() > run()
This is again all generic code for GetResponse imports and not specific to the model 'getresponse.frst.zgruppedetail'

So finally import_record() started the run() from the class GetResponseImporter(). 
This class is used as the base for all Getresponse imports so it has no specific code for the model 'getresponse.frst.zgruppedetail'.
BUT the specific adapter, mapper, and binder will be used since we set '_model_name = ['getresponse.frst.zgruppedetail']' in the first place!


### Some thoughts about this

As i understand it we split the "search for records" and the "import each records" parts. 
First we have the 'search for GetResponse records' part which is solved in the 
ZgruppedetailDirectBatchImporter(DirectBatchImporter(BatchImporter(Importer)))
and
ZgruppedetailDelayedBatchImporter(DelayedBatchImporter(BatchImporter(Importer)))
classes. 

The only difference between these two classes is that we start import_record() with or without .delay() - so with or
without a connector job.

This seems quite an overhead for such a "small" change in the processing... But may give a neat expandability

Then we "import each record" by the function import_record() which will use the class
GetResponseImporter(Importer)

## How to customize what campaigns will be imported

### The filter attribute
If we want to import only campaigns from GetResponse that match a specific criteria we could use the parameter filter 
which will be passed all the way to run() method of the generic BatchImporter() class. Here the filter is passed on 
the the adapters search() method (record_ids = self.backend_adapter.search(filters)) 

Depending on the adapter implementation for the specific model this filter may narrow the results of the returned
records from GetResponse

### Override the run() method
We could also swap out (override) the generic BatchImporter() > run() method with a more appropriate version in the 
'getresponse.frst.zgruppedetail' model specific class ZgruppedetailDirectBatchImporter() and/or in the class
ZgruppedetailDelayedBatchImporter()

I find it HIGHLY CONFUSING that there are three classes implementing a run() method for the record search which will
then in the end call the run() method of the GetResponseImporter class ... It would be much easier to understand if
the run() method of the classes ZgruppedetailDirectBatchImporter(DirectBatchImporter(BatchImporter(Importer))) 
would be called import_records or alike to avoid confusion with the run() method of the GetResponseImporter() class




Getting Started
===============

Installation
------------

NofearDB can be installed by running:

.. code-block:: console

    pip install nofeardb

First Document
-----------------

Just like other NoSQL databases, NofearDB also follows a document-based approach. Data records are stored as JSON files (so-called documents) on the hard disk. However, since NofearDB is schema-consistent, unlike other NoSQL databases, it is first necessary to define which data should be stored in a document. For example, let's assume that we want to store employee data for a company in a database. An employee has a name, a number and a date on which they were hired. A corresponding document class could look like this:

.. code-block:: python

    from nofeardb.orm import Document, Field
    from nofeardb.datatypes import String, Integer, DateTime

    class Employee(Document):

        __documentname__ = "employee"

        name = Field(String, nullable=False)
        number = Field(Integer)
        hired = Field(DateTime)

As you can see documents are simply defined as Python classes which inherits from :class:`nofeardb.orm.Document`. All class attributes that are assigned the descriptor :class:`nofeardb.orm.Field` are later saved under the same name in the document. The Field descriptor expects at least a datatype of type :class:`nofeardb.datatypes`. This ensures, that data is serialized and deserialized in the correct way. The "nullable" attribute determines whether an attribute may be None.

.. note::

    The class attribute __documentname__ sets the global document name. All documents of this type are saved under this name. In the example above, however, __documentname__ could also be omitted, as in this case the name is automatically set to the name of the document class in lower case (here "employee").

You now have the first document which can be persistet to the hard drive.


Persisting documents
--------------------

A document itself is only the definition of a data structure. To actually store and load data in the database, it requires an instance of :class:`nofeardb.engine.StorageEngine`. StorageEngine is the core of NofearDB and acts as an interface between the data on disk and the application layer. The first step is to create an instance:

.. code-block:: python

    from nofeardb.engine import StorageEngine

    engine = StorageEngine("/path/to/db")

StorageEngine expects only one argument and that is the path under which the database is to be created. The next step is to register all document types we wan to use.

.. code-block:: python

    engine.register_models([Employee])

After that saving employees to the database is that simple:

.. code-block:: python

    import datetime

    employee = Employee()
    employee.name = "Max"
    employee.number = 1
    employee.hired = datetime.datetime.now()

    engine.create(employee)

Reading documents
--------------------

With our StorageEngine instance we can now query employees from the database:

.. code-block:: python

    employees = engine.read(Employee).all()

Returned is a list of Employee instances, each filled with the corresponding data.

.. note::

    Please be aware, that read instances of a document are not updated autoamtically when a change is made to the document from somewhere else.
    The only way to be sure to be up to date with your instaces is to read them before using them. Also be aware of the following:
    Currently every call to engine.read() creates fresh instances, which are not synchronized with already existing instances of the document.


Updating documents
--------------------

Lets say we want to update an already persisted document. As expected this is also done by utilizing the StorageEngine:

.. code-block:: python

    employee_to_update = engine.read(Employee).first()
    employee_to_update.name = "Paul"

    engine.update(employee_to_update)

The next time the employee is queried it will have the updated value for the name.


Deleting documents
--------------------

Now if you want to remove a document from the database it can be done like this:

.. code-block:: python

    employee_to_delete = engine.read(Employee).first()

    engine.delete(employee_to_delete)

This operation also updates the relationships on related documents. Therefore in order to success, all documents that are related to the document which should be deleted must be writable. I everything works, the data of the document is physically removed from the harddrive.

Thats it for now. These few lines of Code already allow very basic persisting and querying of data. But there are even more complex things you can do, which where described in the next chapters.
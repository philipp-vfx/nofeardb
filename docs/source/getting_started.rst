Getting Started
===============

Installation
------------

NofearDB can be simply installed by running:

.. code-block:: console

    pip install nofeardb

First Document
-----------------

In order to write data to the database and read it again later, it is necessary to define which data is to be saved and in what form. The first step is to define this. In NofearDB this can be done with “Documents”. A document describes the structure of a data record for a specific data construct. For example, let's assume that we want to store employee data for a company in a database. An employee has a name, a number and a date on which they were hired. A corresponding document could look like this:

.. code-block:: python

    from nofeardb.orm import Document, Field
    from nofeardb.datatypes import String, Integer, DateTime

    class Employee(Document):

        __documentname__ = "employee"

        name = Field(String, nullable=False)
        number = Field(Integer)
        hired = Field(DateTime)

As you can see a document is simply a Python class which inherits from :class:`nofeardb.orm.Document`. To define which data to store we can simply assign :class:`nofeardb.orm.Field` to class attributes.

.. note::

    the class attribute "__documentname__" defines the name of the document. All documents of this kind are stored under this name. In this case it is obsolote since the class name is evaluated to the name in lower case as default if __documentname__ is not provided.
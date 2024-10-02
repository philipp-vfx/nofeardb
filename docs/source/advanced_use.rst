Advanced
========

Working with Id's
------------------

NofearDB works with UUID's, to uniqueally identify enties. Each document is automatically assigned a unique ID when it is created. It is therefore not necessary to specify an ID attribute on the document. However, this can be useful if you want to access the ID of a document from outside. In this case, an ID parameter can be specified as a field and named as desired. To specify a field as a primary key, only the “primary_key” parameter needs to be set to True. Note that there can only be one field per document that is used as the primary key.

.. code-block:: python
    from nofeardb.orm import Document, ManyToOne, OneToMany, Field
    from nofeardb.datatypes import String, Integer, DateTime, Float, UUID

    class Employee(Document):

        my_id = Field(UUID, primary_key=True)
        name = Field(String, nullable=False)
        number = Field(Integer)
        hired = Field(DateTime)
        paychecks = OneToMany("Paycheck", back_populates="employee", cascade=["delete"])

.. note::

    Currently only the datatype UUID is supported as a primary key.


.. note::

    Only the uniqueness of the ID of a document within a document class is guaranteed. Collisions can potentially occur between different document classes


Advanced Queries
-----------------
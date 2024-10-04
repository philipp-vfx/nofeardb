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

NofearDB allows to filter query results by certain criteria. The query class provides the “where” method for this purpose. This method allows you to define expressions to be filtered by. The result is a new query object that only contains those documents to which the expression applies. A further query filter can theoretically be applied to this result. Linking several filters is similar to a logical AND. To build expressions, NofearDB provides special operator objects. Common operators such as equals or greater than are available (a complete list can be found here: :ref:`RST Expressions`). Most operators expect the name of the document attribute to which they are to be applied and a value to be evaluated against as parameters. If we follow the Employee example, a simple query to filter by name could look like this:

.. code-block:: python
    
    import nofeardb.expr as expr

    helgas = engine.read(Employee).where(expr.eq("name", "Helga")).all()

Exceptions are the _and and _or operators. These enable two expressions to be logically linked with each other and expect the relevant expressions accordingly. As an example this allows to filter for all employees with a specific name and a specific number:

.. code-block:: python
    
    import nofeardb.expr as expr

    helgas = engine.read(Employee).where(
            expr._and(
                expr.eq("name", "Helga"),
                expr.gt("number", 38)
            )
        ).all()

In this way, any number of complex expressions can be created during querying.
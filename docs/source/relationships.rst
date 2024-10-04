Relationships
=============

Basics
------

As with any database system, it is possible to define relations with NofearDB. The following relations are currently available: ManyToOne, OneToMany and ManyToMany. Assume that in the previous example, paychecks are to be assigned to each employee. This first requires an additional document type "Paycheck". The relationship can than be modelled as a bidreictional OneToMany relationship, with the reverse side being a ManyToOne relationship:

.. code-block:: python

    from nofeardb.orm import Document, ManyToOne, OneToMany, Field
    from nofeardb.datatypes import String, Integer, DateTime, Float


    class Employee(Document):

        name = Field(String, nullable=False)
        number = Field(Integer)
        hired = Field(DateTime)
        paychecks = OneToMany("Paycheck", back_populates="employee")

    class Paycheck(Document):

        payday = Field(DateTime, nullable=False)
        salary = Field(Float)
        employee = ManyToOne("Employee", back_populates="paychecks")

OneToMany, ManyToOne and ManyToMany are descriptors and always expect the name of the class that is to be set in relation to the document. As a bidirectional relationship is modulated, both sides need the argument "back_populates".  This defines which attributes of a document the other side of the relationship holds. If one side is updated, the other side of the relationship is also automatically updated. NofearDB dispenses with the concept of owning and inverse side.

.. note::

    The name of the class, which is set in relation, corresponds to the actual class name and not the internal identifier __documentname__.

When defined, relationships can be used just like other fields in the document:

.. code-block:: python

    import datetime
    from nofeardb.engine import StorageEngine

    engine = StorageEngine("/path/to/db")
    engine.register_models([Employee, Paycheck])

    employee = Employee()
    employee.name = "Max"

    paycheck1 = Paycheck()
    paycheck1.payday = datetime.datetime(2024,3,31)

    paycheck1 = Paycheck()
    paycheck1.payday = datetime.datetime(2024,4,30)

    employee.paychecks.append(paycheck1)

    paycheck2.employee = employee

    engine.create(employee)

As you can see, the relationship can be assigned from both sides, as it is bidirectional. If employee is persisted, all pending changes to related documents are also persisted by default.

.. note::

    Relationships are always queried lazy by design. That means that on query only the related ID's are queried and associated with empty document instances. When needed, this instances are filled with actual data on demand. This is to prevent from long time queries on heavy relational systems.

Cascading
----------

Cascading is an option to define how related entities should behave during common CRUD operations. In NofearDB you can currently only define a cascading behavior for the “Delete” operation. “Create” and ‘Update’ are cascaded by default to ensure consistent data in the database at all times. If the option cascade=[“delete”] is set in the relationship descriptor, all entities that are linked to the document via this relationship are also deleted. In the example shown above, paychecks only make sense if the corresponding employee still exists. The example can therefore be extended as follows:

.. code-block:: python

    class Employee(Document):

        name = Field(String, nullable=False)
        number = Field(Integer)
        hired = Field(DateTime)
        paychecks = OneToMany("Paycheck", back_populates="employee", cascade=["delete"])

Now when an employee is deleted, all paychecks related to this employee are deleted as well. On the other side, if a paycheck is deleted, the relationship on the employee is updated, but the employee stays persisted in the database. This applies as long as there is no cascade option for the employee specified on the paycheck as well.
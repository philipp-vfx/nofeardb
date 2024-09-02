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
